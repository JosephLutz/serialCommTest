# packetGenerator
import threading
import hashlib
import random
import struct
import Queue
import time

from msgMonitor import GENERATE_DATA

class PacketGenerator(threading.Thread):
	'''
	Generates the information for a packet

	This thread should be started before any TxThreads and
	should be terminated only after all TxThreads have been joined.
	
	A packet is a byte string containing:
	  1.)  packetID:     (0  to  65535)
	  2.)  packetLen:    (_MIN_PACKET_LEN  to  _MAX_PACKET_LEN) a number less than 65535
	  3.)  data:         (_MIN_DATA_LENGTH  to  _MAX_DATA_LEN) number of bytes
	  4.)  dataHash:     (_HASHLIB_ALGORITHM().digest_size) number of bytes
	The data stored in the queue is a tuple containing:
	  1.)  packet:       The above format of packet
	  2.)  packetID:     Same value as in the packet
	  3.)  packetLen:    Same value as in the packet
	  4.)  dataHash:     Hex representation of the dataHash above
	'''
	_NUMBER = 0                 # Initial number of packets in the queue
	_WAIT_TIMEOUT = 1.0         # Wait time before checking the thread is still running
	_PACKET_SIZE = None         # The size of the packets to generate.
	                            #  random lengths (within constraints) if set to None
	                            #algorithm used to generate the hash
	_HASHLIB_ALGORITHM = hashlib.sha256
	_RAND_DATA_SIZE = 10240     #Total number of random bytes generated
	_MIN_DATA_LENGTH = 10       #Minimum length of the data in the packet
	_MAX_PACKET_LEN = 65535     #Length of the largest packet
	                            #Max length of the data portion of the packet
	_MAX_DATA_LEN = _MAX_PACKET_LEN - (_HASHLIB_ALGORITHM().digest_size + (len(struct.pack('!H', 0)) * 2))
	                            #Minimum length of the packet
	_MIN_PACKET_LEN = _MAX_PACKET_LEN - _MAX_DATA_LEN + _MIN_DATA_LENGTH
	_MAX_PACKET_ID = 1024
	dataLock = threading.Lock() #Lock used to access and updated static data in PacketGenerator objects
	alocated = set()            # the allocated packetIDs
	                            #The totale available packetIDs
	_ALLOCATABLE_PACKETID = set(xrange(_MAX_PACKET_ID))
	                            #Hashable value that will seed the random number generator
	_RANDON_SEED = '{time}{len}'.format(time=time.time(), len=len(alocated))

	def __init__(self, threadName, threadID=None, msgQueue=None, bytes=_RAND_DATA_SIZE, printableChars=False, seed=None):
		threading.Thread.__init__(self)
		self.running = False
		self.threadName = threadName
		self.threadID = threadID
		self.runLock = threading.Lock()
		# Queue that holds each packet
		self.queue = Queue.Queue()
		# number of packets to keep in the queue
		self.number = PacketGenerator._NUMBER
		# blocks openSerialPort untill at least one packet is ready
		self.packetUsed = threading.Event()
		# seed and init random numbers
		if seed is None:
			seed = PacketGenerator._RANDON_SEED
		self.rand = random.SystemRandom(seed)
		# random data used for for sending
		if msgQueue:
			msgQueue.put((None, {'bytes':bytes}, GENERATE_DATA))
		if printableChars:
			self.randomData = ''.join([chr(self.rand.randint(33,126)) for i in range(bytes)])
		else:
			self.randomData = ''.join([chr(self.rand.randint(1,255)) for i in range(bytes)])
		# the next index of self.randomData to start gathering the data for the next packet
		self.startIndex = 0

	def run(self):
		self.runLock.acquire()
		self.running = True
		while self.running:
			if self.queue.qsize() < self.number:
				self.makePackets(self.number - self.queue.qsize())
			self.runLock.release()
			self.packetUsed.wait(PacketGenerator._WAIT_TIMEOUT)
			self.runLock.acquire()
			if self.packetUsed.is_set():
				self.packetUsed.clear()
		self.runLock.release()
		# empty out the packet queue
		while not self.queue.empty():
			self.queue.get_nowait()
	
	def makePackets(self, number, packetLength=_PACKET_SIZE):
		'''
		number: number of packets to generate
		packetLength: is the length of each packet. If None then packetLength is randomly generated

		The random data will be used for the packetData.
		Loop through the randome data untill packetData is fully populated.
		'''
		for packetCount in range(number):
			# determine packetLen and dataLen
			if packetLength is None:
				packetLen = (
					(len(struct.pack('!H', 0)) * 2) + 
					self.rand.randint(PacketGenerator._MIN_DATA_LENGTH, PacketGenerator._MAX_DATA_LEN) +
					PacketGenerator._HASHLIB_ALGORITHM().digest_size)
			# generate the packetData
			packetData = ''
			dataHash = PacketGenerator._HASHLIB_ALGORITHM()
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
			packetID = self.rand.choice(list(PacketGenerator._ALLOCATABLE_PACKETID - PacketGenerator.alocated))
			# Set packetID as used
			PacketGenerator.alocated.add(packetID)
			PacketGenerator.dataLock.release()
			# assemble the packet
			packet = struct.pack('!H', packetID) + struct.pack('!H', packetLen) + packetData + dataHash.digest()
			# place the information into the Queue
			self.queue.put((packet, packetID, packetLen, dataHash.hexdigest()))

if __name__ == '__main__':
	import tests.packetGenerator_test
	tests.packetGenerator_test.runtests
