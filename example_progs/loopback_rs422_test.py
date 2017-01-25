# loopback_rs422_test

import traceback
import threading
import termios
import hashlib
import random
import select
import serial
import Queue
import math
import time
import sys
import os
if (sys.hexversion < 0x020100f0):
	import TERMIOS
else:
	TERMIOS = termios

PORT = '/dev/ttyS4'

PRINTABLE_CHARS = True
USE_TCDRAIN = True
DATA_DISPLAY_COLLS = 39

MAX_DISPLAY_DATA = 1400

MAX_PACKET_SIZE = 10240
READ_SIZE = 512
WRITE_SIZE = 512

READ_TIMEOUT = 0.01
WRITE_TIMEOUT_BASE = 0.01
WARMUP_TIME   = 0.001
COOLDOWN_TIME = 0.001
BASE_QUEUE_READ_TIMEOUT = 30.0

TIME_BETWEEN_TESTS = 1.0
NUMBER_OF_LOOPS = 12

#baudrates = (115200, 57600, 38400, 28800, 19200, 14400, 9600, 4800, 2400, 1200)
baudrates = (1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, 115200)

def setup_serial_port(port, read_timeout=None, write_timeout=None):
	# create generic serial port object
	if not os.path.exists(port):
		print ('!!!!!!!!!!  Port "{port}" does not exist.  !!!!!!!!!!'.format(port=port))
		raise BaseException
	ser = serial.Serial(port=None)
	ser.port = port
	ser.baudrate = 115200
	ser.bytesize = serial.EIGHTBITS
	ser.parity = serial.PARITY_NONE
	ser.stopbits = serial.STOPBITS_ONE
	ser.timeout = read_timeout
	ser.xonxoff = False
	ser.rtscts = False
	ser.writeTimeout = write_timeout
	ser.dsrdtr = None
	ser.interCharTimeout = False    # used for enabe/disable read timeout and reading specified number of bytes
	ser.close()
	print ('Port "{port}" created'.format(port=port))
	return ser

class RxThread(threading.Thread):
	def __init__(self, name, threadID, ser):
		threading.Thread.__init__(self)
		self.running_lock = threading.Lock()
		self.running = False
		self.threadID = threadID
		self.name = name
		self.ser = ser
		self.read_queue = Queue.Queue()
	def run(self):
		try:
			if not self.ser.isOpen():
				self.ser.open()
		except serial.SerialException:
			print ('serial.SerialException : Failure to open the port for reading')
			raise BaseException
		# verify port is still open
		if not ser.isOpen():
			print ('Port no longer open')
			raise BaseException
		self.running_lock.acquire()
		self.running = True
		print ('Recieve thread started')
		# start recieving
		start_time = time.time()
		try:
			while self.running:
				self.running_lock.release()
				try:
					# read the data from the serial port
					data = self.ser.read(READ_SIZE)
					while len(data) is READ_SIZE:
						data += self.ser.read(READ_SIZE)
					if len(data) is not 0:
						self.read_queue.put((data, (time.time() - start_time)))
						start_time = time.time()
				except serial.SerialTimeoutException:
					pass
				self.running_lock.acquire()
		except serial.SerialException:
			print ('serial.SerialException in RxThread - Stopping RX')
			try:
				self.running_lock.release()
			except:
				pass
		else:
			self.running_lock.release()
		print ('RxThread is stopping')

'''
while True:
	data = ser.read(READ_SIZE)
	if len(data) is not 0:
		ser.write(data)
'''

def transmit(ser, warm_up, cool_down, data, write_size, write_delay):
	# set RTS and warm_up
	print ('Start Transmitting')
	ser.setRTS(True)
	time.sleep(warm_up)
	# start sending
	while len(data) is not 0:
		write_len = min(len(data), write_size)
		ser.write(data[:write_len])
		data = data[write_len:]
		time.sleep(write_delay)
	# set cool_down and RTS
	if USE_TCDRAIN:
		termios.tcdrain(ser.fd)
	time.sleep(cool_down)
	# set RTS to off
	ser.setRTS(False)
	print ('Finished Transmitting')

def write_test(rxThread, ser, baud, data_to_send, write_size, write_delay, warm_up, cool_down):
	try:
		if ser.isOpen():
			ser.close()
		# set timeouts
		read_queue_timeout = BASE_QUEUE_READ_TIMEOUT
		ser.setWriteTimeout(None)
		# set bauderate
		ser.setBaudrate(baud)
		# open the port again
		ser.open()
		ser.setRTS(False)
		ser.setDTR(True)
		if USE_TCDRAIN:
			iflag, oflag, cflag, lflag, ispeed, ospeed, cc = termios.tcgetattr(ser.fd)
			iflag |= (TERMIOS.IGNBRK | TERMIOS.IGNPAR)
			termios.tcsetattr(ser.fd, TERMIOS.TCSANOW, [iflag, oflag, cflag, lflag, ispeed, ospeed, cc])
		ser.flushInput()
		ser.flushOutput()
	except serial.SerialException:
		print ('serial.SerialException : Failure to change the baudrate to {0}.'.format(baud))
		raise BaseException
	# verify port is still open
	if not ser.isOpen():
		print ('Port no longer open')
		raise BaseException
	# still recieving
	rxThread.running_lock.acquire()
	if not rxThread.running:
		rxThread.running_lock.release()
		print ('Recieve thread prematurly terminated')
		raise BaseException
	rxThread.running_lock.release()
	# examin and display recieved data
	read_start_time = time.time()
	while ((time.time() - read_start_time) < read_queue_timeout):
		try:
			(packet, packet_time) = rxThread.read_queue.get(True, read_queue_timeout)
			print ('recieved {len} bytes within {time:1.4} seconds'.format(len=len(packet), time=packet_time))
			transmit(ser=ser, warm_up=warm_up, cool_down=cool_down, data=packet, write_size=write_size, write_delay=write_delay)
		except Queue.Empty:
			pass

def main():
	ser = setup_serial_port(PORT, read_timeout=READ_TIMEOUT)
	rxThread = RxThread('Recieve thread', 0, ser)
	try:
		rxThread.start()
		for count in range(NUMBER_OF_LOOPS):
			for packet_size in [x for x in range(1, MAX_PACKET_SIZE)]:
					'''for baud in baudrates:'''
					baud = baudrates[5]
					print ('Testing port {port} at {baud} baudrate with {packet_size} bytes of data.'.format(port=ser.port, baud=baud, packet_size=packet_size))
					write_test(rxThread=rxThread,
						ser=ser, baud=baud, data_to_send=None,
						write_size=WRITE_SIZE, write_delay=0.001, warm_up=WARMUP_TIME, cool_down=COOLDOWN_TIME)
					time.sleep(TIME_BETWEEN_TESTS)
	except:
		rxThread.running = False
		print ('\n\n::::: caught exception :::::\n' + getExceptionInfo())
		try:
			rxThread.running_lock.release()
		except:
			pass
	else:
		rxThread.running_lock.acquire()
		rxThread.running = False
		rxThread.running_lock.release()
	finally:
		rxThread.join()

def getExceptionInfo():
	exc_type, exc_obj, exc_tb = sys.exc_info()
	fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
	if (exc_type is None or exc_obj is None or exc_tb is None):
		return 'No Exception Encountered'
	error_out = 'Exception Encountered'
	error_out += '{0}\n'.format('='*80)
	error_out += 'lineno:{lineno}, fname:{fname}'.format(fname=fname, lineno=exc_tb.tb_lineno)
	for line in traceback.format_tb(exc_tb):
		error_out += '{0}\n'.format(line)
	return ('\n{line:80}\n{out}\n{line:80}'.format(line='#'*80, out=error_out))

if __name__ == '__main__':
	main()
