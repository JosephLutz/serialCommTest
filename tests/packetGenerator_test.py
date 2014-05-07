# packetGenerator_test
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
import packetGenerator


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


class TestPacketGenerator(unittest.TestCase):
    def test_object_creation(self):
        msgQueue = Queue.Queue()
        # test that the object is created with minimal arguments
        pktGen = packetGenerator.PacketGenerator('unitTest', 1)
        self.assertTrue(isinstance(pktGen, packetGenerator.PacketGenerator))
        pktGen = None
        # test that the object is created with all arguments
        pktGen = packetGenerator.PacketGenerator('unitTest', 1, msgQueue, 2, True, 'Seed String')
        self.assertTrue(isinstance(pktGen, packetGenerator.PacketGenerator))
        # test the msgQueue gets a message (a message is a tupe of three items)
        msg = msgQueue.get()
        self.assertTrue(isinstance(msg, tuple) and len(msg) is 3)

    def test_make_packets(self):
        pktGen = packetGenerator.PacketGenerator('unitTest', 1, numBytes=2)
        self.assertTrue(pktGen.queue.empty())
        pktGen.makePackets(1)
        self.assertFalse(pktGen.queue.empty())
        packet = pktGen.queue.get()
        self.assertTrue(isinstance(packet, tuple) and len(packet) is 4)
        self.assertTrue(pktGen.queue.empty())

    def test_thread(self):
        testAssert = True
        pktGen = packetGenerator.PacketGenerator('unitTest', 1, numBytes=2)
        try:
            pktGen.start()
            self.assertTrue(pktGen.queue.empty())
            # tell thread to create some packets
            pktGen.runLock.acquire()
            pktGen.number = 1
            pktGen.runLock.release()
            # give time to create first packets
            time.sleep(2.0)
            startTime = time.time()
            # run the thread for 3 seconds
            while (time.time() - startTime) < 3.0:
                pktGen.runLock.acquire()  # lock around calls that need to be atomic
                self.assertFalse(pktGen.queue.empty())
                queueSize = pktGen.queue.qsize()
                pktGen.runLock.release()
                # pull packet off of Queue
                pktGen.runLock.acquire()  # lock around calls that need to be atomic
                pktGen.queue.get()
                newQueueSize = pktGen.queue.qsize()
                self.assertTrue((newQueueSize + 1) is queueSize)
                pktGen.packetUsed.set()
                pktGen.runLock.release()
                # wait some time for the new packet to be generated
                time.sleep(0.3)
                pktGen.runLock.acquire()  # lock around calls that need to be atomic
                newQueueSize = pktGen.queue.qsize()
                self.assertTrue(newQueueSize is queueSize)
                pktGen.runLock.release()
            # Stop the thread
            pktGen.runLock.acquire()
            pktGen.running = False
            pktGen.runLock.release()
        except:
            print '\n' + get_exception_info()
            testAssert = False
            # clean up the thread
            if not pktGen.packetUsed.is_set():
                pktGen.packetUsed.set()
            pktGen.running = False
            try:
                pktGen.runLock.release()
            except threading.ThreadError:
                pass
        pktGen.join()
        self.assertTrue(pktGen.queue.empty())
        self.assertTrue(testAssert)


def runtests():
    unittest.main()


if __name__ == '__main__':
    runtests()
