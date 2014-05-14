# msgMonitor_test
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

import threadMonitor

class testThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.runLock = threading.Lock()
        self.threadID = threadMonitor.getNextThreadID(thread_obj=self)
	def run(self):
		self.runLock.acquire()
		self.running = True
		while self.running:
			self.runLock.release()
			time.sleep(1.0)
			self.runLock.acquire()
		self.runLock.release()
		threadMonitor.threadListLock.acquire()
		threadMonitor.threadList[self.threadID] = None
		threadMonitor.threadListLock.release()

class TestMsgMonitor(unittest.TestCase):
	def setUp(self):
		self.test_event = threading.Event()
	def test_threadList(self):
		# check that only one thread is created
		threadMonitor.threadListLock.acquire()
		self.assertTrue(len(threadMonitor.threadList) is 0)
		threadMonitor.threadListLock.release()
		# check that exception is not raised
		try:
			t = testThread()
			self.assertTrue(t.threadID is not None)
			self.assertTrue(isinstance(t.threadID, int))
			self.assertTrue(t.threadID >= 0))
			self.assertTrue(t.threadID <= 65535)
		except threading.ThreadError:
			self.assertTrue(False)
		# check that exception is raised when no more threadID available
		try:
			for i in range(65536):
				t = testThread()
				self.assertTrue(t.threadID is not None)
				self.assertTrue(isinstance(t.threadID, int))
				self.assertTrue(t.threadID >= 0))
				self.assertTrue(t.threadID <= 65535)
				self.assertTrue(threadList[t.threadID] is t)
		except threading.ThreadError:
			self.assertTrue(True)


		'''
		# run setThread() on a thread already set
		self.assertTrue(msgMonitor.setThread(t))
		print threadList
		self.assertTrue(t.threadID is threadID)
		# run setThread() on a thread for the first time without an ID set
		threadID += 1
		t = testThread(threadID)
		self.assertTrue(t.threadID is threadID)
		self.assertTrue(msgMonitor.setThread(t))
		self.assertTrue(t.threadID is threadID)
		'''

	def test_joinAllThreads(self):
		start_count = 0
		num_start = 12
		# start some threads
		if len(threadList) < 1:
			# threads need to be created
			# let other tests run first
			time.sleep(2.0)
			for i in range(num_start)
				try:
					t = testThread()
			except threading.ThreadError:
				self.assertTrue(False)
		else:
			# start some threads
			t = None
			threadMonitor.threadListLock.acquire()
			for i in range(len(threadMonitor.threadList)):
				if (i in threadMonitor.threadList and threadMonitor.threadList is not None):
					threadMonitor.threadList[i].start()
					start_count += 1

			threadMonitor.threadListLock.release()


def runtests():
	unittest.main()
if __name__ == '__main__':
	runtests()
