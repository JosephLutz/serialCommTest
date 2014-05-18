# rxThread_test
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
import rxThread
import threadMonitor


class DataSendObj():
    def __init__(self):
        self.test_threadGetStartup = False
        self.test_threadGetStart = False
        self.test_getData = False
        self.test_threadGetStop = False
        self.dataSendObjLock = threading.Lock()
        self.loop = True

    def thread_get_startup(self):
        self.test_threadGetStartup = True

    def thread_get_start(self):
        self.test_threadGetStart = True

    def get_data(self):
        self.test_getData = True
        self.dataSendObjLock.acquire()
        loop = self.loop
        self.dataSendObjLock.release()
        return loop

    def thread_get_stop(self):
        self.test_threadGetStop = True


class TestRxThread(unittest.TestCase):
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
        rx = rxThread.RxThread(sendObj)
        self.assertTrue(isinstance(rx, rxThread.RxThread))
        rx = None
        # test that the object is created with all arguments
        rx = rxThread.RxThread(sendObj, threadEvent, name='txThread-unittest-1')
        self.assertTrue(isinstance(rx, rxThread.RxThread))
        # test the msgQueue gets a message (a message is a tupe of three items)
        msg = threadMonitor.ThreadMonitor.msgQueue.get()
        self.assertTrue(isinstance(msg, tuple) and len(msg) is 3)

    def test_thread(self):
        testAssert = True
        sendObj = DataSendObj()
        threadEvent = threading.Event()
        rx = rxThread.RxThread(sendObj, threadEvent, name='txThread-unittest-2')
        try:
            self.assertFalse(rx.syncRxTxEvent.is_set())
            rx.start()
            rx.syncRxTxEvent.wait()
            rx.runLock.acquire()
            self.assertTrue(rx.syncRxTxEvent.is_set())
            self.assertTrue(rx.running)
            self.assertTrue(sendObj.test_threadGetStartup)
            self.assertFalse(threadEvent.is_set())
            threadEvent.set()
            rx.runLock.release()
            # Allow context switch and release of threadEvent.wait()
            time.sleep(0.001)
            rx.runLock.acquire()
            self.assertTrue(threadEvent.is_set())
            self.assertTrue(sendObj.test_threadGetStart)
            rx.runLock.release()
            startTime = time.time()
            # run the thread for 1.5 seconds
            while (time.time() - startTime) < 0.05:
                self.assertTrue(sendObj.test_getData)
            sendObj.dataSendObjLock.acquire()
            sendObj.loop = False
            sendObj.dataSendObjLock.release()
            time.sleep(0.01)
            self.assertTrue(sendObj.test_threadGetStop)
        except:
            testAssert = False
            # clean-up
            if not threadEvent.is_set():
                threadEvent.set()
            raise
        rx.join()
        self.assertFalse(rx.running)
        self.assertTrue(testAssert)


def runtests():
    unittest.main()


if __name__ == '__main__':
    runtests()
