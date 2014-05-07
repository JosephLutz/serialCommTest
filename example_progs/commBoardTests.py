#!/usr/bin/env python
from traceback import format_tb
import threading
from threading import Lock
import termios
import hashlib
import random
import select
import serial
import Queue
import time
import sys
import os

if (sys.hexversion < 0x020100f0):
	import TERMIOS
else:
	TERMIOS = termios

if (sys.hexversion < 0x020200f0):
	import FCNTL
else:
	import fcntl
	FCNTL = fcntl

TEST_TIMEOUT = 10
NUM_TIMES_PER_BAUD = 1
TEST_BREAK_TIME = 12.0

# ammount of time to allow the serial module to read as many bytes as requested: non-blocking reads
RX_BUFFER_FILL_TIME = 0.02
READ_SIZE = 512

WARMUP_TIME   = 0.001
COOLDOWN_TIME =1.0

baudrates = (115200, 57600, 38400, 28800, 19200, 14400, 9600, 4800, 2400, 1200)


def get_state(ser_ports, msg_queue):
	out = ''
	print_msg_queue(msg_queue)
	try:
		out += 'event: TX={txEvent}\n'.format(txEvent=ser_ports[0].TX_thread.TX_event.is_set())
	except:
		out += 'event: TX=[NONE]\n'
	for ser in ser_ports:
		try:
			port = ser.port
		except:
			port = '[NONE]'
		try:
			opened = ser.isOpen()
		except:
			opened = '[NONE]'
		try:
			alive = ser.TX_thread.is_alive()
		except:
			alive = '[NONE]'
		try:
			txEvent = ser.TX_thread.TX_event.is_set()
		except:
			txEvent = '[NONE]'
		try:
			open_event = ser.TX_thread.port_open_event.is_set()
		except:
			open_event = '[NONE]'
		try:
			self.running_lock.acquire()
			running = ser.TX_thread.running
			self.running_lock.release()
		except:
			running = '[NONE]'
		out += '    port({port:<12}) opened:{opened:<6}     Thread:(alive={alive:<6} TX_event={txEvent:<6} open_event={open_event:<6} running={running:<6})\n'.format(
			port=port, opened=opened, alive=alive, txEvent=txEvent, open_event=open_event, running=running)
	return out

def get_rand_data(bytes, printableChars=True):
	rand = random.SystemRandom()
	if printableChars:
		returnVal = ''.join([chr(rand.randint(33,126)) for i in range(bytes)])
	else:
		returnVal = ''.join([chr(rand.randint(1,255)) for i in range(bytes)])
	return hashlib.sha1(returnVal).hexdigest() + returnVal

def print_msg_queue(msg_queue):
	while not msg_queue.empty():
		(threadID, thread_name, msg) = msg_queue.get_nowait()
		if threadID is None:
			print msg
		else:
			print '{0:<4} {1:<25}          {2}'.format(threadID, ('"'+thread_name+'"'), msg)

def setup_serial_port(port, msg_queue, read_timeout=RX_BUFFER_FILL_TIME, write_timeout=None):
	# create generic serial port object
	if not os.path.exists( port ):
		msg_queue.put((None, None, ('!!!!!!!!!!  Port "{port}" does not exist.  !!!!!!!!!!'.format(port=port))))
		raise BaseException
	ser = serial.Serial(port=None)
	ser.port = port
	ser.baudrate = 115200
	ser.bytesize = serial.EIGHTBITS
	ser.parity = serial.PARITY_NONE
	ser.stopbits = serial.STOPBITS_ONE
	ser.xonxoff = False
	ser.rtscts = False
	ser.timeout = read_timeout
	ser.writeTimeout = write_timeout
	ser.close()
	print 'Generate data for {port}'.format(port=ser.port)
	ser.data = get_rand_data(10240, printableChars=False)
	ser.read_buffer = []	# ['', 0.0]
	ser.port_lock = Lock()     # lock exclusive use of hardware
	msg_queue.put((None, None, ('Port "{port}" created'.format(port=port))))
	return ser

def wait_ports_opened(ser_ports):
	# wait for all serial ports to be opened
	events = []
	for ser in ser_ports:
		if not ser.TX_thread.port_open_event.is_set():
			events.append(ser.TX_thread.port_open_event)
	start_time = time.time()
	while (len(events) is not 0):
		if not ser.TX_thread.msg_queue.empty():
			print_msg_queue(ser.TX_thread.msg_queue)
		# wait 100 mSec before checking agan
		events[0].wait(0.1)
		events = [port_event for port_event in events if not port_event.is_set()]
		if ((time.time() - start_time) > TEST_TIMEOUT):
			ser_thread.msg_queue.put((ser_thread.threadID, ser_thread.name,
				('!!!!!!!!!!  Timmed out waiting for serial ports to open.  !!!!!!!!!!')))
			ser_threads = [ser.TX_thread for ser in ser_ports if not ser.TX_thread.port_open_event.is_set()]
			ser_thread.msg_queue.put((None, None,
				('ports that did not open:'.format('"' + '", "'.join([ser_threads.name]) + '"'))))
			raise BaseException

'''
def check_recieved_data(data, ser_thread):
	shaHash = hashlib.sha1()
	digestLen = shaHash.digest_size * 2
	digest = ''
	for index in range(len(data)):
		for data_index in range(len(data[index][0])):
			digest += data[index][0][data_index]
			if len(digest) is digestLen:
				break
		if len(digest) is digestLen:
			break
	if len(digest) < digestLen:
		self.msg_queue.put((ser_thread.threadID, ser_thread.name,
			'Did not even recieve the checksum'))
		return False
	shaHash.update(data[index][0][(data_index + 1):])
	for index in range(index + 1, len(data)):
		shaHash.update(data[index][0])
	return digest == shaHash.hexdigest()
'''


def _open_serial_port(ser_thread):
	ser_thread.ser.port_lock.acquire()
	if not ser_thread.ser.isOpen():
		try:
			ser_thread.ser.open()
		except serial.SerialException:
			ser_thread.msg_queue.put((ser_thread.threadID, ser_thread.name,
				('!!!!!!!!!!  serial exception when opening port {port}.  !!!!!!!!!!'.format(port=ser_thread.ser.port))))
			if not os.path.exists(ser_thread.ser.port):
				ser_thread.msg_queue.put((ser_thread.threadID, ser_thread.name,
					('!!!!!!!!!!  serial port no longer exists {port}.  !!!!!!!!!!'.format(port=ser_thread.ser.port))))
			ser_thread.ser.port_lock.release()
			raise BaseException
		if not ser_thread.ser.isOpen():
			ser_thread.msg_queue.put((ser_thread.threadID, ser_thread.name,
				('!!!!!!!!!!  Port "{port}" is not open.  !!!!!!!!!!'.format(port=ser_thread.ser.port))))
			ser_thread.ser.port_lock.release()
			raise BaseException
		# DEBUG: Disabling tcdrain
		#iflag, oflag, cflag, lflag, ispeed, ospeed, cc = termios.tcgetattr(ser_thread.ser.fd)
		#iflag |= (TERMIOS.IGNBRK | TERMIOS.IGNPAR)
		#termios.tcsetattr(ser_thread.ser.fd, TERMIOS.TCSANOW, [iflag, oflag, cflag, lflag, ispeed, ospeed, cc])
		ser_thread.ser.setRTS(0)
	ser_thread.ser.port_lock.release()
'''
class rxThread(threading.Thread):
	def __init__(self, name, threadID, msg_queue, timeout):
		threading.Thread.__init__(self)
		self.running_lock = Lock()
		self.port_open_event = threading.Event()	# Blocks untill the port is opened
		self.running = False
		self.threadID = threadID
		self.name = name
		self.msg_queue = msg_queue
		self.timeout = timeout
		self.msg_queue.put((self.threadID, self.name, 'RX THREAD CREATED'))
		# sync RX and TX
		self.event = threading.Event()
	def run(self):
		self.running_lock.acquire()
		self.running = True
		_open_serial_port(self)
		# notify this port is opened
		if not self.port_open_event.is_set():
			self.port_open_event.set()
		self.msg_queue.put((self.threadID, self.name, 'RX STARTING'))
		# start recieving
		try:
			while self.running:
				self.running_lock.release()
				data = self._read_data()
				if len(data) is 0:
					self.running_lock.acquire()
					# no new characters recieved within self.timeout period
					self.running = False
				else:
					self.ser.read_buffer += data
					self.running_lock.acquire()
		except serial.SerialTimeoutException:
			pass
		else:
			self.running_lock.release()
	def _read_data(self):
		# Wait untill no data has been recieved for a period of time not less than self.timeout.
		# Return all data read.
		# The value of self.timeout should be less than self.timeout for this to work properly
		start_time = time.time()
		read_buffer = []
		data = ''
		while data is not None:
			(rlist, _, _) = select.select([self.ser.fileno()], [], [], self.timeout)
			if (len(rlist) is 1) and rlist[0] is self.ser.fileno():
				data = self.ser.read(READ_SIZE)
				read_buffer.append((data, (time.time() - start_time)),)
			else:
				data = None
		return read_buffer
'''
class txThread (threading.Thread):
	def __init__(self, name, threadID, msg_queue, TX_event):
		threading.Thread.__init__(self)
		self.running_lock = Lock()
		self.port_open_event = threading.Event()	# Blocks untill the port is opened
		self.TX_event = TX_event	# Releases all the TX threads at the same time (when they are all opened)
		self.running = False
		self.threadID = threadID
		self.name = name
		self.msg_queue = msg_queue
		self.msg_queue.put((self.threadID, self.name, 'TX THREAD CREATED'))
	def run(self):
		self.running_lock.acquire()
		self.running = True
		_open_serial_port(self)
		self.msg_queue.put((self.threadID, self.name, 'TX WAITING'))
		# notify this port is opened
		if not self.port_open_event.is_set():
			self.port_open_event.set()
		# wait for ALL serial ports to be opened
		self.TX_event.wait()
		self.msg_queue.put((self.threadID, self.name, 'TX STARTING'))
		# start transmit
		self.ser.port_lock.acquire()
		self.ser.setRTS(1)
		self.ser.port_lock.release()
		time.sleep(WARMUP_TIME)
		try:
			while self.running:
				self.running_lock.release()
				self.work_funct(self.ser)
				self.running_lock.acquire()
		except serial.SerialTimeoutException:
			pass
		else:
			self.running_lock.release()
		# stop transmit
		self.ser.port_lock.acquire()
		if (self.ser.fd > 0):
			#termios.tcdrain(self.ser.fd)		# DEBUG: Disabling tcdrain
			time.sleep(COOLDOWN_TIME)
			self.ser.setRTS(0)
		if self.ser.isOpen():
			self.ser.close()
		self.ser.port_lock.release()
		self.msg_queue.put((self.threadID, self.name, 'TX STOPPING'))




def write_work_function(ser):
	start_time = time.time()
	try:
		ser.write(ser.data)
		ser.close()
		ser.TX_thread.msg_queue.put((ser.TX_thread.threadID, ser.TX_thread.name,
			('--  {time:<6.4} sec.                                            ({port:<12} @ {baud:<6}).'.format(
				time=(time.time() - start_time), baud=ser.baudrate, port=ser.port))))
	except serial.SerialTimeoutException:
		if self.ser.isOpen():
			ser.close()
		ser.TX_thread.msg_queue.put((ser.TX_thread.threadID, ser.TX_thread.name,
			('--  {time:<6.4} sec.    +++++  SerialTimeoutException  +++++    ({port:<12} @ {baud:<6})'.format(
				time=(time.time() - start_time), baud=ser.baudrate, port=ser.port))))

def test1(funct, ser_ports, msg_queue):
	msg_queue.put((None, None, '\n\n{line:{fill}40}\n{fill}{msg:^38}{fill}\n{line:{fill}40}\n'.format(line='', fill='*', msg='SETUP FOR TEST')))
	# Create the threads
	id_count = 1
	TX_event = threading.Event()
	for ser in ser_ports:
		# TX Thread
		ser.TX_thread = txThread(
			'{port}_TX@{baud}'.format(port=os.path.basename(ser.port), baud=ser.baudrate),
			id_count, msg_queue, TX_event)
		ser.TX_thread.ser = ser    # Need to acces the serial port inside the thread
		ser.TX_thread.work_funct = funct
		# RX Thread
		'''
		ser.RX_thread = rxThread(
			'{port}_RX@{baud}'.format(port=os.path.basename(ser.port), baud=ser.baudrate),
			(id_count + 1), msg_queue, (TEST_TIMEOUT / 2))
		ser.RX_thread.ser = ser    # Need to acces the serial port inside the thread
		'''
		id_count += 2
	# start the threads runnung
	running_txThreads = []
	for ser in ser_ports:
		'''ser.RX_thread.start()'''
		ser.TX_thread.start()
		running_txThreads.append(ser.TX_thread.name)
	num_running_txThreads = len(running_txThreads) + 1
	# wait for all serial ports to be opened
	wait_ports_opened(ser_ports)
	# releas all transmit threads to start sending
	if not TX_event.is_set():
		TX_event.set()
	msg_queue.put((None, None, '\n\n{line:{fill}40}\n{fill}{msg:^38}{fill}\n{line:{fill}40}\n'.format(line='', fill='*', msg='START TEST')))
	# loop while the threads run
	start_time = time.time()
	while (len(running_txThreads) is not 0):
		running_txThreads = []
		# display what is in the message queue
		print_msg_queue(msg_queue)
		# have the threads been running long enough
		if ((time.time() - start_time) >= TEST_TIMEOUT):
			# Stop all threads from running due to timeout
			for ser in ser_ports:
				ser.TX_thread.running_lock.acquire()
				ser.TX_thread.running = False
				ser.TX_thread.running_lock.release()
		# collect which threads are running
		for ser in ser_ports:
			ser.TX_thread.running_lock.acquire()
			if ser.TX_thread.running:
				running_txThreads.append('{padding}"{name}"'.format(padding=('.'*10), name=ser.TX_thread.name))
			ser.TX_thread.running_lock.release()
		if (len(running_txThreads) is not num_running_txThreads):
			num_running_txThreads = len(running_txThreads)
			# creat the message to display which threads are running
			if len(running_txThreads) is 0:
				msg = '  *****  No threads left running.  *****'
			else:
				msg = 'Running threads:\n' + '\n'.join(running_txThreads)
			# queue up the message
			msg_queue.put((None, None, ('\n{msg}'.format(line=('-'*30), msg=msg))))
	msg_queue.put((None, None, '  *****  Wait for all TX threads to terminate.  *****'))
	# display what is in the message queue
	print_msg_queue(msg_queue)
	# wait for all threads to finish
	non_terminated_len = len([ser.TX_thread for ser in ser_ports if ser.TX_thread.is_alive()] + [None])
	while non_terminated_len is not 0:
		print_msg_queue(msg_queue)
		non_terminated = [ser.TX_thread for ser in ser_ports if ser.TX_thread.is_alive()]
		if len(non_terminated) is not non_terminated_len:
			non_terminated_len = len(non_terminated)
			msg_queue.put((None, None, get_state(ser_ports, msg_queue)))
	for ser in ser_ports:
		ser.TX_thread.join()
	'''
	msg_queue.put((None, None, 'Time of TX threads: {time:<6.4} sec.'.format(time=(time.time() - start_time))))
	msg_queue.put((None, None, '  *****  Wait for all RX threads to terminate.  *****'))
	# display what is in the message queue
	print_msg_queue(msg_queue)
	# wait for all threads to finish
	for ser in ser_ports:
		ser.RX_thread.join()
	'''
	msg_queue.put((None, None, 'All threads stopped. Total test time: {time:<6.4} sec.'.format(time=(time.time() - start_time))))
	msg_queue.put((None, None, '\n\n{line:{fill}40}\n{fill}{msg:^38}{fill}\n{line:{fill}40}\n'.format(line='', fill='*', msg='STOP TEST')))
	msg_queue.put((None, None, '\nSleep: {time:<6.4} sec.\n'.format(time=TEST_BREAK_TIME)))
	print_msg_queue(msg_queue)
	time.sleep(TEST_BREAK_TIME)




def main():
	msg_queue = Queue.Queue()
	ser_ports = (
		setup_serial_port('/dev/ttyACM0', msg_queue),
		setup_serial_port('/dev/ttyACM1', msg_queue),
		setup_serial_port('/dev/ttyACM2', msg_queue),
		setup_serial_port('/dev/ttyACM3', msg_queue),
		setup_serial_port('/dev/ttyACM4', msg_queue),
		setup_serial_port('/dev/ttyACM5', msg_queue),
		setup_serial_port('/dev/ttyACM6', msg_queue),
		setup_serial_port('/dev/ttyACM7', msg_queue),
	)
	# choose which baudrates to test at
	selected_baudrates = baudrates
	# run the test NUM_TIMES_PER_BAUD times at the
	# baud rate or forever if NUM_TIMES_PER_BAUD is 0
	count = NUM_TIMES_PER_BAUD
	try:
		while ((count is not 0) or (NUM_TIMES_PER_BAUD is 0)):
			# run the test for each baudrate
			for baud in selected_baudrates:
				msg_queue.put((None, None, '\n\n{line:{fill}40}\n{fill}{msg:^38}{fill}\n{line:{fill}40}\n'.format(line='', fill='*', baud='BAUDRATE = {0}'.format(baud))))
								# set the baud rate for each serial port
				for ser in ser_ports:
					ser.baudrate = baud
					test1(write_work_function, ser_ports, msg_queue)
				msg_queue.put((None, None, '\n\n'))
			msg_queue.put((None, None, '{line:40*}\n\n\n'.format(line='')))
			if (NUM_TIMES_PER_BAUD is not 0):
				count -= 1
	except:
		error_out = get_state(ser_ports, msg_queue)
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		error_out += '{0}\n'.format('='*80)
		error_out += 'lineno:{lineno}, fname:{fname}'.format(fname=fname, lineno=exc_tb.tb_lineno)
		#for line in format_tb(exc_tb):
		#	error_out += '{0}\n'.format(line)
		print('\n{line:{fill}80}\n{out}\n{line:{fill}80}'.format(line='', fill='#', out=error_out))
		
		for ser in ser_ports:
			# ignore locking
			ser.TX_thread.running = False
			if not ser.TX_thread.port_open_event.is_set():
				ser.TX_thread.port_open_event.set()
			if not ser.TX_thread.TX_event.is_set():
				ser.TX_thread.TX_event.set()



if __name__ == "__main__":
	main()
