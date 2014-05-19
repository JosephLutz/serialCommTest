# msgMonitor
import threading
import Queue

from config import *


class ThreadMonitorException(BaseException):
	"""Thread exceptions originating in the ThreadMonitor"""


class ThreadMonitor(threading.Thread):
	# static dictionary of all threads
	threadMap = {}
	threadMapLock = threading.Lock()
	# the queue for ordering, storing and then displaying thread messages
	msg_queue = Queue.Queue()

	def __init__(self, *args, **kwargs):
		super(ThreadMonitor, self).__init__(*args, **kwargs)
		self.running_lock = threading.Lock()
		# value stating weather the thread should continue to execute or
		# terminate at the earliest possibility
		self.running = False
		# set thread_id
		self.threadMapLock.acquire()
		available_id = (set(xrange(START_THREAD_ID, MAX_THREAD_ID)) -
			set(self.threadMap.keys()))
		if len(available_id) is 0:
			self.threadMapLock.release()
			raise ThreadMonitorException
		self.thread_id = available_id.pop()
		self.threadMap[self.thread_id] = self
		self.threadMapLock.release()

	def run(self):
		self.running_lock.acquire()
		self.running = True
		try:
			# run the thread
			self.locked_running()
		except:
			# cleanup when any exception occurs
			if not self.running_lock.locked():
				self.running_lock.acquire()
			self.running = False
			raise
		finally:
			# cleanup threadMap of this thread
			self.threadMapLock.acquire()
			self.threadMap[self.thread_id] = None
			self.threadMapLock.release()
			# release the running_lock
			self.running_lock.release()

	def locked_running(self):
		pass

	def join(self, *args, **kwargs):
		# Inform the thread to terminate if still running
		self.running_lock.acquire()
		if self.running:
			self.running = False
		self.running_lock.release()
		# wait for the thread to terminate
		threading.Thread.join(self, *args, **kwargs)

	@staticmethod
	def join_all():
		ThreadMonitor.threadMapLock.acquire()
		# inform all threads to terminate
		for threadMapKey in ThreadMonitor.threadMap:
			if ThreadMonitor.threadMap[threadMapKey] is None:
				continue
			ThreadMonitor.threadMapLock.release()
			ThreadMonitor.threadMap[threadMapKey].running_lock.acquire()
			if ThreadMonitor.threadMap[threadMapKey].running:
				ThreadMonitor.threadMap[threadMapKey].running = False
			ThreadMonitor.threadMap[threadMapKey].running_lock.release()
			ThreadMonitor.threadMapLock.acquire()
		# Wait for each thread to be joined in succession
		for threadMapKey in ThreadMonitor.threadMap:
			if ThreadMonitor.threadMap[threadMapKey] is not None:
				ThreadMonitor.threadMapLock.release()
				ThreadMonitor.threadMap[threadMapKey].join()
				ThreadMonitor.threadMapLock.acquire()
				ThreadMonitor.threadMap[threadMapKey] = None
		ThreadMonitor.threadMapLock.release()

	@staticmethod
	def clean_terminated():
		thread_ids_to_clean = []
		# release the thread_ids for all thread_ids marked as None (terminated threads)
		ThreadMonitor.threadMapLock.acquire()
		# find which threads to clean
		for threadMapKey in ThreadMonitor.threadMap:
			if ThreadMonitor.threadMap[threadMapKey] is None:
				thread_ids_to_clean.append(threadMapKey)
		# clean the thread_ids
		for threadMapKey in thread_ids_to_clean:
			ThreadMonitor.threadMap.pop(threadMapKey, None)
		ThreadMonitor.threadMapLock.release()


if __name__ == '__main__':
	import tests.testThreadMonitor
	tests.testThreadMonitor.runtests()

# Message are placed onto the Queue named msg_queue.
# These messages are a tuple of three items. A threadId, message data,
# and a string message.
# threadId: This gives which thread is sending the message.
#     If the thread is the main thread then the threadId is None.
# message data: Either a dictionary of key, value pairs or None for no data sent.
#     The key, value pairs will be used in formatting the message string.
#     The keys in SPECIAL_MSG_DATA_KEYS will be used else where and for the
#     formatting will be empty strings.
# string message: is ether an int, string, or unicode. If the type is int,
#     there is a lookup dictionary in messageQueueMessages for common messages.
#     Otherwise use the string message with the message data as it's
#     format parameters.
