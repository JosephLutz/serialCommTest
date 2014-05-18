# packetGenerator
import threading
import random
import struct
import Queue
import time
import threadMonitor

from config import *


class PacketGeneratorException(BaseException):
    """Exceptions originating in the PacketGenerator"""

class PacketGenerator(threadMonitor.ThreadMonitor):
    # Generates the information for a packet
    #
    # This thread should be started before any TxThreads and
    # should be terminated only after all TxThreads have been joined.
    #
    # A packet is a byte string containing:
    #   1.)  packetID:     (0  to  65535)
    #   2.)  packetLen:    (MIN_PACKET_LENGTH  to  MAX_PACKET_LENGTH) a number less than 65535
    #   3.)  data:         (MIN_PACKET_DATA_LENGTH  to  MAX_PACKET_DATA_LENGTH) number of bytes
    #   4.)  data_hash:    (PACKET_GENERATOR_HASHLIB_ALGORITHM().digest_size) number of bytes
    # The data stored in the queue is a tuple containing:
    #   1.)  packet:       The above format of packet
    #   2.)  packetID:     Same value as in the packet
    #   3.)  packetLen:    Same value as in the packet
    #   4.)  data_hash:    Hex representation of the data_hash above

    #Lock used to access and updated static data in PacketGenerator objects
    allocated_lock = threading.Lock()

    # the allocated packetIDs
    allocated = set()

    #The total available packetIDs
    ALLOCATABLE_PACKET_ID = set(xrange(MAX_PACKET_ID))

    #Hashable value that will seed the random number generator
    _RANDOM_SEED = '{time}{len}'.format(time=time.time(), len=len(allocated))

    def __init__(self, max_queue_size=INITIAL_PACKET_NUMBER, num_rand_bytes=RAND_DATA_SIZE,
            printable_chars=False, seed=None, *args, **kwargs):
        """
        init method for PacketGenerator thread

        :type self: threadMonitor.ThreadMonitor
        :param max_queue_size: The size to use when creating packets. Try and keep at least this many packets.
        :param num_rand_bytes: number of random bytes to generate (Larger is better. Only one time when assembiling data)
        :param printable_chars: True if only printable characters desired
        :param seed: customize the random seed
        """
        super(PacketGenerator, self).__init__(*args, **kwargs)
        if max_queue_size > MAX_PACKET_ID:
            raise PacketGeneratorException
        if num_rand_bytes > (
                (len(struct.pack('!H', 0)) * 2) +
                MAX_PACKET_DATA_LENGTH +
                PACKET_GENERATOR_HASHLIB_ALGORITHM().digest_size):
            raise PacketGeneratorException
        # seed and init random numbers
        if seed is None:
            seed = PacketGenerator._RANDOM_SEED
        self._rand = random.SystemRandom(seed)
        # the next index of self._random_data to start gathering the data for the next packet
        self._start_index = 0
        # random data used for for sending
        if printable_chars:
            self._random_data = ''.join([chr(self._rand.randint(33, 126)) for i in xrange(num_rand_bytes)])
        else:
            self._random_data = ''.join([chr(self._rand.randint(1, 255)) for i in xrange(num_rand_bytes)])
        # the length of the packet to create
        self._packet_length = PACKET_SIZE
        self._packet_length_lock = threading.Lock()
        # Queue that holds each packet
        self.queue = Queue.Queue(maxsize=max_queue_size)
        if self.msgQueue:
            self.msgQueue.put((None, {'num_rand_bytes': num_rand_bytes}, GENERATE_DATA))

    def change_packet_length(self, packet_length=PACKET_SIZE):
        """
        If the packet length is set to None then a randome length is used
        Packet length must be greater than MIN_PACKET_DATA_LENGTH and
        less than MAX_PACKET_DATA_LENGTH. MAX_PACKET_DATA_LENGTH is calculated
        based off MAX_PACKET_LENGTH, PACKET_GENERATOR_HASHLIB_ALGORITHM's
        digest size, 2 bytes used for a length of the packet data and 2 bytes
        used for the packetID.

        :param packet_length: The length of the packets to be created
        """
        if ((packet_length > MAX_PACKET_LENGTH) or
                (packet_length < MIN_PACKET_LENGTH)):
            raise PacketGeneratorException
        self._packet_length_lock.acquire()
        self._packet_length = packet_length
        self._packet_length_lock.release()

    def locked_running(self):
        try:
            next_packet = None
            while self.running:
                self.runLock.release()
                if next_packet is None:
                    next_packet = self.makePacket()
                try:
                    self.queue.put(next_packet, True, PACKET_GENERATOR_TIMEOUT)
                except Queue.Full:
                    pass
                else:
                    next_packet = None
                self.runLock.acquire()
        except:
            if self._packet_length_lock.locked():
                self._packet_length_lock.release()
            if PacketGenerator.allocated_lock.locked():
                self._packet_length_lock.release()
            raise
        finally:
            # empty out the packet queue
            try:
                # loop untill Queue.Empty exception is thrown
                while True:
                    self.queue.get_nowait()
            except Queue.Empty:
                pass

    def makePacket(self):
        """
        Generates the packets of random data

        The random data will be used for the packet_data.
        Loop through the random data until packet_data is fully populated.
        """
        # determine packet_len
        self._packet_length_lock.acquire()
        if self._packet_length is None:
            local_packet_length = (
                (len(struct.pack('!H', 0)) * 2) +
                self._rand.randint(MIN_PACKET_DATA_LENGTH, MAX_PACKET_DATA_LENGTH) +
                PACKET_GENERATOR_HASHLIB_ALGORITHM().digest_size)
        else:
            local_packet_length = self._packet_length
        self._packet_length_lock.release()
        # assemble the packet_data from 
        packet_data = ''
        data_hash = PACKET_GENERATOR_HASHLIB_ALGORITHM()
        data_len = local_packet_length - (len(struct.pack('!H', 0)) * 2) - data_hash.digest_size
        while len(packet_data) < data_len:
            # end_index is the smaller of, the length of self._random_data, or
            #  self._start_index plus the number of bytes still needed for the packet_data.
            end_index = min(len(self._random_data), self._start_index + (data_len - len(packet_data)))
            # copy data from self._random_data, starting at self._start_index and
            # ending at end_index, to packet_data.
            packet_data += self._random_data[self._start_index:end_index]
            # add the data to the hash calculation
            data_hash.update(self._random_data[self._start_index:end_index])
            # calculate self._start_index for next time around
            self._start_index = end_index + 1
            if self._start_index > len(self._random_data):
                self._start_index = 0
        # get the next packetID
        PacketGenerator.allocated_lock.acquire()
        packetID = self._rand.choice(list(PacketGenerator.ALLOCATABLE_PACKET_ID - PacketGenerator.allocated))
        # Set packetID as used
        PacketGenerator.allocated.add(packetID)
        PacketGenerator.allocated_lock.release()
        # assemble the packet
        packet = struct.pack('!H', packetID) + struct.pack('!H', local_packet_length) + packet_data + data_hash.digest()
        # place the information into the Queue
        return (packet, packetID, local_packet_length, data_hash.hexdigest(),)


if __name__ == '__main__':
    import tests.packetGenerator_test

    tests.packetGenerator_test.runtests
