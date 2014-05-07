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
import unittest
import Queue
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
import rxThread
import txThread


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
    def test_serial_device_exists(self):
        ser_port = os.path.normpath(SERIAL_PORT_DEVICE)
        self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?

    def test_object_creation(self):
        msgQueue = Queue.Queue()
        pktGen = packetGenerator.PacketGenerator('unitTest', 1, msgQueue, 20, True, 'Seed String')
        # test the msgQueue gets a message (a message is a tupe of three items)
        msg = msgQueue.get()
        self.assertTrue(isinstance(msg, tuple) and len(msg) is 3)
        # test simple object creation
        self.assertTrue(
            isinstance(serialData.SerialData(port=SERIAL_PORT_DEVICE, packetSource=None), serialData.SerialData))
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
        ser.set_serial_mode([0, 0, 0, 0, 0, 0, 0, 0])
        # test setting the serial mode for all ports using [0,0,0,0,] - set all to loopback, though not verifiable
        ser.set_serial_mode([0, 0, 0, 0, ])
        self.assertTrue(True)

    def test_open_port(self):
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
        self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
        #test the port is opened and configured
        ser.open_serial_port()
        self.assertTrue(ser.isOpen())
        # Close the port
        ser.close_serial_port()
        self.assertFalse(ser.isOpen())

    def test_close_port(self):
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
        self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
        #test the port is opened and configured
        ser.open_serial_port()
        self.assertTrue(ser.isOpen())
        # Close the port
        ser.close_serial_port()
        self.assertFalse(ser.isOpen())

    def test_thread_send_startup(self):
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
        self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
        #test the port is opened, configured, and threading variables are configured
        self.assertFalse(ser.isOpen())
        ser.thread_send_startup()
        self.assertTrue(ser.isOpen())
        # Close the port
        ser.close_serial_port()
        self.assertFalse(ser.isOpen())

    def test_thread_send_start(self):
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
        self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
        #test the port is opened, configured, and threading variables are configured
        self.assertFalse(ser.isOpen())
        ser.thread_send_startup()
        self.assertTrue(ser.isOpen())
        try:
            ser.thread_send_start()
        except:
            self.assertTrue(False)
        # Close the port
        self.assertTrue(ser.isOpen())
        ser.close_serial_port()
        self.assertFalse(ser.isOpen())

    def test_thread_send_data(self):
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
        self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
        #test the port is opened, configured, and threading variables are configured
        self.assertFalse(ser.isOpen())
        ser.thread_send_startup()
        self.assertTrue(ser.isOpen())
        try:
            ser.thread_send_start()
        except:
            self.assertTrue(False)
        # test sending a packet of data
        self.assertTrue(ser.send_data())
        # test sending a packet of data when no data exists in queue
        self.assertFalse(ser.send_data())
        # Close the port
        self.assertTrue(ser.isOpen())
        ser.close_serial_port()
        self.assertFalse(ser.isOpen())

    def test_thread_send_stop(self):
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
        self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
        #test the port is opened, configured, and threading variables are configured
        self.assertFalse(ser.isOpen())
        ser.thread_send_startup()
        self.assertTrue(ser.isOpen())
        try:
            ser.thread_send_start()
        except:
            self.assertTrue(False)
        try:
            ser.thread_send_stop()
        except:
            self.assertTrue(False)
        # Close the port
        self.assertTrue(ser.isOpen())
        ser.close_serial_port()
        self.assertFalse(ser.isOpen())

    def test_thread_get_startup(self):
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
        self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
        #test the port is opened, configured, and threading variables are configured
        self.assertFalse(ser.isOpen())
        ser.thread_get_startup()
        self.assertTrue(ser.isOpen())
        # Close the port
        ser.close_serial_port()
        self.assertFalse(ser.isOpen())

    def test_thread_get_start(self):
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
        self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
        #test the port is opened, configured, and threading variables are configured
        ser.thread_get_startup()
        self.assertTrue(ser.isOpen())
        try:
            ser.thread_get_start()
        except:
            self.assertTrue(False)
        # Close the port
        self.assertTrue(ser.isOpen())
        ser.close_serial_port()
        self.assertFalse(ser.isOpen())

    def test_thread_get_data(self):
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
        self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
        #test the port is opened, configured, and threading variables are configured
        ser.thread_get_startup()
        self.assertTrue(ser.isOpen())
        try:
            ser.thread_get_start()
        except:
            self.assertTrue(False)
        # test receiving a packet of data when none is in the queue sent.
        ser.flushInput()
        self.assertFalse(ser.get_data())
        # test sending a packet of data
        self.assertTrue(ser.send_data())
        # test receiving a packet of data. (since loopback should be same data as sent)
        self.assertTrue(ser.get_data())
        # Close the port
        self.assertTrue(ser.isOpen())
        ser.close_serial_port()
        self.assertFalse(ser.isOpen())

    def test_thread_get_stop(self):
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
        self.assertTrue(os.path.exists(ser_port))  # Serial unit testing hardware device exists?
        #test the port is opened, configured, and threading variables are configured
        self.assertFalse(ser.isOpen())
        ser.thread_get_startup()
        self.assertTrue(ser.isOpen())
        try:
            ser.thread_get_start()
        except:
            self.assertTrue(False)
        try:
            ser.thread_get_stop()
        except:
            self.assertTrue(False)
        # Close the port
        self.assertTrue(ser.isOpen())
        ser.close_serial_port()
        self.assertFalse(ser.isOpen())


def runtests():
    unittest.main()


if __name__ == '__main__':
    runtests()
