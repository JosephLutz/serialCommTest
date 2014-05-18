# txThread_test
import traceback
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
        self.test_threadSendStartup = False
        self.test_threadSendStart = False
        self.test_sendData = False
        self.test_threadSendStop = False
        self.dataSendObjLock = threading.Lock()
        self.loop = True

    def thread_send_startup(self):
        self.test_threadSendStartup = True

    def thread_send_start(self):
        self.test_threadSendStart = True

    def send_data(self):
        self.test_sendData = True
        self.dataSendObjLock.acquire()
        loop = self.loop
        self.dataSendObjLock.release()
        return loop

    def thread_send_stop(self):
        self.test_threadSendStop = True


class TestTxThread(unittest.TestCase):
    def setUp(self):
        threadMonitor.ThreadMonitor.threadMapLock.acquire()
        threadMonitor.ThreadMonitor.threadMap = {}
        threadMonitor.ThreadMonitor.threadMapLock.release()
        threadMonitor.ThreadMonitor.threadMapLock = threading.Lock()
        threadMonitor.ThreadMonitor.msgQueue = Queue.Queue()

    def test_object_creation(self):
        sendObj = DataSendObj()
        threadEvent = threading.Event()
        # test that the object is created with minimal arguments
        tx = txThread.TxThread(sendObj)
        self.assertTrue(isinstance(tx, txThread.TxThread))
        tx = None
        # test that the object is created with all arguments
        tx = txThread.TxThread(sendObj, threadEvent, name='txThread-unittest-1')
        self.assertTrue(isinstance(tx, txThread.TxThread))
        # test the msgQueue gets a message (a message is a tupe of three items)
        msg = threadMonitor.ThreadMonitor.msgQueue.get()
        self.assertTrue(isinstance(msg, tuple) and len(msg) is 3)

    def test_thread(self):
        testAssert = True
        sendObj = DataSendObj()
        threadEvent = threading.Event()
        tx = txThread.TxThread(sendObj, threadEvent, name='txThread-unittest-2')
        try:
            self.assertFalse(tx.syncRxTxEvent.is_set())
            tx.start()
            tx.syncRxTxEvent.wait()
            tx.runLock.acquire()
            self.assertTrue(tx.syncRxTxEvent.is_set())
            self.assertTrue(tx.running)
            self.assertTrue(sendObj.test_threadSendStartup)
            self.assertFalse(threadEvent.is_set())
            threadEvent.set()
            tx.runLock.release()
            # Allow context switch and release of threadEvent.wait()
            time.sleep(0.001)
            tx.runLock.acquire()
            self.assertTrue(threadEvent.is_set())
            self.assertTrue(sendObj.test_threadSendStart)
            tx.runLock.release()
            startTime = time.time()
            # run the thread for 1.5 seconds
            while (time.time() - startTime) < 0.05:
                self.assertTrue(sendObj.test_sendData)
            sendObj.dataSendObjLock.acquire()
            sendObj.loop = False
            sendObj.dataSendObjLock.release()
            time.sleep(0.01)
            self.assertTrue(sendObj.test_threadSendStop)
        except:
            testAssert = False
            # clean-up
            if not threadEvent.is_set():
                threadEvent.set()
            raise
        tx.join()
        self.assertFalse(tx.running)
        self.assertTrue(testAssert)


def runtests():
    unittest.main()


if __name__ == '__main__':
    runtests()
