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


def get_exception_info():
    """
    Gathers information about a caught exception.
    This is used when I cause other exceptions in an except clause

    :rtype : string
    """
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    if exc_type is None or exc_obj is None or exc_tb is None:
        return 'No Exception Encountered'
    error_out = 'Exception Encountered'
    error_out += '{0}\n'.format('=' * 80)
    error_out += 'lineno:{lineno}, fname:{fname}'.format(fname=fname, lineno=exc_tb.tb_lineno)
    for line in traceback.format_tb(exc_tb):
        error_out += '{0}\n'.format(line)
    return '\n{line:80}\n{out}\n{line:80}'.format(line='#' * 80, out=error_out)


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
    def test_object_creation(self):
        sendObj = DataSendObj()
        msgQueue = Queue.Queue()
        threadEvent = threading.Event()
        # test that the object is created with minimal arguments
        rx = rxThread.RxThread('unitTest', sendObj)
        self.assertTrue(isinstance(rx, rxThread.RxThread))
        rx = None
        # test that the object is created with all arguments
        rx = rxThread.RxThread('unitTest', sendObj, 1, msgQueue, threadEvent)
        self.assertTrue(isinstance(rx, rxThread.RxThread))
        # test the msgQueue gets a message (a message is a tupe of three items)
        msg = msgQueue.get()
        self.assertTrue(isinstance(msg, tuple) and len(msg) is 3)

    def test_thread(self):
        testAssert = True
        sendObj = DataSendObj()
        msgQueue = Queue.Queue()
        threadEvent = threading.Event()
        rx = rxThread.RxThread('unitTest', sendObj, 1, msgQueue, threadEvent)
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
            while (time.time() - startTime) < 1.5:
                self.assertTrue(sendObj.test_getData)
            sendObj.dataSendObjLock.acquire()
            sendObj.loop = False
            sendObj.dataSendObjLock.release()
            time.sleep(0.01)
            self.assertTrue(sendObj.test_threadGetStop)
        except:
            print '\n' + get_exception_info()
            testAssert = False
            # clean up the thread
            if not rx.syncRxTxEvent.is_set():
                rx.syncRxTxEvent.set()
            if not threadEvent.is_set():
                threadEvent.set()
            rx.running = False
            try:
                rx.runLock.release()
            except threading.ThreadError:
                pass
        rx.join()
        self.assertFalse(rx.running)
        self.assertTrue(testAssert)


def runtests():
    unittest.main()


if __name__ == '__main__':
    runtests()
