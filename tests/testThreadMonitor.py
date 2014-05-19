# msgMonitor_test

import threading
import unittest
import Queue
import time

if __name__ == '__main__':
	import os
	import sys

	importDirectory = os.getcwd()
	if os.path.basename(importDirectory) in ['tests']:
		importDirectory = os.path.dirname(importDirectory)
	sys.path = [importDirectory] + sys.path

import threadMonitor
from config import *


class TestThread(threadMonitor.ThreadMonitor):
	def __init__(self, *args, **kwargs):
		super(TestThread, self).__init__(*args, **kwargs)
		self.work_started = False
		self.work_ended = False
		self.thread_exception = False
		self.thread_exception_running_lock = False
		self.thread_state_lock = threading.Lock()
		self.exception_encountered = None

	def locked_running(self):
		try:
			self.thread_state_lock.acquire()
			self.work_started = True
			self.thread_state_lock.release()
			while self.running:
				self.running_lock.release()
				time.sleep(0.05)
				self.thread_state_lock.acquire()
				if self.thread_exception:
					if self.thread_exception_running_lock:
						self.running_lock.acquire()
					self.thread_state_lock.release()
					raise BaseException
				self.thread_state_lock.release()
				self.running_lock.acquire()
		except BaseException:
			self.exception_encountered = True
			# catch exception and perform any cleanup needed
			if self.thread_state_lock.locked():
				self.thread_state_lock.release()
			raise
		else:
			self.exception_encountered = False
		finally:
			self.thread_state_lock.acquire()
			self.work_ended = True
			self.thread_state_lock.release()


class TestThreadMonitor(unittest.TestCase):
	def setUp(self):
		threadMonitor.ThreadMonitor.threadMapLock.acquire()
		threadMonitor.ThreadMonitor.threadMap = {}
		threadMonitor.ThreadMonitor.threadMapLock.release()
		threadMonitor.ThreadMonitor.threadMapLock = threading.Lock()
		threadMonitor.ThreadMonitor.msg_queue = Queue.Queue()

	def test_object_creation(self):
		# no threads
		self.assertTrue(len(threadMonitor.ThreadMonitor.threadMap) is 0)
		# first thread
		t = threadMonitor.ThreadMonitor()
		self.assertTrue(isinstance(t, threadMonitor.ThreadMonitor))
		self.assertTrue(len(threadMonitor.ThreadMonitor.threadMap) is 1)
		self.assertTrue(isinstance(t.thread_id, int))
		self.assertTrue(START_THREAD_ID <= t.thread_id < MAX_THREAD_ID)
		self.assertTrue(threadMonitor.ThreadMonitor.threadMap[t.thread_id] is t)
		# second thread
		t = TestThread()
		self.assertTrue(isinstance(t, TestThread))
		self.assertTrue(len(threadMonitor.ThreadMonitor.threadMap) is 2)
		self.assertTrue(isinstance(t.thread_id, int))
		self.assertTrue(START_THREAD_ID <= t.thread_id < MAX_THREAD_ID)
		self.assertTrue(threadMonitor.ThreadMonitor.threadMap[t.thread_id] is t)
		# create over MAX_THREAD_ID number of threads
		try:
			for count in xrange(START_THREAD_ID, MAX_THREAD_ID + 1):
				t = TestThread()
				self.assertTrue(isinstance(t, TestThread))
				self.assertTrue(isinstance(t.thread_id, int))
				self.assertTrue(START_THREAD_ID <= t.thread_id < MAX_THREAD_ID)
				self.assertTrue(threadMonitor.ThreadMonitor.threadMap[t.thread_id] is t)
		except threadMonitor.ThreadMonitorException:
			self.assertTrue(True)
		else:
			self.assertTrue(False)

	def _create_thread(self, *args, **kwargs):
		# create the thread
		t = TestThread(*args, **kwargs)
		t.thread_state_lock.acquire()
		self.assertFalse(t.work_started)
		self.assertFalse(t.work_ended)
		t.thread_state_lock.release()
		t.running_lock.acquire()
		self.assertFalse(t.running)
		t.running_lock.release()
		return t

	def _thread_running_state(self, t):
		# check state now
		t.thread_state_lock.acquire()
		self.assertTrue(t.work_started)
		self.assertFalse(t.work_ended)
		t.thread_state_lock.release()
		t.running_lock.acquire()
		self.assertTrue(t.running)
		t.running_lock.release()

	def _thread_final_state(self, t):
		# check final state
		t.thread_state_lock.acquire()
		self.assertTrue(t.work_started)
		self.assertTrue(t.work_ended)
		t.thread_state_lock.release()
		t.running_lock.acquire()
		self.assertFalse(t.running)
		t.running_lock.release()

	def test_run(self):
		t = self._create_thread()
		# start the thread
		t.start()
		# allow a context switch
		time.sleep(0.01)
		self._thread_running_state(t)
		# set to stop running
		t.running_lock.acquire()
		t.running = False
		t.running_lock.release()
		# allow a context switch and wait for thread to terminate
		time.sleep(0.1)
		self._thread_final_state(t)

	def test_exception_in_run(self):
		# iterate over each state of the running_lock for the new thread
		for running_lock_state in [True, False]:
			t = self._create_thread(name='!!! EXPECTING EXCEPTION !!! running_lock_state={0}'.format(running_lock_state))
			# start the thread
			t.start()
			# allow a context switch
			time.sleep(0.01)
			self._thread_running_state(t)
			# tell thread to throw exception with running_lock set to running_lock_state
			#try:
			t.thread_state_lock.acquire()
			t.thread_exception = True
			t.thread_exception_running_lock = running_lock_state
			t.thread_state_lock.release()
			# allow a context switch and wait for thread to terminate
			t.join()
			if t.exception_encountered is None:
				self.assertTrue(False)
			elif t.exception_encountered:
				self.assertTrue(True)
			else:
				self.assertTrue(False)
			self._thread_final_state(t)

	def test_join(self):
		t = self._create_thread()
		# start the thread
		t.start()
		# allow a context switch
		time.sleep(0.01)
		self._thread_running_state(t)
		# join the thread
		t.join()
		self._thread_final_state(t)

	def _common_multithread_test(self, num_threads, term_thread_index):
		# self check
		self.assertTrue(num_threads >= term_thread_index)
		# create three threads
		thread_list = []
		for _ in xrange(num_threads):
			thread_list.append(self._create_thread())
		# check the number of assigned thread_ids is same as number of threads
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
			self._thread_running_state(t)
		# terminate the term_thread_index thread and wait for it to be joined
		thread_list[term_thread_index].running_lock.acquire()
		thread_list[term_thread_index].running = False
		thread_list[term_thread_index].running_lock.release()
		thread_list[term_thread_index].join()
		# check the number of assigned thread_ids is same as number of threads
		threadMonitor.ThreadMonitor.threadMapLock.acquire()
		self.assertTrue(len(threadMonitor.ThreadMonitor.threadMap) is len(thread_list))
		# and check that the threadMap for the thread_id is set to None
		self.assertTrue(threadMonitor.ThreadMonitor.threadMap[thread_list[term_thread_index].thread_id] is None)
		threadMonitor.ThreadMonitor.threadMapLock.release()
		# check the state of the three threads
		#  running Threads
		for t in thread_list[:term_thread_index] + thread_list[(term_thread_index + 1):]:
			self._thread_running_state(t)
		#  terminated Thread
		thread_list[term_thread_index].thread_state_lock.acquire()
		self.assertTrue(thread_list[term_thread_index].work_started)
		self.assertTrue(thread_list[term_thread_index].work_ended)
		thread_list[term_thread_index].thread_state_lock.release()
		thread_list[term_thread_index].running_lock.acquire()
		self.assertFalse(thread_list[term_thread_index].running)
		thread_list[term_thread_index].running_lock.release()
		return thread_list

	def test_join_all(self):
		thread_list = self._common_multithread_test(num_threads=3, term_thread_index=1)
		# join all threads
		threadMonitor.ThreadMonitor.join_all()
		# check final state
		for t in thread_list:
			self._thread_final_state(t)

	def test_clean_terminated(self):
		term_thread_index = 1
		thread_list = self._common_multithread_test(num_threads=3, term_thread_index=term_thread_index)
		# clean up the terminated thread_ids
		threadMonitor.ThreadMonitor.clean_terminated()
		# check the number of assigned thread_ids is same as number of threads minus 1
		threadMonitor.ThreadMonitor.threadMapLock.acquire()
		self.assertTrue(len(threadMonitor.ThreadMonitor.threadMap) is (len(thread_list) - 1))
		# and check that the threadMap for the thread_id no longer exists
		self.assertFalse(thread_list[term_thread_index].thread_id in threadMonitor.ThreadMonitor.threadMap)
		threadMonitor.ThreadMonitor.threadMapLock.release()
		# join all threads to cleanup
		threadMonitor.ThreadMonitor.join_all()


def runtests():
	unittest.main()


if __name__ == '__main__':
	runtests()
