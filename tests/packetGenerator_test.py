# packetGenerator_test
import traceback
import unittest
import Queue
import time

if __name__ == '__main__':
	import os, sys
	importDirectory = os.getcwd()
	if os.path.basename(importDirectory) in ['tests']:
		importDirectory = os.path.dirname(importDirectory)
	sys.path = [importDirectory] + sys.path

# Module to test
import packetGenerator

def getExceptionInfo():
	exc_type, exc_obj, exc_tb = sys.exc_info()
	fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
	if (exc_type is None or exc_obj is None or exc_tb is None):
		return 'No Exception Encountered'
	error_out = 'Exception Encountered'
	error_out += '{0}\n'.format('='*80)
	error_out += 'lineno:{lineno}, fname:{fname}'.format(fname=fname, lineno=exc_tb.tb_lineno)
	for line in traceback.format_tb(exc_tb):
		error_out += '{0}\n'.format(line)
	return ('\n{line:80}\n{out}\n{line:80}'.format(line='#'*80, out=error_out))

class TestPacketGenerator(unittest.TestCase):
	def setUp(self):
		pass
	def test_ObjectCreation(self):
		msgQueue = Queue.Queue()
		# test that the object is created with minimal arguments
		pktGen = packetGenerator.PacketGenerator('unitTest', 1)
		self.assertTrue(isinstance(pktGen, packetGenerator.PacketGenerator))
		pktGen = None
		# test that the object is created with all arguments
		pktGen = packetGenerator.PacketGenerator('unitTest', 1, msgQueue, 20, True, 'Seed String')
		self.assertTrue(isinstance(pktGen, packetGenerator.PacketGenerator))
		# test the msgQueue gets a message (a message is a tupe of three items)
		msg = msgQueue.get()
		self.assertTrue(isinstance(msg, tuple) and len(msg) is 3)
	def test_MakePackets(self):
		pktGen = packetGenerator.PacketGenerator('unitTest', 1, bytes=20)
		self.assertTrue(pktGen.queue.empty())
		pktGen.makePackets(1)
		self.assertFalse(pktGen.queue.empty())
		packet = pktGen.queue.get()
		self.assertTrue(isinstance(packet, tuple) and len(packet) is 4)
		self.assertTrue(pktGen.queue.empty())
	def test_thread(self):
		testAssert = True
		pktGen = packetGenerator.PacketGenerator('unitTest', 1, bytes=20)
		try:
			pktGen.start()
			self.assertTrue(pktGen.queue.empty())
			# give time to create first packets
			time.sleep(2.0)
			startTime = time.time()
			# run the thread for 3 seconds
			while (time.time() - startTime) < 3.0:
				self.assertFalse(pktGen.queue.empty())
				queueSize = pktGen.queue.qsize()
				# pull packet off of Queue
				pktGen.queue.get()
				newQueueSize = pktGen.queue.qsize()
				self.assertTrue((newQueueSize + 1) is queueSize)
				pktGen.packetUsed.set()
				# wait some time for the new packet to be generated
				time.sleep(0.3)
				newQueueSize = pktGen.queue.qsize()
				self.assertTrue(newQueueSize is queueSize)
			# Stop the thread
			pktGen.runLock.acquire()
			pktGen.running = False
			pktGen.runLock.release()
		except:
			print '\n' + getExceptionInfo()
			testAssert = False
			# clean up the thread
			if not pktGen.packetUsed.is_set():
				pktGen.packetUsed.set()
			pktGen.running = False
			try:
				pktGen.runLock.release()
			except:
				pass
		pktGen.join()
		self.assertTrue(pktGen.queue.empty())
		self.assertTrue(testAssert)


def runtests():
	unittest.main()
if __name__ == '__main__':
	runtests()
