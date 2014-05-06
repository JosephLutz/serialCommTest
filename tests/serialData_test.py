# serialData_test
'''
This test requires a USART!
This is because it is testing calls that use the serial module
Edit the SERIAL_PORT_DEVICE variable below to match a USART.
The USART needs to be in loopback mode.

loopback mode:
  RX, and TX connected
  RTS, and CTS connected
  DTR, DCD and DSR connected
'''
SERIAL_PORT_DEVICE = '/dev/ttyUSB0'
#SERIAL_PORT_DEVICE = '/dev/serial/by-path/platform-musb-hdrc.0.auto-usb-0:1.1:1.0',



import traceback
import unittest
import Queue
import os

if __name__ == '__main__':
	import os, sys
	importDirectory = os.getcwd()
	if os.path.basename(importDirectory) in ['tests']:
		importDirectory = os.path.dirname(importDirectory)
	sys.path = [importDirectory] + sys.path

# Module to test
import serialData
# Other modules
import packetGenerator
import rxThread
import txThread

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

class TestSerialData(unittest.TestCase):
	def setUp(self):
		pass
	def test_serialDeviceExists(self):
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))	# Serial unit testing hardware device exists?
	def test_ObjectCreation(self):
		msgQueue = Queue.Queue()
		pktGen = packetGenerator.PacketGenerator('unitTest', 1, msgQueue, 20, True, 'Seed String')
		# test the msgQueue gets a message (a message is a tupe of three items)
		msg = msgQueue.get()
		# test simple object creation
		self.assertTrue(isinstance(serialData.SerialData(port=SERIAL_PORT_DEVICE, packetSource=None), serialData.SerialData))
		# test that the object is created with all arguments
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE, 
			packetSource=pktGen, 
			msgQueue=msgQueue,
			readTimeout=1.0,
			writeTimeout=None,
			interCharTimeout=None)
		self.assertTrue(isinstance(ser, serialData.SerialData))
		# test the msgQueue gets a message (a message is a tupe of three items)
		msg = msgQueue.get()
		self.assertTrue(isinstance(msg, tuple) and len(msg) is 3)
	def test_set_serial_mode(self):
		self.assertTrue(serialData.SERIAL_SETTINGS)
		msgQueue = Queue.Queue()
		pktGen = packetGenerator.PacketGenerator('unitTest', 1, msgQueue, 20, True, 'Seed String')
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE, 
			packetSource=pktGen, 
			msgQueue=msgQueue,
			readTimeout=1.0,
			writeTimeout=None,
			interCharTimeout=None)
		# test setting the serial mode for all ports to the same thing using 'RS232'
		ser.set_serial_mode('RS232')
		# test setting the serial mode for all ports to the same thing using 'RS-485 2-wire'
		ser.set_serial_mode('RS-485 2-wire')
		# test setting the serial mode for all ports to the same thing using 0
		ser.set_serial_mode(0)
		# test setting the serial mode for all ports to the same thing using u'RS232'
		ser.set_serial_mode(u'RS232')
		# test setting the serial mode for all ports using [0,0,0,0, 0,0,0,0]
		ser.set_serial_mode([0,0,0,0, 0,0,0,0])
		# test setting the serial mode for all ports using [0,0,0,0,] - set all to loopback, though not verifiable
		ser.set_serial_mode([0,0,0,0,])

	def test_OpenPort(self):
		msgQueue = Queue.Queue()
		pktGen = packetGenerator.PacketGenerator('unitTest', 1, msgQueue, 20, True, 'Seed String')
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE, 
			packetSource=pktGen, 
			msgQueue=msgQueue,
			readTimeout=1.0,
			writeTimeout=None,
			interCharTimeout=None)
		ser.txThread = txThread.TxThread('TX Thread', ser)
		ser.rxThread = rxThread.RxThread('RX Thread', ser)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))	# Serial unit testing hardware device exists?
		#test the port is opened and configured
		ser.openSerialPort()
		self.assertTrue(ser.isOpen())
		# Close the port
		ser.closeSerialPort()
		self.assertFalse(ser.isOpen())
	def test_ClosePort(self):
		msgQueue = Queue.Queue()
		pktGen = packetGenerator.PacketGenerator('unitTest', 1, msgQueue, 20, True, 'Seed String')
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE, 
			packetSource=pktGen, 
			msgQueue=msgQueue,
			readTimeout=1.0,
			writeTimeout=None,
			interCharTimeout=None)
		ser.txThread = txThread.TxThread('TX Thread', ser)
		ser.rxThread = rxThread.RxThread('RX Thread', ser)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))	# Serial unit testing hardware device exists?
		#test the port is opened and configured
		ser.openSerialPort()
		self.assertTrue(ser.isOpen())
		# Close the port
		ser.closeSerialPort()
		self.assertFalse(ser.isOpen())
	def test_threadSendStartup(self):
		msgQueue = Queue.Queue()
		pktGen = packetGenerator.PacketGenerator('unitTest', 1, msgQueue, 20, True, 'Seed String')
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE, 
			packetSource=pktGen, 
			msgQueue=msgQueue,
			readTimeout=1.0,
			writeTimeout=None,
			interCharTimeout=None)
		ser.txThread = txThread.TxThread('TX Thread', ser)
		ser.rxThread = rxThread.RxThread('RX Thread', ser)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))	# Serial unit testing hardware device exists?
		#test the port is opened, configured, and threading variables are configured
		self.assertFalse(ser.isOpen())
		ser.threadSendStartup()
		self.assertTrue(ser.isOpen())
		# Close the port
		ser.closeSerialPort()
		self.assertFalse(ser.isOpen())
	def test_threadSendStart(self):
		msgQueue = Queue.Queue()
		pktGen = packetGenerator.PacketGenerator('unitTest', 1, msgQueue, 20, True, 'Seed String')
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE, 
			packetSource=pktGen, 
			msgQueue=msgQueue,
			readTimeout=1.0,
			writeTimeout=None,
			interCharTimeout=None)
		ser.txThread = txThread.TxThread('TX Thread', ser)
		ser.rxThread = rxThread.RxThread('RX Thread', ser)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))	# Serial unit testing hardware device exists?
		#test the port is opened, configured, and threading variables are configured
		self.assertFalse(ser.isOpen())
		ser.threadSendStartup()
		self.assertTrue(ser.isOpen())
		try:
			ser.threadSendStart()
		except:
			assertTrue(False)
		# Close the port
		self.assertTrue(ser.isOpen())
		ser.closeSerialPort()
		self.assertFalse(ser.isOpen())
	def test_threadSendData(self):
		msgQueue = Queue.Queue()
		pktGen = packetGenerator.PacketGenerator('unitTest', 1, msgQueue, 20, True, 'Seed String')
		pktGen.makePackets(1)
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE, 
			packetSource=pktGen, 
			msgQueue=msgQueue,
			readTimeout=1.0,
			writeTimeout=None,
			interCharTimeout=None)
		ser.txThread = txThread.TxThread('TX Thread', ser)
		ser.rxThread = rxThread.RxThread('RX Thread', ser)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))	# Serial unit testing hardware device exists?
		#test the port is opened, configured, and threading variables are configured
		self.assertFalse(ser.isOpen())
		ser.threadSendStartup()
		self.assertTrue(ser.isOpen())
		try:
			ser.threadSendStart()
		except:
			assertTrue(False)
		# test sending a packet of data
		self.assertTrue(ser.sendData())
		# test sending a packet of data when no data exists in queue
		self.assertFalse(ser.sendData())
		# Close the port
		self.assertTrue(ser.isOpen())
		ser.closeSerialPort()
		self.assertFalse(ser.isOpen())
	def test_threadSendStop(self):
		msgQueue = Queue.Queue()
		pktGen = packetGenerator.PacketGenerator('unitTest', 1, msgQueue, 20, True, 'Seed String')
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE, 
			packetSource=pktGen, 
			msgQueue=msgQueue,
			readTimeout=1.0,
			writeTimeout=None,
			interCharTimeout=None)
		ser.txThread = txThread.TxThread('TX Thread', ser)
		ser.rxThread = rxThread.RxThread('RX Thread', ser)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))	# Serial unit testing hardware device exists?
		#test the port is opened, configured, and threading variables are configured
		self.assertFalse(ser.isOpen())
		ser.threadSendStartup()
		self.assertTrue(ser.isOpen())
		try:
			ser.threadSendStart()
		except:
			assertTrue(False)
		try:
			ser.threadSendStop()
		except:
			assertTrue(False)
		# Close the port
		self.assertTrue(ser.isOpen())
		ser.closeSerialPort()
		self.assertFalse(ser.isOpen())

	def test_threadGetStartup(self):
		msgQueue = Queue.Queue()
		pktGen = packetGenerator.PacketGenerator('unitTest', 1, msgQueue, 20, True, 'Seed String')
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE, 
			packetSource=pktGen, 
			msgQueue=msgQueue,
			readTimeout=1.0,
			writeTimeout=None,
			interCharTimeout=None)
		ser.txThread = txThread.TxThread('TX Thread', ser)
		ser.rxThread = rxThread.RxThread('RX Thread', ser)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))	# Serial unit testing hardware device exists?
		#test the port is opened, configured, and threading variables are configured
		self.assertFalse(ser.isOpen())
		ser.threadGetStartup()
		self.assertTrue(ser.isOpen())
		# Close the port
		ser.closeSerialPort()
		self.assertFalse(ser.isOpen())
	def test_threadGetStart(self):
		msgQueue = Queue.Queue()
		pktGen = packetGenerator.PacketGenerator('unitTest', 1, msgQueue, 20, True, 'Seed String')
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE, 
			packetSource=pktGen, 
			msgQueue=msgQueue,
			readTimeout=1.0,
			writeTimeout=None,
			interCharTimeout=None)
		ser.txThread = txThread.TxThread('TX Thread', ser)
		ser.rxThread = rxThread.RxThread('RX Thread', ser)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))	# Serial unit testing hardware device exists?
		#test the port is opened, configured, and threading variables are configured
		ser.threadGetStartup()
		self.assertTrue(ser.isOpen())
		try:
			ser.threadGetStart()
		except:
			assertTrue(False)
		# Close the port
		self.assertTrue(ser.isOpen())
		ser.closeSerialPort()
		self.assertFalse(ser.isOpen())
	def test_threadGetData(self):
		msgQueue = Queue.Queue()
		pktGen = packetGenerator.PacketGenerator('unitTest', 1, msgQueue, 20, True, 'Seed String')
		pktGen.makePackets(1)
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE, 
			packetSource=pktGen, 
			msgQueue=msgQueue,
			readTimeout=1.0,
			writeTimeout=None,
			interCharTimeout=None)
		ser.txThread = txThread.TxThread('TX Thread', ser)
		ser.rxThread = rxThread.RxThread('RX Thread', ser)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))	# Serial unit testing hardware device exists?
		#test the port is opened, configured, and threading variables are configured
		ser.threadGetStartup()
		self.assertTrue(ser.isOpen())
		try:
			ser.threadGetStart()
		except:
			assertTrue(False)
		# test recieving a packet of data when none is in the queue sent.
		ser.flushInput()
		self.assertFalse(ser.getData())
		# test sending a packet of data
		self.assertTrue(ser.sendData())
		# test recieving a packet of data. (since loopback should be same data as sent)
		self.assertTrue(ser.getData())
		# Close the port
		self.assertTrue(ser.isOpen())
		ser.closeSerialPort()
		self.assertFalse(ser.isOpen())
	def test_threadGetStop(self):
		msgQueue = Queue.Queue()
		pktGen = packetGenerator.PacketGenerator('unitTest', 1, msgQueue, 20, True, 'Seed String')
		ser = serialData.SerialData(
			port=SERIAL_PORT_DEVICE, 
			packetSource=pktGen, 
			msgQueue=msgQueue,
			readTimeout=1.0,
			writeTimeout=None,
			interCharTimeout=None)
		ser.txThread = txThread.TxThread('TX Thread', ser)
		ser.rxThread = rxThread.RxThread('RX Thread', ser)
		# verify the port exists
		ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
		self.assertTrue(os.path.exists(ser_port))	# Serial unit testing hardware device exists?
		#test the port is opened, configured, and threading variables are configured
		self.assertFalse(ser.isOpen())
		ser.threadGetStartup()
		self.assertTrue(ser.isOpen())
		try:
			ser.threadGetStart()
		except:
			assertTrue(False)
		try:
			ser.threadGetStop()
		except:
			assertTrue(False)
		# Close the port
		self.assertTrue(ser.isOpen())
		ser.closeSerialPort()
		self.assertFalse(ser.isOpen())

def runtests():
	unittest.main()
if __name__ == '__main__':
	runtests()
