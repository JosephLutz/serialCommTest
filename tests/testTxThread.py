# txThread_test

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
import txThread
import threadMonitor


class DataSendObj():
	def __init__(self):
		self.test_thread_send_startup = False
		self.test_thread_send_start = False
		self.test_send_data = False
		self.test_thread_send_stop = False
		self.data_send_obj_lock = threading.Lock()
		self.loop = True

	def thread_send_startup(self):
		self.test_thread_send_startup = True

	def thread_send_start(self):
		self.test_thread_send_start = True

	def send_data(self):
		self.test_send_data = True
		self.data_send_obj_lock.acquire()
		loop = self.loop
		self.data_send_obj_lock.release()
		return loop

	def thread_send_stop(self):
		self.test_thread_send_stop = True


class TestTxThread(unittest.TestCase):
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
		tx = txThread.TxThread(send_obj)
		self.assertTrue(isinstance(tx, txThread.TxThread))
		# test that the object is created with all arguments
		tx = txThread.TxThread(send_obj, thread_event, name='tx_thread-unittest-1')
		self.assertTrue(isinstance(tx, txThread.TxThread))
		# test the msg_queue gets a message (a message is a tuple of three items)
		msg = threadMonitor.ThreadMonitor.msg_queue.get()
		self.assertTrue(isinstance(msg, tuple) and len(msg) is 3)

	def test_thread(self):
		send_obj = DataSendObj()
		thread_event = threading.Event()
		tx = txThread.TxThread(send_obj, thread_event, name='tx_thread-unittest-2')
		try:
			self.assertFalse(tx.sync_rxtx_event.is_set())
			tx.start()
			tx.sync_rxtx_event.wait()
			tx.running_lock.acquire()
			self.assertTrue(tx.sync_rxtx_event.is_set())
			self.assertTrue(tx.running)
			self.assertTrue(send_obj.test_thread_send_startup)
			self.assertFalse(thread_event.is_set())
			thread_event.set()
			tx.running_lock.release()
			# Allow context switch and release of thread_event.wait()
			time.sleep(0.001)
			tx.running_lock.acquire()
			self.assertTrue(thread_event.is_set())
			self.assertTrue(send_obj.test_thread_send_start)
			tx.running_lock.release()
			start_time = time.time()
			# run the thread for 1.5 seconds
			while (time.time() - start_time) < 0.05:
				self.assertTrue(send_obj.test_send_data)
			send_obj.data_send_obj_lock.acquire()
			send_obj.loop = False
			send_obj.data_send_obj_lock.release()
			# Allow context switch
			time.sleep(0.01)
			self.assertTrue(send_obj.test_thread_send_stop)
			self.assertTrue(True)
		except BaseException:
			self.assertTrue(False)
			# clean-up
			if not thread_event.is_set():
				thread_event.set()
			raise
		finally:
			self.assertFalse(tx.running)
			tx.join()


def runtests():
	unittest.main()


if __name__ == '__main__':
	runtests()
