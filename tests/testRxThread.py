# rxThread_test

import threading
import unittest
import Queue
import time
import sys
import os

if __name__ == '__main__':
	importDirectory = os.getcwd()
	if os.path.basename(importDirectory) in ['tests']:
		importDirectory = os.path.dirname(importDirectory)
	sys.path = [importDirectory] + sys.path

# Module to test
import rxThread
import threadMonitor


class DataSendObj():
	def __init__(self):
		self.test_thread_get_startup = False
		self.test_thread_get_start = False
		self.test_get_data = False
		self.test_thread_get_stop = False
		self.data_send_obj_lock = threading.Lock()
		self.loop = True

	def thread_get_startup(self):
		self.test_thread_get_startup = True

	def thread_get_start(self):
		self.test_thread_get_start = True

	def get_data(self):
		self.test_get_data = True
		self.data_send_obj_lock.acquire()
		loop = self.loop
		self.data_send_obj_lock.release()
		return loop

	def thread_get_stop(self):
		self.test_thread_get_stop = True


class TestRxThread(unittest.TestCase):
	def setUp(self):
		threadMonitor.ThreadMonitor.threadMapLock.acquire()
		threadMonitor.ThreadMonitor.threadMap = {}
		threadMonitor.ThreadMonitor.threadMapLock.release()
		threadMonitor.ThreadMonitor.threadMapLock = threading.Lock()
		threadMonitor.ThreadMonitor.msg_queue = Queue.Queue()

	def test_object_creation(self):
		send_obj = DataSendObj()
		thread_event = threading.Event()
		# test that the object is created with minimal arguments
		rx = rxThread.RxThread(send_obj)
		self.assertTrue(isinstance(rx, rxThread.RxThread))
		# test that the object is created with all arguments
		rx = rxThread.RxThread(send_obj, thread_event, name='tx_thread-unittest-1')
		self.assertTrue(isinstance(rx, rxThread.RxThread))
		# test the msg_queue gets a message (a message is a tuple of three items)
		msg = threadMonitor.ThreadMonitor.msg_queue.get()
		self.assertTrue(isinstance(msg, tuple) and len(msg) is 3)

	def test_thread(self):
		send_obj = DataSendObj()
		thread_event = threading.Event()
		rx = rxThread.RxThread(send_obj, thread_event, name='tx_thread-unittest-2')
		try:
			self.assertFalse(rx.sync_rxtx_event.is_set())
			rx.start()
			rx.sync_rxtx_event.wait()
			rx.running_lock.acquire()
			self.assertTrue(rx.sync_rxtx_event.is_set())
			self.assertTrue(rx.running)
			self.assertTrue(send_obj.test_thread_get_startup)
			self.assertFalse(thread_event.is_set())
			thread_event.set()
			rx.running_lock.release()
			# Allow context switch and release of thread_event.wait()
			time.sleep(0.001)
			rx.running_lock.acquire()
			self.assertTrue(thread_event.is_set())
			self.assertTrue(send_obj.test_thread_get_start)
			rx.running_lock.release()
			start_time = time.time()
			# run the thread for 1.5 seconds
			while (time.time() - start_time) < 0.05:
				self.assertTrue(send_obj.test_get_data)
			send_obj.data_send_obj_lock.acquire()
			send_obj.loop = False
			send_obj.data_send_obj_lock.release()
			time.sleep(0.01)
			self.assertTrue(send_obj.test_thread_get_stop)
			self.assertTrue(True)
		except BaseException:
			self.assertTrue(False)
			# clean-up
			if not thread_event.is_set():
				thread_event.set()
			raise
		rx.join()
		self.assertFalse(rx.running)


def runtests():
	unittest.main()


if __name__ == '__main__':
	runtests()
