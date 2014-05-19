# serialData

import threading
import select
import termios
import Queue
import time
import sys
import os

from OrionPythonModules import serial_settings
import serial
import threadMonitor


if sys.hexversion < 0x020100f0:
	import TERMIOS
else:
	TERMIOS = termios

from config import *


class SerialData(serial.Serial):
	#Used by the tx_thread and rxThread as the DataSendObj and data_get_obj.
	LXM_MODE_VALUES = [
		u'RS-232', u'RS-485 2-wire',
		u'RS-485/422 4-wire', u'Loopback']
	LXM_SERIAL_TYPES = {
		u'RS232': LXM_MODE_VALUES[0],
		u'RS485': LXM_MODE_VALUES[1],
		u'RS422': LXM_MODE_VALUES[2],
		None: LXM_MODE_VALUES[3],}

	def __init__(self, port, packet_source, read_timeout=SERIAL_PORT_READ_TIMEOUT,
				 write_timeout=None, inter_char_timeout=None):
		super(SerialData, self).__init__(
			# number/name of device
			# numbering starts at zero. if everything fails, the user can specify
			# a device string, NOTE: that this isn't portable anymore.
			# The port will be opened if one is specified
			port=None,
			# baudrate
			baudrate=115200,
			# number of databits
			bytesize=serial.EIGHTBITS,
			#enable parity checking
			parity=serial.PARITY_NONE,
			#number of stopbits
			stopbits=serial.STOPBITS_ONE,
			#set a timeout value, None to wait forever
			timeout=read_timeout,
			#enable software flow control
			xonxoff=0,
			#enable RTS/CTS flow control
			rtscts=0,
			#set a timeout for writes
			writeTimeout=write_timeout,
			#None: use rtscts setting, dsrdtr override if true or false
			dsrdtr=None,
			#Inter-character timeout, None to disable
			interCharTimeout=inter_char_timeout)
		if isinstance(port, str) or isinstance(port, unicode):
			self.port = os.path.normpath(port)
		else:
			# Using an integer is not as specific (A guess is made).
			self.port = port
		# Queue for sending state back to messaging thread
		self.msg_queue = threadMonitor.ThreadMonitor.msg_queue
		# lock for when a thread needs exclusive access to the serial port
		# lock exclusive use of hardware
		self.port_lock = threading.Lock()
		# the next packet queued up to send
		self.packet_tuple = None
		# list of sent packet information
		# FORMAT: [(packetID, packetLength, hash), ...]
		self.sent_packets = []
		# place holder populated when the tx_thread is created
		self.tx_thread = None
		# data received (list of tuples, each containing data read and time since last read)
		# FORMAT: [(data, time), ...]
		self.read_buffer = []
		# place holder populated when the rxThread is created
		self.rx_thread = None
		# Queue that holds data packets to be sent
		self.packet_source = packet_source
		if self.msg_queue is not None:
			self.msg_queue.put((None, {'port': self.port}, CREATE_SERIAL_PORT))

	@staticmethod
	def set_serial_mode(mode=None):
		def mode_in(index_mode):
			if ((isinstance(index_mode, str) or isinstance(index_mode, unicode)) and
					(unicode(index_mode.upper()) in SerialData.LXM_SERIAL_TYPES.keys())):
				return SerialData.LXM_SERIAL_TYPES[index_mode]
			elif ((isinstance(index_mode, str) or isinstance(index_mode, unicode)) and
					(unicode(index_mode) in SerialData.LXM_SERIAL_TYPES.values())):
				return unicode(index_mode)
			elif (isinstance(index_mode, int) and
					(index_mode >= 0) and
					(index_mode < len(SerialData.LXM_MODE_VALUES))):
				return SerialData.LXM_MODE_VALUES[index_mode]
			else:
				return u'Loopback'

		settings = serial_settings.SerialSettings()
		settings.cards = [
			{
				'type': '124',
				'ports': [{}, {}, {}, {}, ],
			}, {
				'type': '124',
				'ports': [{}, {}, {}, {}, ],
			}]
		if isinstance(mode, tuple) and len(mode) is 8:
			for mode_index in xrange(0, 4):
				settings.cards[0]['ports'][mode_index]['type'] = mode_in(mode[mode_index])
			for mode_index in xrange(0, 4):
				settings.cards[1]['ports'][mode_index]['type'] = mode_in(mode[mode_index])
		elif isinstance(mode, str) or isinstance(mode, unicode) or isinstance(mode, int):
			mode = mode_in(mode)
			for mode_index in xrange(0, 4):
				settings.cards[0]['ports'][mode_index]['type'] = mode
			for mode_index in xrange(0, 4):
				settings.cards[1]['ports'][mode_index]['type'] = mode
		else:
			mode = 'Loopback'
			for mode_index in xrange(0, 4):
				settings.cards[0]['ports'][mode_index]['type'] = mode
			for mode_index in xrange(0, 4):
				settings.cards[1]['ports'][mode_index]['type'] = mode
		settings.apply()

	def open_serial_port(self):
		self.port_lock.acquire()
		if not self.isOpen():
			if not os.path.exists(self.port):
				if self.msg_queue is not None:
					self.msg_queue.put((self.tx_thread.thread_id, {'port': self.port}, PORT_NOT_EXIST))
				self.port_lock.release()
				return False
			try:
				self.open()
			except serial.SerialException:
				if not os.path.exists(self.port):
					if self.msg_queue is not None:
						self.msg_queue.put(
							(self.tx_thread.thread_id, {'port': self.port}, SERIALEXCEPTION_OPEN_DISAPPEAR))
				else:
					if self.msg_queue is not None:
						self.msg_queue.put(
							(self.tx_thread.thread_id, {'port': self.port}, SERIALEXCEPTION_OPEN))
				self.port_lock.release()
				return False
			if not self.isOpen():
				if self.msg_queue is not None:
					self.msg_queue.put(
						(self.tx_thread.thread_id, {'port': self.port}, PORT_NOT_OPEN))
				self.port_lock.release()
				return False
			if ENABLE_RTS_LINE:
				# NOTE: Set RTS back to False as soon as possible after open.
				#       open resets RTS True when RTS/CTS flow control disabled
				# (re)set RTS to off
				self.setRTS(False)
			if ENABLE_DTR_LINE:
				# set DTR to on
				self.setDTR(True)
			if ENABLE_TCDRAIN:
				(iflag, oflag, cflag, lflag, ispeed, ospeed, cc) = (
					termios.tcgetattr(self.fd))
				iflag |= (TERMIOS.IGNBRK | TERMIOS.IGNPAR)
				termios.tcsetattr(self.fd, TERMIOS.TCSANOW,
					[iflag, oflag, cflag, lflag, ispeed, ospeed, cc])
		if self.msg_queue is not None:
			self.msg_queue.put((self.tx_thread.thread_id, {'port': self.port}, SERIAL_PORT_OPENED))
		self.port_lock.release()
		return True

	def close_serial_port(self):
		self.port_lock.acquire()
		if self.isOpen():
			if ENABLE_RTS_LINE:
				# set RTS to off
				self.setRTS(False)
			if ENABLE_DTR_LINE:
				# set DTR to off
				self.setDTR(False)
			# close the port
			self.close()
		if self.msg_queue is not None:
			self.msg_queue.put((self.tx_thread.thread_id, {'port': self.port}, SERIAL_PORT_CLOSED))
		self.port_lock.release()

	#
	# These methods determine how the port is used
	#
	def thread_send_startup(self):
		self.sent_packets = []
		# open the port
		if not self.open_serial_port():
			raise BaseException

	def thread_send_start(self):
		try:
			if self.packet_tuple is None:
				self.packet_tuple = self.packet_source.queue.get(block=True, timeout=SERIAL_PORT_QUEUE_TIME)
		except Queue.Empty:
			return False
		if ENABLE_RTS_LINE:
			self.port_lock.acquire()
			# set RTS to on
			self.setRTS(True)
			self.port_lock.release()
			time.sleep(SERIAL_PORT_WARMUP_TIME)
		return True

	def send_data(self):
		start_time = time.time()
		# get the self.packet_tuple from the Queue.
		# First time there should already be a packet in self.packet_tuple
		try:
			if self.packet_tuple is None:
				self.packet_tuple = self.packet_source.queue.get(block=True, timeout=SERIAL_PORT_QUEUE_TIME)
		except Queue.Empty:
			return False
		# write the data
		try:
			if self.msg_queue is not None:
				self.msg_queue.put(
					(
						self.tx_thread.thread_id,
						{
							'packetID': self.packet_tuple[1],
							'time': (time.time() - start_time),
							'packetLength': self.packet_tuple[2],
						}, START_PACKET,
					))
			self.write(self.packet_tuple[0])
			if self.msg_queue is not None:
				self.msg_queue.put(
					(self.tx_thread.thread_id,
						{
							'packetID': self.packet_tuple[1],
							'time': (time.time() - start_time),
							'packetLength': self.packet_tuple[2]
						}, FINISH_PACKET,)
				)
		except serial.SerialTimeoutException:
			if self.msg_queue is not None:
				self.msg_queue.put((self.tx_thread.thread_id, {}, SERIAL_TIMEOUT))
			# This packet gets dropped
			self.packet_tuple = None
			return False
		# store tuple of packet info, everything except the data: (packetID, packetLength, hash)
		self.sent_packets.append(self.packet_tuple[1:])
		# keep track that the next time we need to get a packet from the queue
		self.packet_tuple = None
		return True

	def thread_send_stop(self):
		if self.fd > 0:
			if ENABLE_RTS_LINE:
				self.port_lock.acquire()
				if ENABLE_TCDRAIN:
					termios.tcdrain(self.fd)
				time.sleep(SERIAL_PORT_COOLDOWN_TIME)
				# set RTS to off
				self.setRTS(False)
				self.port_lock.release()
		# use the message queue to send self.sent_packets
		if self.msg_queue is not None:
			self.msg_queue.put(
				(
					self.tx_thread.thread_id,
					{SPECIAL_MSG_DATA_KEYS[SPECIAL_MSG__SENT_DATA]: self.sent_packets, },
					REPORT_SENT_DATA
				))
		# if there was a packet in self.packet_tuple it will get dropped
		# (NOTE: I think this will always be None already)
		self.packet_tuple = None

	def thread_get_startup(self):
		# reset the read_buffer
		self.read_buffer = []
		# open the port
		if not self.open_serial_port():
			raise BaseException

	def thread_get_start(self):
		pass

	def get_data(self):
		reading = True
		bytes_read = 0
		start_time = time.time()
		while reading:
			(rlist, _, _) = select.select([self.fileno()], [], [], self.timeout)
			if (len(rlist) is 1) and rlist[0] is self.fileno():
				data = self.read(NUM_BYTES_TO_READ)
				bytes_read += len(data)
				self.read_buffer.append((data, (time.time() - start_time)), )
			else:
				reading = False
		if bytes_read is 0:
			return False
		return True

	def thread_get_stop(self):
		# send the read_buffer in the message queue
		if self.msg_queue is not None:
			self.msg_queue.put(
				(
					self.tx_thread.thread_id,
					{SPECIAL_MSG_DATA_KEYS[SPECIAL_MSG__RECEIVED_DATA]: self.read_buffer,},
					REPORT_RECEIVED_DATA,
				))


if __name__ == '__main__':
	import tests.testSerialData
	tests.testSerialData.runtests()
