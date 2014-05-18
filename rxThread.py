# TxThread
import threading
import threadMonitor

from config import *


class RxThread(threadMonitor.ThreadMonitor):
    # Thread for running reads from dataGetObj.
    # NOTE:
    #   dataGetObj.threadStartup() is run before event syncRxTxEvent.
    #   Event syncRxTxEvent will be cleared before event threadEvent blocks.
    def __init__(self, dataGetObj, threadEvent=None, *args, **kwargs):
        super(RxThread, self).__init__(*args, **kwargs)
        self.dataGetObj = dataGetObj
        self.dataGetObj.rxThread = self
        # Blocks run until event is set in other thread
        self.threadEvent = threadEvent
        # Used to notify when dataGetObj.threadStartup() is completed
        if ENABLE_SYNC_RX_TX_THREADS:
            # sync RxThread and TxThread
            self.syncRxTxEvent = threading.Event()
        else:
            self.syncRxTxEvent = None
        if self.msgQueue:
            # notify 'thread created' using msgQueue
            self.msgQueue.put((self.threadID, {'thread_type': 'RX'}, THREAD_CREATED))

    def locked_running(self):
        try:
            # thread starting code
            self.dataGetObj.thread_get_startup()
            if ENABLE_SYNC_RX_TX_THREADS:
                if self.msgQueue:
                    # notify 'RX thread ready' using msgQueue
                    self.msgQueue.put((self.threadID, {'thread_type': 'RX'}, THREAD_READY))
                if not self.syncRxTxEvent.is_set():
                    self.syncRxTxEvent.set()
            # block until event is set in other thread
            if self.threadEvent:
                if self.msgQueue:
                    # notify 'threadEvent.wait' using msgQueue
                    self.msgQueue.put((self.threadID, {'thread_type': 'RX'}, THREAD_SYNC_WAIT))
                self.runLock.release()
                self.threadEvent.wait()
                self.runLock.acquire()
            if self.msgQueue:
                # notify 'thread starting' using msgQueue
                self.msgQueue.put((self.threadID, {'thread_type': 'RX'}, THREAD_STARTING))
            # anything that needs to happen just before the thread loop starts
            self.dataGetObj.thread_get_start()
            while self.running:
                self.runLock.release()
                if self.dataGetObj.get_data():
                    self.runLock.acquire()
                else:
                    # finished reading
                    self.runLock.acquire()
                    self.running = False
            self.runLock.release()
            # anything that needs to happen just after the thread loop ends
            self.dataGetObj.thread_get_stop()
            self.runLock.acquire()
            if self.msgQueue:
                # notify 'thread stopped' using msgQueue
                self.msgQueue.put((self.threadID, {'thread_type': 'RX'}, THREAD_STOPPED))
        except:
            if not self.syncRxTxEvent.is_set():
                self.syncRxTxEvent.set()
            raise


if __name__ == '__main__':
    import tests.rxThread_test

    tests.rxThread_test.runtests
