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
		threadMonitor.ThreadMonitor.msg_queue = Queue.Queue()

	def test_object_creation(self):
		# test that the object is created with minimal arguments
		pkt_gen = packetGenerator.PacketGenerator()
		self.assertTrue(isinstance(pkt_gen, packetGenerator.PacketGenerator))
		# test that the object is created with all arguments
		pkt_gen = packetGenerator.PacketGenerator(
			max_queue_size=10, num_rand_bytes=10000, printable_chars=True, seed='Seed String',
			name='PacketGenerator-unittest')
		self.assertTrue(isinstance(pkt_gen, packetGenerator.PacketGenerator))
		# test the msg_queue gets a message (a message is a tuple of three items)
		msg = threadMonitor.ThreadMonitor.msg_queue.get()
		self.assertTrue(isinstance(msg, tuple) and len(msg) is 3)

	def test_make_packet(self):
		pkt_gen = packetGenerator.PacketGenerator(
			max_queue_size=1, num_rand_bytes=10000, printable_chars=True, name='PacketGenerator-unittest')
		self.assertTrue(pkt_gen.queue.empty())
		packet = pkt_gen.make_packet()
		self.assertTrue(isinstance(packet, tuple))
		self.assertTrue(len(packet) is 4)
		self.assertTrue(packet[2] <= MAX_PACKET_LENGTH)
		self.assertTrue(packet[2] >= MIN_PACKET_LENGTH)

	def test_change_packet_length(self):
		pkt_gen = packetGenerator.PacketGenerator(
			max_queue_size=1, num_rand_bytes=10000, printable_chars=True, name='PacketGenerator-unittest')
		self.assertTrue(pkt_gen.queue.empty())
		try:
			pkt_gen.change_packet_length(packet_length=5)
			self.assertTrue(False)
		except BaseException:
			self.assertTrue(True)
		try:
			pkt_gen.change_packet_length(packet_length=50)
			self.assertTrue(True)
		except BaseException:
			self.assertTrue(False)
		pkt_gen.start()
		# pull packet off of Queue
		packet = pkt_gen.queue.get()
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
			pkt_gen.change_packet_length(packet_length=60)
			self.assertTrue(True)
		except BaseException:
			self.assertTrue(False)
		# pull packet off of Queue
		packet = pkt_gen.queue.get()
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
		packet = pkt_gen.queue.get()
		self.assertTrue(isinstance(packet, tuple))
		self.assertTrue(len(packet) is 4)
		self.assertTrue(len(packet[0]) is 60)
		self.assertTrue(packet[1] >= 0)
		self.assertTrue(packet[1] <= MAX_PACKET_ID)
		self.assertTrue(packet[2] is 60)
		# Stop the thread
		pkt_gen.running_lock.acquire()
		pkt_gen.running = False
		pkt_gen.running_lock.release()
		# wait for the thread to terminate
		pkt_gen.join()
		self.assertTrue(pkt_gen.queue.empty())

	def test_thread(self):
		packet_count = 0
		pkt_gen = packetGenerator.PacketGenerator(
			max_queue_size=1, num_rand_bytes=10000, printable_chars=True, name='PacketGenerator-unittest')
		self.assertTrue(pkt_gen.queue.empty())
		# specify a packet size
		try:
			pkt_gen.change_packet_length(packet_length=50)
			self.assertTrue(True)
		except BaseException:
			self.assertTrue(False)
		pkt_gen.start()
		# run the thread for 1 second
		start_time = time.time()
		while (time.time() - start_time) < 0.01:
			# pull packet off of Queue
			packet = pkt_gen.queue.get()
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
		pkt_gen.running_lock.acquire()
		pkt_gen.running = False
		pkt_gen.running_lock.release()
		# wait for the thread to terminate
		pkt_gen.join()
		self.assertTrue(pkt_gen.queue.empty())


def runtests():
	unittest.main()


if __name__ == '__main__':
	runtests()
