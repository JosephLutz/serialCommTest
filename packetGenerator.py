# packetGenerator
import threading
import random
import struct
import Queue
import time

from config import *

from msgMonitor import GENERATE_DATA


#Max length of the data portion of the packet
_MAX_PACKET_DATA_LENGTH = MAX_PACKET_LENGTH - (PACKET_GENERATOR_HASHLIB_ALGORITHM().digest_size + (len(struct.pack('!H', 0)) * 2))

#Minimum length of the packet
_MIN_PACKET_LENGTH = MAX_PACKET_LENGTH - _MAX_PACKET_DATA_LENGTH + MIN_PACKET_DATA_LENGTH


class PacketGenerator(threading.Thread):
    # Generates the information for a packet
    #
    # This thread should be started before any TxThreads and
    # should be terminated only after all TxThreads have been joined.
    #
    # A packet is a byte string containing:
    #   1.)  packetID:     (0  to  65535)
    #   2.)  packetLen:    (_MIN_PACKET_LENGTH  to  MAX_PACKET_LENGTH) a number less than 65535
    #   3.)  data:         (MIN_PACKET_DATA_LENGTH  to  _MAX_PACKET_DATA_LENGTH) number of bytes
    #   4.)  dataHash:     (PACKET_GENERATOR_HASHLIB_ALGORITHM().digest_size) number of bytes
    # The data stored in the queue is a tuple containing:
    #   1.)  packet:       The above format of packet
    #   2.)  packetID:     Same value as in the packet
    #   3.)  packetLen:    Same value as in the packet
    #   4.)  dataHash:     Hex representation of the dataHash above

    #Lock used to access and updated static data in PacketGenerator objects
    dataLock = threading.Lock()

    # the allocated packetIDs
    allocated = set()

    #The total available packetIDs
    _ALLOCATABLE_PACKET_ID = set(xrange(MAX_PACKET_ID))

    #Hashable value that will seed the random number generator
    _RANDOM_SEED = '{time}{len}'.format(time=time.time(), len=len(allocated))

    def __init__(self, threadName, threadID=None, msgQueue=None, numBytes=RAND_DATA_SIZE, printableChars=False,
                 seed=None):
        """
        init method for PacketGenerator thread

        :type self: threading.Thread
        :param threadName: A name for the thread used when displaying a message in the msgQueue
        :param threadID: ID number used to identify the thread in the msgQueue
        :param msgQueue: Queue to send messages, status, and updates
        :param numBytes: number of random bytes to generate
        :param printableChars: True if only printable characters desired
        :param seed: customize the random seed
        """
        threading.Thread.__init__(self)
        self.running = False
        self.threadName = threadName
        self.threadID = threadID
        self.runLock = threading.Lock()
        # Queue that holds each packet
        self.queue = Queue.Queue()
        # number of packets to keep in the queue
        self.number = INITIAL_PACKET_NUMBER
        # blocks open_serial_port untill at least one packet is ready
        self.packetUsed = threading.Event()
        # seed and init random numbers
        if seed is None:
            seed = PacketGenerator._RANDOM_SEED
        self.rand = random.SystemRandom(seed)
        # random data used for for sending
        if msgQueue:
            msgQueue.put((None, {'numBytes': numBytes}, GENERATE_DATA))
        if printableChars:
            self.randomData = ''.join([chr(self.rand.randint(33, 126)) for i in range(numBytes)])
        else:
            self.randomData = ''.join([chr(self.rand.randint(1, 255)) for i in range(numBytes)])
        # the next index of self.randomData to start gathering the data for the next packet
        self.startIndex = 0

    def run(self):
        self.runLock.acquire()
        self.running = True
        while self.running:
            if self.queue.qsize() < self.number:
                self.makePackets(self.number - self.queue.qsize())
            self.runLock.release()
            self.packetUsed.wait(PACKET_GENERATOR_WAIT_TIMEOUT)
            self.runLock.acquire()
            if self.packetUsed.is_set():
                self.packetUsed.clear()
        self.runLock.release()
        # empty out the packet queue
        while not self.queue.empty():
            self.queue.get_nowait()

    def makePackets(self, number, packetLength=PACKET_SIZE):
        """
        Generates the packets of random data

        The random data will be used for the packetData.
        Loop through the random data until packetData is fully populated.

        :param number: The number of packets to be created
        :param packetLength: The length of the packets to be created
        """
        for packetCount in range(number):
            # determine packetLen and dataLen
            if packetLength is None:
                packetLen = (
                    (len(struct.pack('!H', 0)) * 2) +
                    self.rand.randint(MIN_PACKET_DATA_LENGTH, _MAX_PACKET_DATA_LENGTH) +
                    PACKET_GENERATOR_HASHLIB_ALGORITHM().digest_size)
            # generate the packetData
            packetData = ''
            dataHash = PACKET_GENERATOR_HASHLIB_ALGORITHM()
            dataLen = packetLen - (len(struct.pack('!H', 0)) * 2) - dataHash.digest_size
            while len(packetData) < dataLen:
                # endIndex is the smaller of, the length of self.randomData, or
                #  self.startIndex pluss the number of bytes still needed for the packetData.
                endIndex = min(len(self.randomData), self.startIndex + (dataLen - len(packetData)))
                # copy data from self.randomData, starting at self.startIndex and
                # ending at endIndex, to packetData.
                packetData += self.randomData[self.startIndex:endIndex]
                # add the data to the hash calculation
                dataHash.update(self.randomData[self.startIndex:endIndex])
                # calculate self.startIndex for next time around
                self.startIndex = endIndex + 1
                if self.startIndex > len(self.randomData):
                    self.startIndex = 0
            # get the next packetID
            PacketGenerator.dataLock.acquire()
            packetID = self.rand.choice(list(PacketGenerator._ALLOCATABLE_PACKET_ID - PacketGenerator.allocated))
            # Set packetID as used
            PacketGenerator.allocated.add(packetID)
            PacketGenerator.dataLock.release()
            # assemble the packet
            packet = struct.pack('!H', packetID) + struct.pack('!H', packetLen) + packetData + dataHash.digest()
            # place the information into the Queue
            self.queue.put((packet, packetID, packetLen, dataHash.hexdigest()))


if __name__ == '__main__':
    import tests.packetGenerator_test

    tests.packetGenerator_test.runtests
