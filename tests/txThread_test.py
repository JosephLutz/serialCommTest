# txThread_test
import traceback
import threading
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
import txThread

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

class dataSendObj():
	def __init__(self):
		self.test_threadSendStartup = False
		self.test_threadSendStart = False
		self.test_sendData = False
		self.test_threadSendStop = False
		self.dataSendObjLock = threading.Lock()
		self.loop = True
	def threadSendStartup(self):
		self.test_threadSendStartup = True
	def threadSendStart(self):
		self.test_threadSendStart = True
	def sendData(self):
		self.test_sendData = True
		self.dataSendObjLock.acquire()
		loop = self.loop
		self.dataSendObjLock.release()
		return loop
	def threadSendStop(self):
		self.test_threadSendStop = True

class TestTxThread(unittest.TestCase):
	def setUp(self):
		pass
	def test_ObjectCreation(self):
		sendObj = dataSendObj()
		msgQueue = Queue.Queue()
		threadEvent = threading.Event()
		# test that the object is created with minimal arguments
		tx = txThread.TxThread('unitTest', sendObj)
		self.assertTrue(isinstance(tx, txThread.TxThread))
		tx = None
		# test that the object is created with all arguments
		tx = txThread.TxThread('unitTest', sendObj, 1, msgQueue, threadEvent)
		self.assertTrue(isinstance(tx, txThread.TxThread))
		# test the msgQueue gets a message (a message is a tupe of three items)
		msg = msgQueue.get()
		self.assertTrue(isinstance(msg, tuple) and len(msg) is 3)
	def test_thread(self):
		testAssert = True
		sendObj = dataSendObj()
		msgQueue = Queue.Queue()
		threadEvent = threading.Event()
		tx = txThread.TxThread('unitTest', sendObj, 1, msgQueue, threadEvent)
		try:
			self.assertFalse(tx.syncRxTxEvent.is_set())
			tx.start()
			tx.syncRxTxEvent.wait()
			tx.runLock.acquire()
			self.assertTrue(tx.syncRxTxEvent.is_set())
			self.assertTrue(tx.running)
			self.assertTrue(sendObj.test_threadSendStartup)
			self.assertFalse(threadEvent.is_set())
			threadEvent.set()
			tx.runLock.release()
			# Allow context switch and release of threadEvent.wait()
			time.sleep(0.001)
			tx.runLock.acquire()
			self.assertTrue(threadEvent.is_set())
			self.assertTrue(sendObj.test_threadSendStart)
			tx.runLock.release()
			startTime = time.time()
			# run the thread for 1.5 seconds
			while (time.time() - startTime) < 1.5:
				self.assertTrue(sendObj.test_sendData)
			sendObj.dataSendObjLock.acquire()
			sendObj.loop = False
			sendObj.dataSendObjLock.release()
			time.sleep(0.01)
			self.assertTrue(sendObj.test_threadSendStop)
		except:
			print '\n' + getExceptionInfo()
			testAssert = False
			# clean up the thread
			if not tx.syncRxTxEvent.is_set():
				tx.syncRxTxEvent.set()
			if not threadEvent.is_set():
				threadEvent.set()
			tx.running = False
			try:
				tx.runLock.release()
			except:
				pass
		tx.join()
		self.assertFalse(tx.running)
		self.assertTrue(testAssert)


def runtests():
	unittest.main()
if __name__ == '__main__':
	runtests()
