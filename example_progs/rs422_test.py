# rs422_test

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

PORT = '/dev/ttyACM0'

USE_TCDRAIN = True
DATA_DISPLAY_COLLS = 25
MAX_DISPLAY_DATA = 600  # display at most 600 bytes
MAX_PACKET_SIZE = 10240
TEST_TIMEOUT = 10.0
TIME_BETWEEN_TESTS = 4.0
READ_SIZE = 512
WRITE_SIZE = 512
WARMUP_TIME   = 0.001
COOLDOWN_TIME = 0.001
NUMBER_OF_LOOPS = 12

baudrates = (115200, 57600, 38400, 28800, 19200, 14400, 9600, 4800, 2400, 1200)

def get_rand_data(bytes, printableChars=True):
	rand = random.SystemRandom()
	if printableChars:
		returnVal = ''.join([chr(rand.randint(33,127)) for i in range(bytes)])
	else:
		returnVal = ''.join([chr(rand.randint(1,255)) for i in range(bytes)])
	return hashlib.sha1(returnVal).hexdigest() + returnVal

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
	ser.xonxoff = False
	ser.rtscts = False
	ser.timeout = read_timeout
	ser.writeTimeout = write_timeout
	ser.close()
	print ('Port "{port}" created'.format(port=port))
	return ser

class RxThread(threading.Thread):
	def __init__(self, name, threadID, ser):
		threading.Thread.__init__(self)
		self.running_lock = Lock()
		self.running = False
		self.threadID = threadID
		self.name = name
		self.ser = ser
		self.read_queue = Queue.Queue()
	def run(self):
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
		except:
			print ('Exception in RxThread - Stopping RX')
			try:
				self.running_lock.release()
			except:
				pass
		else:
			self.running_lock.release()
		print ('RxThread is stopping')

def write_test(rxThread, read_timeout, ser, baud, data_to_send, write_size, write_delay, warm_up, cool_down):
	try:
		if not ser.isOpen():
			ser.open()
		# set bauderate
		ser.setBaudrate(baud)
		ser.setRTS(False)
		ser.setDTR(True)
		if USE_TCDRAIN:
			iflag, oflag, cflag, lflag, ispeed, ospeed, cc = termios.tcgetattr(ser.fd)
			iflag |= (TERMIOS.IGNBRK | TERMIOS.IGNPAR)
			termios.tcsetattr(ser.fd, TERMIOS.TCSANOW, [iflag, oflag, cflag, lflag, ispeed, ospeed, cc])
	except:
		print ('Failure to change the baudrate to {0}.'.format(baud))
		raise BaseException
	# verify port is still open
	if not ser.isOpen():
		print ('Port no longer open')
		raise BaseException
	# set RTS and warm_up
	print ('Start Transmitting')
	ser.setRTS(True)
	time.sleep(warm_up)
	# start sending
	while len(data_to_send) is not 0:
		write_len = min(len(data_to_send), write_size)
		ser.write(data_to_send[:write_len])
		data_to_send = write_len[write_len:]
		time.sleep(write_delay)
	# set cool_down and RTS
	if USE_TCDRAIN:
		termios.tcdrain(ser.fd)
	time.sleep(cool_down)
	# set RTS to off
	ser.setRTS(False)
	print ('Finished Transmitting')
	# still recieving
	rxThread.running_lock.acquire()
	if not rxThread.running:
		rxThread.running_lock.release()
		print ('Recieve thread prematurly terminated')
		raise BaseException
	rxThread.running_lock.release()
	# examin and display recieved data
	read_start_time = time.time()
	read_data = ''
	while ((len(read_data) < len(data_to_send))  and ((time.time() - read_start_time) < read_timeout)):
		(packet, packet_time) = rxThread.read_queue.get()
		print ('recieved {len} bytes within {time:1.4} seconds'.format(len=len(packet), time=packet_time))
		read_data += packet
	if (len(read_data) is not len(data_to_send)):
		print ('The TX and RX data does not match - Length is different')
	if (read_data == data_to_send):
		print ('Recieved all the transmitted data !!!')
	else:
		print ('The TX and RX data does not match - different data')
		if max(len(read_data), len(data_to_send)) < MAX_DISPLAY_DATA:
			print ('\n{tx_row:<{DATA_DISPLAY_COLLS}}  {rx_row:{DATA_DISPLAY_COLLS}}'.format(tx_row='TX Data', rx_row='RX Data', DATA_DISPLAY_COLLS=DATA_DISPLAY_COLLS))
			for row_count in range((max(len(read_data), len(data_to_send)) / DATA_DISPLAY_COLLS)):
				tx_row = ''
				rx_row = ''
				row_index = row_count * DATA_DISPLAY_COLLS
				if len(data_to_send) > row_index:
					tx_row = data_to_send[row_index:(row_index + min(DATA_DISPLAY_COLLS, (len(data_to_send) - row_index)))]
				if len(read_data) > row_index:
					rx_row = read_data[row_index:(row_index + min(DATA_DISPLAY_COLLS, (len(read_data) - row_index)))]
				print ('{tx_row:<{DATA_DISPLAY_COLLS}}  {rx_row:{DATA_DISPLAY_COLLS}}'.format(tx_row=tx_row, rx_row=rx_row, DATA_DISPLAY_COLLS=DATA_DISPLAY_COLLS))
			print ('\n')
		else:
			print ('Too much data to display\n\n')

def main():
	print ('Generate {0} bytes of random data'.format(MAX_PACKET_SIZE))
	data = get_rand_data(MAX_PACKET_SIZE, printableChars=False)
	ser = setup_serial_port(PORT, 1.0, 1.0)
	rxThread = RxThread('Recieve thread', 0, ser)
	for count in range(NUMBER_OF_LOOPS):
		for packet_size in [x for x in range(1, MAX_PACKET_SIZE)]:
			for baud in baudrates:
				print ('Testing port {port} at {baud} baudrate with {packet_size} bytes of data.'.format(port=ser.port, baud=baud, packet_size=packet_size))
				write_test(rxThread=rxThread,
					read_timeout=(TEST_TIMEOUT * int(baudrates.index(baud)/4 + 1)),
					ser=ser, baud=baud, data_to_send=data[:packet_size],
					write_size=WRITE_SIZE, write_delay=0.001, warm_up=WARMUP_TIME, cool_down=COOLDOWN_TIME)
				time.sleep(TIME_BETWEEN_TESTS)
	rxThread.running_lock.acquire()
	rxThread.running = False
	rxThread.running_lock.release()
	rxThread.join()

if __name__ == '__main__':
	main()
