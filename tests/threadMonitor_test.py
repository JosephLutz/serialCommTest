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
from config import *

class testThread(threadMonitor.ThreadMonitor):
	def __init__(self):
		self.work_started = False
		self.work_ended = False
		threadMonitor.ThreadMonitor.__init__(self)
	def locked_running(self):
		self.work_started = True
		while self.running:
			self.runLock.release()
			time.sleep(1.0)
			self.runLock.acquire()
		self.work_ended = True

class TestMsgMonitor(unittest.TestCase):
	def setUp(self):
		threadMonitor.ThreadMonitor.threadMap = {}
		threadMonitor.ThreadMonitor.threadMapLock = threading.Lock()
		threadMonitor.ThreadMonitor.msgQueue = Queue.Queue()
	
	def test_object_creation(self):
		# no threads
		self.assertTrue(len(threadMonitor.ThreadMonitor.threadMap) is 0)
		# first thread
		t = threadMonitor.ThreadMonitor()
		self.assertTrue(isinstance(t, threadMonitor.ThreadMonitor))
		self.assertTrue(len(threadMonitor.ThreadMonitor.threadMap) is 1)
		self.assertTrue(isinstance(t.threadID, int))
		self.assertTrue(t.threadID >= START_THREAD_ID and t.threadID < MAX_THREAD_ID)
		self.assertTrue(threadMonitor.ThreadMonitor.threadMap[t.threadID] is t)
		# second thread
		t = testThread()
		self.assertTrue(isinstance(t, testThread))
		self.assertTrue(len(threadMonitor.ThreadMonitor.threadMap) is 2)
		self.assertTrue(isinstance(t.threadID, int))
		self.assertTrue(t.threadID >= START_THREAD_ID and t.threadID < MAX_THREAD_ID)
		self.assertTrue(threadMonitor.ThreadMonitor.threadMap[t.threadID] is t)
		# create over MAX_THREAD_ID number of threads
		try:
			for count in range(START_THREAD_ID, MAX_THREAD_ID + 1):
				t = testThread()
				self.assertTrue(isinstance(t, testThread))
				self.assertTrue(isinstance(t.threadID, int))
				self.assertTrue(t.threadID >= START_THREAD_ID and t.threadID < MAX_THREAD_ID)
				self.assertTrue(threadMonitor.ThreadMonitor.threadMap[t.threadID] is t)
		except threading.ThreadError:
			self.assertTrue(True)
		else:
			self.assertTrue(False)

	def test_run(self):
		# create the thread
		t = testThread()
		t.runLock.acquire()
		self.assertFalse(t.running)
		self.assertFalse(t.work_started)
		self.assertFalse(t.work_ended)
		t.runLock.release()
		# start the thread
		t.start()
		# allow a context switch
		time.sleep(0.01)
		# check state now
		t.runLock.acquire()
		self.assertTrue(t.running)
		self.assertTrue(t.work_started)
		self.assertFalse(t.work_ended)
		t.running = False
		t.runLock.release()
		# allow a context switch and wait for thread to terminate
		time.sleep(1.01)
		# check final state
		t.runLock.acquire()
		self.assertFalse(t.running)
		self.assertTrue(t.work_started)
		self.assertTrue(t.work_ended)
		t.runLock.release()

	def test_join(self):
		# create the thread
		t = testThread()
		t.runLock.acquire()
		self.assertFalse(t.running)
		self.assertFalse(t.work_started)
		self.assertFalse(t.work_ended)
		t.runLock.release()
		# start the thread
		t.start()
		# allow a context switch
		time.sleep(0.01)
		# check state now
		t.runLock.acquire()
		self.assertTrue(t.running)
		self.assertTrue(t.work_started)
		self.assertFalse(t.work_ended)
		t.runLock.release()
		# join the thread
		t.join()
		# check final state
		t.runLock.acquire()
		self.assertFalse(t.running)
		self.assertTrue(t.work_started)
		self.assertTrue(t.work_ended)
		t.runLock.release()

	def test_join_all(self):
		# create three threads
		thread_list = [testThread(), testThread(), testThread()]
		for t in thread_list:
			t.runLock.acquire()
			self.assertFalse(t.running)
			self.assertFalse(t.work_started)
			self.assertFalse(t.work_ended)
			t.runLock.release()
		# start the threads
		for t in thread_list:
			t.start()
		# allow a context switch
		time.sleep(0.01)
		# check state now
		for t in thread_list:
			t.runLock.acquire()
			self.assertTrue(t.running)
			self.assertTrue(t.work_started)
			self.assertFalse(t.work_ended)
			t.runLock.release()
		# terminate and join the second thread and wait for it to be joined
		thread_list[1].runLock.acquire()
		thread_list[1].running = False
		thread_list[1].runLock.release()
		thread_list[1].join()
		# check the state of the three threads
		#  Thread 1
		thread_list[0].runLock.acquire()
		self.assertTrue(thread_list[0].running)
		self.assertTrue(thread_list[0].work_started)
		self.assertFalse(thread_list[0].work_ended)
		thread_list[0].runLock.release()
		#  Thread 2
		thread_list[1].runLock.acquire()
		self.assertFalse(thread_list[1].running)
		self.assertTrue(thread_list[1].work_started)
		self.assertTrue(thread_list[1].work_ended)
		thread_list[1].runLock.release()
		#  Thread 3
		thread_list[2].runLock.acquire()
		self.assertTrue(thread_list[2].running)
		self.assertTrue(thread_list[2].work_started)
		self.assertFalse(thread_list[2].work_ended)
		thread_list[2].runLock.release()
		# join all threads
		threadMonitor.ThreadMonitor.join_all()
		# check final state
		for t in thread_list:
			t.runLock.acquire()
			self.assertFalse(t.running)
			self.assertTrue(t.work_started)
			self.assertTrue(t.work_ended)
			t.runLock.release()

	def test_clean_terminated(self):
		# create three threads
		thread_list = [testThread(), testThread(), testThread()]
		for t in thread_list:
			t.runLock.acquire()
			self.assertFalse(t.running)
			self.assertFalse(t.work_started)
			self.assertFalse(t.work_ended)
			t.runLock.release()
		# check the number of assigned threadIDs is same as number of threads
		threadMonitor.ThreadMonitor.threadMapLock.acquire()
		self.assertTrue(len(threadMonitor.ThreadMonitor.threadMap) is len(thread_list))
		threadMonitor.ThreadMonitor.threadMapLock.release()
		# start the threads
		for t in thread_list:
			t.start()
		# allow a context switch
		time.sleep(0.01)
		# check state now
		for t in thread_list:
			t.runLock.acquire()
			self.assertTrue(t.running)
			self.assertTrue(t.work_started)
			self.assertFalse(t.work_ended)
			t.runLock.release()
		# terminate and join the second thread and wait for it to be joined
		thread_list[1].runLock.acquire()
		thread_list[1].running = False
		thread_list[1].runLock.release()
		thread_list[1].join()
		# check the number of assigned threadIDs is same as number of threads
		threadMonitor.ThreadMonitor.threadMapLock.acquire()
		self.assertTrue(len(threadMonitor.ThreadMonitor.threadMap) is len(thread_list))
		# and check that the threadMap for the threadID is set to None
		self.assertTrue(threadMonitor.ThreadMonitor.threadMap[thread_list[1].threadID] is None)
		threadMonitor.ThreadMonitor.threadMapLock.release()
		# check the state of the three threads
		#  Thread 1
		thread_list[0].runLock.acquire()
		self.assertTrue(thread_list[0].running)
		self.assertTrue(thread_list[0].work_started)
		self.assertFalse(thread_list[0].work_ended)
		thread_list[0].runLock.release()
		#  Thread 2
		thread_list[1].runLock.acquire()
		self.assertFalse(thread_list[1].running)
		self.assertTrue(thread_list[1].work_started)
		self.assertTrue(thread_list[1].work_ended)
		thread_list[1].runLock.release()
		#  Thread 3
		thread_list[2].runLock.acquire()
		self.assertTrue(thread_list[2].running)
		self.assertTrue(thread_list[2].work_started)
		self.assertFalse(thread_list[2].work_ended)
		thread_list[2].runLock.release()
		# clean up the terminated threadIDs
		threadMonitor.ThreadMonitor.clean_terminated()
		# check the number of assigned threadIDs is same as number of threads minus 1
		threadMonitor.ThreadMonitor.threadMapLock.acquire()
		self.assertTrue(len(threadMonitor.ThreadMonitor.threadMap) is (len(thread_list) - 1))
		# and check that the threadMap for the threadID no longer exists
		self.assertFalse(threadMonitor.ThreadMonitor.threadMap.has_key(thread_list[1].threadID))
		threadMonitor.ThreadMonitor.threadMapLock.release()
		# join all threads to cleanup
		threadMonitor.ThreadMonitor.join_all()





# defunct code
if False:
	def test_threadMap(self):
		# check that only one thread is created
		threadMonitor.ThreadMonitor.threadMapLock.acquire()
		self.assertTrue(len(threadMonitor.ThreadMonitor.threadMap) is 0)
		threadMonitor.ThreadMonitor.threadMapLock.release()
		# check that exception is not raised
		try:
			t = testThread()
			threadMonitor.ThreadMonitor.threadMapLock.acquire()
			self.assertTrue(t.threadID is not None)
			self.assertTrue(isinstance(t.threadID, int))
			self.assertTrue(t.threadID >= 0)
			self.assertTrue(t.threadID <= 65535)
			if len(threadMonitor.ThreadMonitor.threadMap) is 1:
				self.assertTrue(True)
				self.assertTrue(threadMonitor.ThreadMonitor.threadMap[threadMonitor.ThreadMonitor.threadMap.keys()[0]] is t)
			else:
				self.assertTrue(False)
			threadMonitor.ThreadMonitor.threadMapLock.release()
		except threading.ThreadError:
			threadMonitor.ThreadMonitor.threadMapLock.release()
			self.assertTrue(False)
		# check that exception is raised when all threadIDs are used
		threadMonitor.ThreadMonitor.threadMapLock.acquire()
		try:
			for i in range(65536):
				threadMonitor.ThreadMonitor.threadMapLock.release()
				t = testThread()
				threadMonitor.ThreadMonitor.threadMapLock.acquire()
				self.assertTrue(t.threadID is not None)
				self.assertTrue(isinstance(t.threadID, int))
				self.assertTrue(t.threadID >= 0)
				self.assertTrue(t.threadID <= 65535)
				self.assertTrue(threadMap[t.threadID] is t)
		except threading.ThreadError:
			threadMonitor.ThreadMonitor.threadMapLock.release()
			self.assertTrue(True)
		'''
		# Let the rest of the tests use threadMap
		self.test_threadMap_event.set()

		'''
		# run setThread() on a thread already set
		self.assertTrue(msgMonitor.setThread(t))
		print threadMap
		self.assertTrue(t.threadID is threadID)
		# run setThread() on a thread for the first time without an ID set
		threadID += 1
		t = testThread(threadID)
		self.assertTrue(t.threadID is threadID)
		self.assertTrue(msgMonitor.setThread(t))
		self.assertTrue(t.threadID is threadID)

	def test_joinAllThreads(self):
		#self.test_threadMap_event.wait()
		threadMonitor.ThreadMonitor.threadMapLock.acquire()
		'''
		self.assertTrue(len(threadMonitor.ThreadMonitor.threadMap) > 24)
		# start the first 12 threads
		toStartThreadIDs = threadMonitor.ThreadMonitor.threadMap.keys()[:12]
		for tID in toStartThreadIDs:
			self.assertFalse(tID.is_alive())
			tID.start()
			self.assertTrue(tID.is_alive())
		threadMonitor.ThreadMonitor.threadMapLock.release()
		joinAllThreads()
		threadMonitor.ThreadMonitor.threadMapLock.acquire()
		for tID in threadMonitor.ThreadMonitor.threadMap:
			self.assertFalse(tID.is_alive())
		'''
		threadMonitor.ThreadMonitor.threadMapLock.release()




def runtests():
	unittest.main()
if __name__ == '__main__':
	runtests()
