# TxThread
import threading
from msgMonitor import THREAD_CREATED
from msgMonitor import STARTING
from msgMonitor import STOPPED
from msgMonitor import THREAD_READY
from msgMonitor import THREAD_SYNC_WAIT

class RxThread(threading.Thread):
	'''
	Thread for running reads from dataGetObj.
	NOTE:
	  dataGetObj.threadStartup() is run before event syncRxTxEvent.
	  Event syncRxTxEvent will be cleared before event threadEvent blocks.
	'''
	_ENABLE_SYNC_RX_TX_THREADS = True

	def __init__(self, threadName, dataGetObj, threadID=None, msgQueue=None, threadEvent=None):
		threading.Thread.__init__(self)
		self.running = False
		self.threadName = threadName
		self.threadID = threadID
		self.dataGetObj = dataGetObj
		self.dataGetObj.rxThread = self
		self.runLock = threading.Lock()
		# Queue for sending state back to messaging thread
		self.msgQueue = msgQueue
		# Blocks run untill event is set in other thread
		self.threadEvent = threadEvent
		# Used to notify when dataGetObj.threadStartup() is compleated
		if RxThread._ENABLE_SYNC_RX_TX_THREADS:
			# sync RxThread and TxThread
			self.syncRxTxEvent = threading.Event()
		else:
			self.syncRxTxEvent = None
		if self.msgQueue:
			# notify 'thread created' using msgQueue
			self.msgQueue.put((self.threadID, None, THREAD_CREATED))
	
	def run(self):
		try:
			self.runLock.acquire()
			self.running = True
			# thread starting code
			self.dataGetObj.threadGetStartup()
			if RxThread._ENABLE_SYNC_RX_TX_THREADS:
				if self.msgQueue:
					# notify 'RX thread ready' using msgQueue
					self.msgQueue.put((self.threadID, None, THREAD_READY))
				if not self.syncRxTxEvent.is_set():
					self.syncRxTxEvent.set()
			# block untill event is set in other thread
			if self.threadEvent:
				if self.msgQueue:
					# notify 'threadEvent.wait' using msgQueue
					self.msgQueue.put((self.threadID, None, THREAD_SYNC_WAIT))
				self.runLock.release()
				self.threadEvent.wait()
				self.runLock.acquire()
			if self.msgQueue:
				# notify 'thread starting' using msgQueue
				self.msgQueue.put((self.threadID, None, STARTING))
			# anything that needs to happen just before the thread loop starts
			self.dataGetObj.threadGetStart()
			while self.running:
				self.runLock.release()
				if self.dataGetObj.getData():
					self.runLock.acquire()
				else:
					# finished reading
					self.runLock.acquire()
					self.running = False
			self.runLock.release()
			# anything that needs to happen just after the thread loop ends
			self.dataGetObj.threadGetStop()
			if self.msgQueue:
				# notify 'thread stopped' using msgQueue
				self.msgQueue.put((self.threadID, None, STOPPED))
		except:
			if not self.syncRxTxEvent.is_set():
				self.syncRxTxEvent.set()
			self.running = False
			try:
				# may cause aditional error if lock is held
				# and in particular place in code flow
				self.runLock.release()
			except:
				pass
			raise

if __name__ == '__main__':
	import tests.rxThread_test
	tests.rxThread_test.runtests
