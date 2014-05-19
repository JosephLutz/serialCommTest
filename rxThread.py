# TxThread
import threading

import threadMonitor
from config import *


class RxThread(threadMonitor.ThreadMonitor):
	# Thread for running reads from data_get_obj.
	# NOTE:
	#   data_get_obj.threadStartup() is run before event sync_rxtx_event.
	#   Event sync_rxtx_event will be cleared before event thread_event blocks.
	def __init__(self, data_get_obj, thread_event=None, *args, **kwargs):
		super(RxThread, self).__init__(*args, **kwargs)
		self.data_get_obj = data_get_obj
		self.data_get_obj.rx_thread = self
		# Blocks run until event is set in other thread
		self.thread_event = thread_event
		# Used to notify when data_get_obj.threadStartup() is completed
		if ENABLE_SYNC_RX_TX_THREADS:
			# sync RxThread and TxThread
			self.sync_rxtx_event = threading.Event()
		else:
			self.sync_rxtx_event = None
		if self.msg_queue:
			# notify 'thread created' using msg_queue
			self.msg_queue.put((self.thread_id, {'thread_type': 'RX'}, THREAD_CREATED))

	def locked_running(self):
		try:
			# thread starting code
			self.data_get_obj.thread_get_startup()
			if ENABLE_SYNC_RX_TX_THREADS:
				if self.msg_queue:
					# notify 'RX thread ready' using msg_queue
					self.msg_queue.put((self.thread_id, {'thread_type': 'RX'}, THREAD_READY))
				if not self.sync_rxtx_event.is_set():
					self.sync_rxtx_event.set()
			# block until event is set in other thread
			if self.thread_event:
				if self.msg_queue:
					# notify 'thread_event.wait' using msg_queue
					self.msg_queue.put((self.thread_id, {'thread_type': 'RX'}, THREAD_SYNC_WAIT))
				self.running_lock.release()
				self.thread_event.wait()
				self.running_lock.acquire()
			if self.msg_queue:
				# notify 'thread starting' using msg_queue
				self.msg_queue.put((self.thread_id, {'thread_type': 'RX'}, THREAD_STARTING))
			# anything that needs to happen just before the thread loop starts
			self.data_get_obj.thread_get_start()
			while self.running:
				self.running_lock.release()
				if self.data_get_obj.get_data():
					self.running_lock.acquire()
				else:
					# finished reading
					self.running_lock.acquire()
					self.running = False
			self.running_lock.release()
			# anything that needs to happen just after the thread loop ends
			self.data_get_obj.thread_get_stop()
			self.running_lock.acquire()
			if self.msg_queue:
				# notify 'thread stopped' using msg_queue
				self.msg_queue.put((self.thread_id, {'thread_type': 'RX'}, THREAD_STOPPED))
		except:
			if not self.sync_rxtx_event.is_set():
				self.sync_rxtx_event.set()
			raise


if __name__ == '__main__':
	import tests.testRxThread
	tests.testRxThread.runtests()
