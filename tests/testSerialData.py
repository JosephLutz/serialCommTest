# serialData_test

# This test requires a USART!
# This is because it is testing calls that use the serial module
# Edit the SERIAL_PORT_DEVICE variable below to match a USART.
# The USART needs to be in loopback mode.
#
# loopback mode:
#   RX, and TX connected
#   RTS, and CTS connected
#   DTR, DCD and DSR connected

SERIAL_PORT_DEVICE = '/dev/ttyUSB0'
#SERIAL_PORT_DEVICE = '/dev/serial/by-path/platform-musb-hdrc.0.auto-usb-0:1.1:1.0',

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
import serialData
# Other modules
import packetGenerator
import txThread
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


class TestSerialData(unittest.TestCase):
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

	def test_serial_device_exists(self):
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?

	def test_object_creation(self):
		pkt_gen = packetGenerator.PacketGenerator(
			max_queue_size=1, num_rand_bytes=2000, printable_chars=True, seed='Seed String',
			name='PacketGenerator-unittest')
		# test the msg_queue gets a message (a message is a tuple of three items)
		msg = threadMonitor.ThreadMonitor.msg_queue.get()
		self.assertTrue(isinstance(msg, tuple) and len(msg) is 3)
		# test simple object creation
		self.assertTrue(
			isinstance(
				serialData.SerialData(port=SERIAL_PORT_DEVICE, packet_source=pkt_gen),
				serialData.SerialData))
		# test that the object is created with all arguments
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE,
			packet_source=pkt_gen,
			read_timeout=1.0,
			write_timeout=None,
			inter_char_timeout=None)
		self.assertTrue(isinstance(ser, serialData.SerialData))
		# test the msg_queue gets a message (a message is a tuple of three items)
		msg = threadMonitor.ThreadMonitor.msg_queue.get()
		self.assertTrue(isinstance(msg, tuple) and len(msg) is 3)

	def test_set_serial_mode(self):
		pkt_gen = packetGenerator.PacketGenerator(
			max_queue_size=1, num_rand_bytes=2000, printable_chars=True, seed='Seed String',
			name='PacketGenerator-unittest')
		pkt_gen.start()
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE,
			packet_source=pkt_gen,
			read_timeout=1.0,
			write_timeout=None,
			inter_char_timeout=None)
		# test setting the serial mode for all ports to the same thing using 'RS232'
		ser.set_serial_mode('RS232')
		# test setting the serial mode for all ports to the same thing using 'RS-485 2-wire'
		ser.set_serial_mode('RS-485 2-wire')
		# test setting the serial mode for all ports to the same thing using 0
		ser.set_serial_mode(0)
		# test setting the serial mode for all ports to the same thing using u'RS232'
		ser.set_serial_mode(u'RS232')
		# test setting the serial mode for all ports using [0,0,0,0, 0,0,0,0]
		ser.set_serial_mode([0, 0, 0, 0, 0, 0, 0, 0])
		# test setting the serial mode for all ports using [0,0,0,0,] - set all to loopback, though not verifiable
		ser.set_serial_mode([0, 0, 0, 0, ])
		self.assertTrue(True)
		# shut down pkt_gen
		pkt_gen.running_lock.acquire()
		pkt_gen.running = False
		pkt_gen.running_lock.release()
		pkt_gen.join()

	def test_open_port(self):
		pkt_gen = packetGenerator.PacketGenerator(
			max_queue_size=1, num_rand_bytes=2000, printable_chars=True, seed='Seed String',
			name='PacketGenerator-unittest')
		pkt_gen.start()
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE,
			packet_source=pkt_gen,
			read_timeout=1.0,
			write_timeout=None,
			inter_char_timeout=None)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
		# create the tx_thread just for it's thread_id when sending msgs on msg_queue
		ser.tx_thread = txThread.TxThread(ser, name='TX Thread for {0}'.format(os.path.basename(ser_port)))
		#test the port is opened and configured
		ser.open_serial_port()
		self.assertTrue(ser.isOpen())
		# Close the port
		ser.close_serial_port()
		self.assertFalse(ser.isOpen())
		# shut down pkt_gen
		pkt_gen.running_lock.acquire()
		pkt_gen.running = False
		pkt_gen.running_lock.release()
		pkt_gen.join()

	def test_close_port(self):
		pkt_gen = packetGenerator.PacketGenerator(
			max_queue_size=1, num_rand_bytes=2000, printable_chars=True, seed='Seed String',
			name='PacketGenerator-unittest')
		pkt_gen.start()
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE,
			packet_source=pkt_gen,
			read_timeout=1.0,
			write_timeout=None,
			inter_char_timeout=None)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
		# create the tx_thread just for it's thread_id when sending msgs on msg_queue
		ser.tx_thread = txThread.TxThread(ser, name='TX Thread for {0}'.format(os.path.basename(ser_port)))
		#test the port is opened and configured
		ser.open_serial_port()
		self.assertTrue(ser.isOpen())
		# Close the port
		ser.close_serial_port()
		self.assertFalse(ser.isOpen())
		# shut down pkt_gen
		pkt_gen.running_lock.acquire()
		pkt_gen.running = False
		pkt_gen.running_lock.release()
		pkt_gen.join()

	def test_thread_send_startup(self):
		pkt_gen = packetGenerator.PacketGenerator(
			max_queue_size=1, num_rand_bytes=2000, printable_chars=True, seed='Seed String',
			name='PacketGenerator-unittest')
		pkt_gen.start()
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE,
			packet_source=pkt_gen,
			read_timeout=1.0,
			write_timeout=None,
			inter_char_timeout=None)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
		# create the tx_thread just for it's thread_id when sending msgs on msg_queue
		ser.tx_thread = txThread.TxThread(ser, name='TX Thread for {0}'.format(os.path.basename(ser_port)))
		#test the port is opened, configured, and threading variables are configured
		self.assertFalse(ser.isOpen())
		ser.thread_send_startup()
		self.assertTrue(ser.isOpen())
		# Close the port
		ser.close_serial_port()
		self.assertFalse(ser.isOpen())
		# shut down pkt_gen
		pkt_gen.running_lock.acquire()
		pkt_gen.running = False
		pkt_gen.running_lock.release()
		pkt_gen.join()

	def test_thread_send_start(self):
		pkt_gen = packetGenerator.PacketGenerator(
			max_queue_size=1, num_rand_bytes=2000, printable_chars=True, seed='Seed String',
			name='PacketGenerator-unittest')
		pkt_gen.start()
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE,
			packet_source=pkt_gen,
			read_timeout=1.0,
			write_timeout=None,
			inter_char_timeout=None)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
		# create the tx_thread just for it's thread_id when sending msgs on msg_queue
		ser.tx_thread = txThread.TxThread(ser, name='TX Thread for {0}'.format(os.path.basename(ser_port)))
		#test the port is opened, configured, and threading variables are configured
		self.assertFalse(ser.isOpen())
		ser.thread_send_startup()
		self.assertTrue(ser.isOpen())
		self.assertTrue(ser.packet_tuple is None)
		try:
			self.assertTrue(ser.thread_send_start())
		except BaseException:
			self.assertTrue(False)
		self.assertFalse(ser.packet_tuple is None)
		# Close the port
		self.assertTrue(ser.isOpen())
		ser.close_serial_port()
		self.assertFalse(ser.isOpen())
		# shut down pkt_gen
		pkt_gen.running_lock.acquire()
		pkt_gen.running = False
		pkt_gen.running_lock.release()
		pkt_gen.join()

	def test_thread_send_data(self):
		pkt_gen = packetGenerator.PacketGenerator(
			max_queue_size=1, num_rand_bytes=2000, printable_chars=True, seed='Seed String',
			name='PacketGenerator-unittest')
		pkt_gen.start()
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE,
			packet_source=pkt_gen,
			read_timeout=1.0,
			write_timeout=None,
			inter_char_timeout=None)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
		# create the tx_thread just for it's thread_id when sending msgs on msg_queue
		ser.tx_thread = txThread.TxThread(ser, name='TX Thread for {0}'.format(os.path.basename(ser_port)))
		#test the port is opened, configured, and threading variables are configured
		self.assertFalse(ser.isOpen())
		ser.thread_send_startup()
		self.assertTrue(ser.isOpen())
		try:
			# block pkt_gen from creating any more packets
			pkt_gen.running_lock.acquire()
			# give the pkt_gen thread time to block on the running_lock
			time.sleep(0.1 + PACKET_GENERATOR_TIMEOUT)
			self.assertTrue(ser.packet_tuple is None)
			self.assertFalse(pkt_gen.queue.empty())
			try:
				self.assertTrue(ser.thread_send_start())
			except BaseException:
				self.assertTrue(False)
			self.assertFalse(ser.packet_tuple is None)
			self.assertTrue(pkt_gen.queue.empty())
			# test sending a packet of data
			self.assertTrue(ser.send_data())
			# test sending a packet of data when no data exists in queue
			self.assertTrue(ser.packet_tuple is None)
			#self.assertTrue(pkt_gen.queue.empty())
			self.assertFalse(ser.send_data())
			# release pkt_gen
			pkt_gen.running_lock.release()
		except BaseException:
			pkt_gen.running_lock.release()
			raise
		# Close the port
		self.assertTrue(ser.isOpen())
		ser.close_serial_port()
		self.assertFalse(ser.isOpen())
		# shut down pkt_gen
		pkt_gen.running_lock.acquire()
		pkt_gen.running = False
		pkt_gen.running_lock.release()
		pkt_gen.join()

	def test_thread_send_stop(self):
		pkt_gen = packetGenerator.PacketGenerator(
			max_queue_size=1, num_rand_bytes=2000, printable_chars=True, seed='Seed String',
			name='PacketGenerator-unittest')
		pkt_gen.start()
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE,
			packet_source=pkt_gen,
			read_timeout=1.0,
			write_timeout=None,
			inter_char_timeout=None)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
		# create the tx_thread just for it's thread_id when sending msgs on msg_queue
		ser.tx_thread = txThread.TxThread(ser, name='TX Thread for {0}'.format(os.path.basename(ser_port)))
		#test the port is opened, configured, and threading variables are configured
		self.assertFalse(ser.isOpen())
		ser.thread_send_startup()
		self.assertTrue(ser.isOpen())
		self.assertTrue(ser.packet_tuple is None)
		try:
			self.assertTrue(ser.thread_send_start())
		except BaseException:
			self.assertTrue(False)
		self.assertFalse(ser.packet_tuple is None)
		try:
			ser.thread_send_stop()
		except BaseException:
			self.assertTrue(False)
		# Close the port
		self.assertTrue(ser.isOpen())
		ser.close_serial_port()
		self.assertFalse(ser.isOpen())
		# shut down pkt_gen
		pkt_gen.running_lock.acquire()
		pkt_gen.running = False
		pkt_gen.running_lock.release()
		pkt_gen.join()

	def test_thread_get_startup(self):
		pkt_gen = packetGenerator.PacketGenerator(
			max_queue_size=1, num_rand_bytes=2000, printable_chars=True, seed='Seed String',
			name='PacketGenerator-unittest')
		pkt_gen.start()
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE,
			packet_source=pkt_gen,
			read_timeout=1.0,
			write_timeout=None,
			inter_char_timeout=None)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
		# create the tx_thread just for it's thread_id when sending msgs on msg_queue
		ser.tx_thread = txThread.TxThread(ser, name='TX Thread for {0}'.format(os.path.basename(ser_port)))
		#test the port is opened, configured, and threading variables are configured
		self.assertFalse(ser.isOpen())
		ser.thread_get_startup()
		self.assertTrue(ser.isOpen())
		# Close the port
		ser.close_serial_port()
		self.assertFalse(ser.isOpen())
		# shut down pkt_gen
		pkt_gen.running_lock.acquire()
		pkt_gen.running = False
		pkt_gen.running_lock.release()
		pkt_gen.join()

	def test_thread_get_start(self):
		pkt_gen = packetGenerator.PacketGenerator(
			max_queue_size=1, num_rand_bytes=2000, printable_chars=True, seed='Seed String',
			name='PacketGenerator-unittest')
		pkt_gen.start()
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE,
			packet_source=pkt_gen,
			read_timeout=1.0,
			write_timeout=None,
			inter_char_timeout=None)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
		# create the tx_thread just for it's thread_id when sending msgs on msg_queue
		ser.tx_thread = txThread.TxThread(ser, name='TX Thread for {0}'.format(os.path.basename(ser_port)))
		#test the port is opened, configured, and threading variables are configured
		ser.thread_get_startup()
		self.assertTrue(ser.isOpen())
		try:
			ser.thread_get_start()
		except BaseException:
			self.assertTrue(False)
		# Close the port
		self.assertTrue(ser.isOpen())
		ser.close_serial_port()
		self.assertFalse(ser.isOpen())
		# shut down pkt_gen
		pkt_gen.running_lock.acquire()
		pkt_gen.running = False
		pkt_gen.running_lock.release()
		pkt_gen.join()

	def test_thread_get_data(self):
		pkt_gen = packetGenerator.PacketGenerator(
			max_queue_size=1, num_rand_bytes=2000, printable_chars=True, seed='Seed String',
			name='PacketGenerator-unittest')
		pkt_gen.start()
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE,
			packet_source=pkt_gen,
			read_timeout=1.0,
			write_timeout=None,
			inter_char_timeout=None)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
		# create the tx_thread just for it's thread_id when sending msgs on msg_queue
		ser.tx_thread = txThread.TxThread(ser, name='TX Thread for {0}'.format(os.path.basename(ser_port)))
		#test the port is opened, configured, and threading variables are configured
		ser.thread_get_startup()
		self.assertTrue(ser.isOpen())
		try:
			ser.thread_get_start()
		except BaseException:
			self.assertTrue(False)
		# test receiving a packet of data when no data was sent.
		ser.flushInput()
		self.assertFalse(ser.get_data())
		# sending a packet of data
		self.assertTrue(ser.send_data())
		# test receiving a packet of data. (since loopback should be same data as sent)
		self.assertTrue(ser.get_data())
		# Close the port
		self.assertTrue(ser.isOpen())
		ser.close_serial_port()
		self.assertFalse(ser.isOpen())
		# shut down pkt_gen
		pkt_gen.running_lock.acquire()
		pkt_gen.running = False
		pkt_gen.running_lock.release()
		pkt_gen.join()

	def test_thread_get_stop(self):
		pkt_gen = packetGenerator.PacketGenerator(
			max_queue_size=1, num_rand_bytes=2000, printable_chars=True, seed='Seed String',
			name='PacketGenerator-unittest')
		pkt_gen.start()
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE,
			packet_source=pkt_gen,
			read_timeout=1.0,
			write_timeout=None,
			inter_char_timeout=None)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
		# create the tx_thread just for it's thread_id when sending msgs on msg_queue
		ser.tx_thread = txThread.TxThread(ser, name='TX Thread for {0}'.format(os.path.basename(ser_port)))
		#test the port is opened, configured, and threading variables are configured
		self.assertFalse(ser.isOpen())
		ser.thread_get_startup()
		self.assertTrue(ser.isOpen())
		try:
			ser.thread_get_start()
		except BaseException:
			self.assertTrue(False)
		try:
			ser.thread_get_stop()
		except BaseException:
			self.assertTrue(False)
		# Close the port
		self.assertTrue(ser.isOpen())
		ser.close_serial_port()
		self.assertFalse(ser.isOpen())
		# shut down pkt_gen
		pkt_gen.running_lock.acquire()
		pkt_gen.running = False
		pkt_gen.running_lock.release()
		pkt_gen.join()


def runtests():
	unittest.main()


if __name__ == '__main__':
	runtests()
#suite = unittest.TestLoader().loadTestsFromTestCase(TestSerialData)
#unittest.TextTestRunner(verbosity=2).run(suite)
