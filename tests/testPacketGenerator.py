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
import threadMonitor
from config import *


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
    def setUp(self):
        packetGenerator.PacketGenerator.allocated_lock.acquire()
        packetGenerator.PacketGenerator.allocated = set()
        packetGenerator.PacketGenerator.ALLOCATABLE_PACKET_ID = set(xrange(MAX_PACKET_ID))
        packetGenerator.PacketGenerator.allocated_lock.release()
        packetGenerator.PacketGenerator.allocated_lock = threading.Lock()
        threadMonitor.ThreadMonitor.threadMapLock.acquire()
        threadMonitor.ThreadMonitor.threadMap = {}
        threadMonitor.ThreadMonitor.threadMapLock.release()
        threadMonitor.ThreadMonitor.threadMapLock = threading.Lock()
        threadMonitor.ThreadMonitor.msgQueue = Queue.Queue()
    
    def test_object_creation(self):
        # test that the object is created with minimal arguments
        pktGen = packetGenerator.PacketGenerator()
        self.assertTrue(isinstance(pktGen, packetGenerator.PacketGenerator))
        pktGen = None
        # test that the object is created with all arguments
        pktGen = packetGenerator.PacketGenerator(max_queue_size=10,
            num_rand_bytes=10000, printable_chars=True, seed='Seed String',
            name='PacketGenerator-unittest')
        self.assertTrue(isinstance(pktGen, packetGenerator.PacketGenerator))
        # test the msgQueue gets a message (a message is a tupe of three items)
        msg = threadMonitor.ThreadMonitor.msgQueue.get()
        self.assertTrue(isinstance(msg, tuple) and len(msg) is 3)
    
    def test_make_packet(self):
        pktGen = packetGenerator.PacketGenerator(max_queue_size=1,
            num_rand_bytes=10000, printable_chars=True,
            name='PacketGenerator-unittest')
        self.assertTrue(pktGen.queue.empty())
        packet = pktGen.makePacket()
        self.assertTrue(isinstance(packet, tuple))
        self.assertTrue(len(packet) is 4)
        self.assertTrue(packet[2] <= MAX_PACKET_LENGTH)
        self.assertTrue(packet[2] >= MIN_PACKET_LENGTH)
    
    def test_change_packet_length(self):
        packet_count = 0
        pktGen = packetGenerator.PacketGenerator(max_queue_size=1,
            num_rand_bytes=10000, printable_chars=True,
            name='PacketGenerator-unittest')
        self.assertTrue(pktGen.queue.empty())
        try:
            pktGen.change_packet_length(packet_length=5)
            self.assertTrue(False)
        except:
            self.assertTrue(True)
        try:
            pktGen.change_packet_length(packet_length=50)
            self.assertTrue(True)
        except:
            self.assertTrue(False)
        pktGen.start()
        # pull packet off of Queue
        packet = pktGen.queue.get()
        self.assertTrue(isinstance(packet, tuple))
        self.assertTrue(len(packet) is 4)
        self.assertTrue(len(packet[0]) is 50)
        self.assertTrue(packet[1] >= 0)
        self.assertTrue(packet[1] <= MAX_PACKET_ID)
        self.assertTrue(packet[2] is 50)
        # difference between binary values and string representation using hex
        self.assertTrue(len(packet[3]) == (PACKET_GENERATOR_HASHLIB_ALGORITHM().digest_size * 2))
        # change the length
        try:
            pktGen.change_packet_length(packet_length=60)
            self.assertTrue(True)
        except:
            self.assertTrue(False)
        # pull packet off of Queue
        packet = pktGen.queue.get()
        self.assertTrue(isinstance(packet, tuple))
        self.assertTrue(len(packet) is 4)
        # length could be 50 or 60 depending what happened first, a new packet was generated,
        # or the length was change and then a new packet was generated.
        self.assertTrue((len(packet[0]) is 50) or (len(packet[0]) is 60))
        self.assertTrue(packet[1] >= 0)
        self.assertTrue(packet[1] <= MAX_PACKET_ID)
        self.assertTrue((packet[2] is 50) or (packet[2] is 60))
        # difference between binary values and string representation using hex
        self.assertTrue(len(packet[3]) == (PACKET_GENERATOR_HASHLIB_ALGORITHM().digest_size * 2))
        # pull packet off of Queue
        packet = pktGen.queue.get()
        self.assertTrue(isinstance(packet, tuple))
        self.assertTrue(len(packet) is 4)
        self.assertTrue(len(packet[0]) is 60)
        self.assertTrue(packet[1] >= 0)
        self.assertTrue(packet[1] <= MAX_PACKET_ID)
        self.assertTrue(packet[2] is 60)
        # Stop the thread
        pktGen.runLock.acquire()
        pktGen.running = False
        pktGen.runLock.release()
        # wait for the thread to terminate
        pktGen.join()
        self.assertTrue(pktGen.queue.empty())
    
    def test_thread(self):
        packet_count = 0
        pktGen = packetGenerator.PacketGenerator(max_queue_size=1,
            num_rand_bytes=10000, printable_chars=True,
            name='PacketGenerator-unittest')
        self.assertTrue(pktGen.queue.empty())
        # specify a packet size
        try:
            pktGen.change_packet_length(packet_length=50)
            self.assertTrue(True)
        except:
            self.assertTrue(False)
        pktGen.start()
        # run the thread for 1 second
        startTime = time.time()
        while (time.time() - startTime) < 0.01:
            # pull packet off of Queue
            packet = pktGen.queue.get()
            self.assertTrue(isinstance(packet, tuple))
            self.assertTrue(len(packet) is 4)
            self.assertTrue(len(packet[0]) is 50)
            self.assertTrue(packet[1] >= 0)
            self.assertTrue(packet[1] <= MAX_PACKET_ID)
            self.assertTrue(packet[2] is 50)
            # difference between binary values and string representation using hex
            self.assertTrue(len(packet[3]) == (PACKET_GENERATOR_HASHLIB_ALGORITHM().digest_size * 2))
            packet_count += 1
        # Stop the thread
        pktGen.runLock.acquire()
        pktGen.running = False
        pktGen.runLock.release()
        # wait for the thread to terminate
        pktGen.join()
        self.assertTrue(pktGen.queue.empty())


def runtests():
    unittest.main()


if __name__ == '__main__':
    runtests()
