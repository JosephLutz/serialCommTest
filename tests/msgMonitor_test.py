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

import msgMonitor

class testThread(threading.Thread):
	def __init__(self, threadID=None):
		threading.Thread.__init__(self)
		self.runLock = threading.Lock()
		self.threadID = threadID
	def run(self):
		self.runLock.acquire()
		self.running = True
		while self.running:
			self.runLock.release()
			time.sleep(1.0)
			self.runLock.acquire()
		self.runLock.release()

class TestMsgMonitor(unittest.TestCase):
	def setUp(self):
		pass
	def test_setThread(self):
		from msgMonitor import l_threadList as threadList
		print threadList
		t = testThread()
		self.assertTrue(t.threadID is None)
		# run setThread() on a thread for the first time without an ID set
		self.assertTrue(msgMonitor.setThread(t))
		print threadList
		threadID = t.threadID
		self.assertTrue(threadID is not None)
		self.assertTrue(threadList[t.threadID] is t)
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

	def test_joinThreads(self):
		pass
	def test_joinAllThreads(self):
		pass

def runtests():
	unittest.main()
if __name__ == '__main__':
	runtests()
