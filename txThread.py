# txThread
import threading
import threadMonitor

from config import *


class TxThread(threadMonitor.ThreadMonitor):
    # Thread for running writes from DataSendObj.
    # NOTE:
    #   DataSendObj.threadStartup() is run before event syncRxTxEvent.
    #   Event syncRxTxEvent will be cleared before event threadEvent blocks.
    def __init__(self, dataSendObj, threadEvent=None, *args, **kwargs):
        super(TxThread, self).__init__(*args, **kwargs)
        self.dataSendObj = dataSendObj
        self.dataSendObj.txThread = self
        # Blocks run until event is set in other thread
        self.threadEvent = threadEvent
        # Used to notify when DataSendObj.threadStartup() is completed
        if ENABLE_SYNC_RX_TX_THREADS:
            # sync RxThread and TxThread
            self.syncRxTxEvent = threading.Event()
        else:
            self.syncRxTxEvent = None
        if self.msgQueue:
            # notify 'thread created' using msgQueue
            self.msgQueue.put((self.threadID, {'thread_type': 'TX'}, THREAD_CREATED))

    def locked_running(self):
        try:
            # thread starting code
            self.dataSendObj.thread_send_startup()
            if ENABLE_SYNC_RX_TX_THREADS:
                if self.msgQueue:
                    # notify 'RX thread ready' using msgQueue
                    self.msgQueue.put((self.threadID, {'thread_type': 'TX'}, THREAD_READY))
                if not self.syncRxTxEvent.is_set():
                    self.syncRxTxEvent.set()
            # block until event is set in other thread
            if self.threadEvent:
                if self.msgQueue:
                    # notify 'threadEvent.wait' using msgQueue
                    self.msgQueue.put((self.threadID, {'thread_type': 'TX'}, THREAD_SYNC_WAIT))
                self.runLock.release()
                self.threadEvent.wait()
                self.runLock.acquire()
            if self.msgQueue:
                # notify 'thread starting' using msgQueue
                self.msgQueue.put((self.threadID, {'thread_type': 'TX'}, THREAD_STARTING))
            # anything that needs to happen just before the thread loop starts
            self.dataSendObj.thread_send_start()
            while self.running:
                self.runLock.release()
                if self.dataSendObj.send_data():
                    self.runLock.acquire()
                else:
                    # finished reading
                    self.runLock.acquire()
                    self.running = False
            self.runLock.release()
            # anything that needs to happen just after the thread loop ends
            self.dataSendObj.thread_send_stop()
            self.runLock.acquire()
            if self.msgQueue:
                # notify 'thread stopped' using msgQueue
                self.msgQueue.put((self.threadID, {'thread_type': 'TX'}, THREAD_STOPPED))
        except:
            if not self.syncRxTxEvent.is_set():
                self.syncRxTxEvent.set()
            raise


if __name__ == '__main__':
    import tests.txThread_test

    tests.txThread_test.runtests
