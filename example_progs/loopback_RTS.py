# loopback_RTS.py

from OrionPythonModules import serial_settings

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

PORT = '/dev/ttyACM0'

SET_MODE_DELAY = 4.0
PORT_OPEN_DELAY = 2.0
PORT_CLOSED_DELAY = 4.0


PRINTABLE_CHARS = True
USE_TCDRAIN = True
DATA_DISPLAY_COLLS = 39

MAX_DISPLAY_DATA = 1400

MAX_PACKET_SIZE = 10240
READ_SIZE = 512
WRITE_SIZE = 512

#READ_TIMEOUT = 0.01
READ_TIMEOUT = 4.0
WRITE_TIMEOUT_BASE = 0.01
WARMUP_TIME   = 0.002
COOLDOWN_TIME = 0.002
BASE_QUEUE_READ_TIMEOUT = 30.0

TIME_BETWEEN_TESTS = 1.0
NUMBER_OF_LOOPS = 12

#baudrates = (115200, 57600, 38400, 28800, 19200, 14400, 9600, 4800, 2400, 1200)
baudrates = (1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, 115200)

LXM_MODE_VALUES = [
	u'RS-232', u'RS-485 2-wire',
	u'RS-485/422 4-wire', u'Loopback'
]
LXM_SERIAL_TYPES = {
	u'RS232': LXM_MODE_VALUES[0],
	u'RS485': LXM_MODE_VALUES[1],
	u'RS422': LXM_MODE_VALUES[2],
	None: LXM_MODE_VALUES[3],
}

def get_rand_data(bytes, printableChars=True):
    rand = random.SystemRandom()
    if printableChars:
        return ''.join([chr(rand.randint(33,126)) for i in range(bytes)])
    else:
        return ''.join([chr(rand.randint(1,255)) for i in range(bytes)])

def set_serial_mode(mode=None):
    def mode_in(mode):
        if ((isinstance(mode, str) or isinstance(mode, unicode)) and
                (unicode(mode.upper()) in LXM_SERIAL_TYPES.keys())):
            return LXM_SERIAL_TYPES[mode]
        elif ((isinstance(mode, str) or isinstance(mode, unicode)) and
              (unicode(mode) in LXM_SERIAL_TYPES.values())):
            return unicode(mode)
        elif isinstance(mode, int) and (mode >= 0) and (mode < len(LXM_MODE_VALUES)):
            return LXM_MODE_VALUES[mode]
        else:
            return u'Loopback'

    settings = serial_settings.SerialSettings()
    settings.cards = [{
        'type': '124',
        'ports': [{}, {}, {}, {}, ]
    }, {
        'type': '124',
        'ports': [{}, {}, {}, {}, ]
    }]
    if isinstance(mode, tuple) and len(mode) is 8:
        for mode_index in range(0, 4):
            settings.cards[0]['ports'][mode_index]['type'] = mode_in(mode[mode_index])
        for mode_index in range(0, 4):
            settings.cards[1]['ports'][mode_index]['type'] = mode_in(mode[mode_index])
    elif isinstance(mode, str) or isinstance(mode, unicode) or isinstance(mode, int):
        mode = mode_in(mode)
        for mode_index in range(0, 4):
            settings.cards[0]['ports'][mode_index]['type'] = mode
        for mode_index in range(0, 4):
            settings.cards[1]['ports'][mode_index]['type'] = mode
    else:
        mode = 'Loopback'
        for mode_index in range(0, 4):
            settings.cards[0]['ports'][mode_index]['type'] = mode
        for mode_index in range(0, 4):
            settings.cards[1]['ports'][mode_index]['type'] = mode
    settings.apply()

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


def open_serial_port(ser, baud):
	try:
		if ser.isOpen():
			ser.close()
		# set timeouts
		read_queue_timeout = BASE_QUEUE_READ_TIMEOUT
		ser.setWriteTimeout(None)
		# set bauderate
		ser.setBaudrate(baud)
		if not os.path.exists(ser.port):
			print ('Serial port no longer exists.')
			return False
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
		return False
	# verify port is still open
	if not ser.isOpen():
		print ('Port no longer open')
		return False
	return True

def main():
	data = get_rand_data(bytes=256, printableChars=True)
	print data
	ser = setup_serial_port(PORT, read_timeout=READ_TIMEOUT)
	while True:
		for baud in baudrates:
			for mode in [u'RS-232', u'Loopback']:
				print ("baud={0} mode={1}".format(baud, mode))
				set_serial_mode(mode)
				print '... mode set'
				time.sleep(SET_MODE_DELAY)
				if not open_serial_port(ser, baud):
					raise BaseException
				print '... port opened'
				time.sleep(PORT_OPEN_DELAY)
				# RTS on and WARMUP
				# set RTS to on
				ser.setRTS(True)
				time.sleep(WARMUP_TIME)
				# Write data
				ser.write(data)
				# read data
				d = ser.read(256)
				# COOLDOWN and RTS off
				termios.tcdrain(ser.fd)
				time.sleep(COOLDOWN_TIME)
				# set RTS to off
				ser.setRTS(False)
				# check the data
				if (data == d):
					print ("TX data == RX data", (data == d))
				else:
					print len(data)
					print len(d)
					print d
				# set RTS to off
				ser.setRTS(False)
				# set DTR to off
				ser.setDTR(False)
				# close port
				ser.close()
				print '... port closed'
				time.sleep(PORT_CLOSED_DELAY)


if __name__ == '__main__':
	main()
