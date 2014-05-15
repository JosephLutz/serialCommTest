# msgMonitor
import threading
import Queue

from config import *

class ThreadMonitor(threading.Thread):
	# static distionary of all threads
	threadMap = {}
	threadMapLock = threading.Lock()
	# the queue for ordering, storing and then displaying thread messages
	msgQueue = Queue.Queue()

	def __init__(self):
		threading.Thread.__init__(self)
		self.runLock = threading.Lock()
		self.running = False
		# set threadID
		self.threadMapLock.acquire()
		inUseIDs = set(self.threadMap.keys())
		availableIDs = set(range(START_THREAD_ID, MAX_THREAD_ID)) - inUseIDs
		if len(availableIDs) is 0:
			self.threadMapLock.release()
			raise threading.ThreadError
		self.threadID = availableIDs.pop()
		self.threadMap[self.threadID] = self
		self.threadMapLock.release()

	def run(self):
		self.runLock.acquire()
		self.running = True
		# run the thread
		self.locked_running()
		# cleanup threadMap of this thread
		self.threadMapLock.acquire()
		self.threadMap[self.threadID] = None
		self.threadMapLock.release()
		self.runLock.release()

	def join(self):
		# Inform the thread to terminate if still running
		self.runLock.acquire()
		if self.running:
			self.running = False
		self.runLock.release()
		# wait for the thread to terminate
		threading.Thread.join(self)

	@staticmethod
	def join_all():
		ThreadMonitor.threadMapLock.acquire()
		# inform all threads to terminate
		for threadMapKey in ThreadMonitor.threadMap:
				if ThreadMonitor.threadMap[threadMapKey] is None:
					continue
				ThreadMonitor.threadMapLock.release()
				ThreadMonitor.threadMap[threadMapKey].runLock.acquire()
				if ThreadMonitor.threadMap[threadMapKey].running:
					ThreadMonitor.threadMap[threadMapKey].running = False
				ThreadMonitor.threadMap[threadMapKey].runLock.release()
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
		threadIDs_to_clean = []
		# release the threadIDs for all threadIDs marked as None (terminated threads)
		ThreadMonitor.threadMapLock.acquire()
		# find which threads to clean
		for threadMapKey in ThreadMonitor.threadMap:
			if ThreadMonitor.threadMap[threadMapKey] is None:
				threadIDs_to_clean.append(threadMapKey)
		# clean the threadIDs
		for threadMapKey in threadIDs_to_clean:
			if ThreadMonitor.threadMap.pop(threadMapKey, None) is not None:
				raise threading.ThreadError
		ThreadMonitor.threadMapLock.release()


if __name__ == '__main__':
	import tests.threadMonitor_test
	tests.threadMonitor_test.runtests

# Message are placed onto the Queue named msgQueue.
# These messages are a tiple of three items. A threadId, message data,
# and a string message.
# threadId: This gives which thread is sending the message.
#     If the thread is the main thread then the threadId is None.
# message data: Either a dictionary of key, value pairs or None for no data sent.
#     The key, value pairs will be used in formatting the message string.
#     The keys in SPECIAL_MSG_DATA_KEYS will be used else where and for the
#     formatting will be empty strings.
# string message: is eithere an int, string, or unicode. If the type is int,
#     there is a lookup dictionary in messageQueueMessages for common messages.
#     Otherwise use the string message with the message data as it's
#     format parameters.


