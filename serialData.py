# serialData

from OrionPythonModules import serial_settings
from msgMonitor import CREATE_SERIAL_PORT
from msgMonitor import PORT_OPENED
from msgMonitor import PORT_CLOSED
from msgMonitor import REPORT_DATA_RECIEVED
import threading
import serial
import select
import termios
import Queue
import time
import sys
import os

if sys.hexversion < 0x020100f0:
    import TERMIOS
else:
    TERMIOS = termios

from config import *


class SerialData(serial.Serial):
    #Used by the txThread and rxThread as the DataSendObj and dataGetObj.
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

    def __init__(self, port, packetSource, msgQueue=None, readTimeout=SERIAL_PORT_READ_TIMEOUT, writeTimeout=None,
                 interCharTimeout=None):
        serial.Serial.__init__(self,
                 port = None,                       #number of device, numbering starts at
                                                    #zero. if everything fails, the user
                                                    #can specify a device string, note
                                                    #that this isn't portable anymore
                                                    #port will be opened if one is specified
                 baudrate=115200,                   #baudrate
                 bytesize=serial.EIGHTBITS,         #number of databits
                 parity=serial.PARITY_NONE,         #enable parity checking
                 stopbits=serial.STOPBITS_ONE,      #number of stopbits
                 timeout=readTimeout,               #set a timeout value, None to wait forever
                 xonxoff=0,                         #enable software flow control
                 rtscts=0,                          #enable RTS/CTS flow control
                 writeTimeout=writeTimeout,         #set a timeout for writes
                 dsrdtr=None,                       #None: use rtscts setting, dsrdtr override if true or false
                 interCharTimeout=interCharTimeout  #Inter-character timeout, None to disable
                 )
        if isinstance(port, str) or isinstance(port, unicode):
            self.port = os.path.normpath(port)
        else:
            # Using an intiger is not as reliable (A guess is made).
            self.port = port
        # Queue for sending state back to messaging thread
        self.msgQueue = msgQueue
        # lock for when a thread needs exclusive access to the serial port
        self.portLock = threading.Lock()     # lock exclusive use of hardware
        # list of sent packet information
        self.sentPackets = []   #[(packetID, packetLength, hash), ...]
        # place holder populated when the txThread is created
        self.txThread = None
        # data recieved (list of tuples, each containing data read and time since last read)
        self.readBuffer = []    # [(data, time), ...]
        # place holder populated when the rxThread is created
        self.rxThread = None
        # Queue that holds data packets to be sent
        self.packetSource = packetSource
        if self.msgQueue is not None:
            self.msgQueue.put((None, {'port': self.port}, CREATE_SERIAL_PORT))

    def set_serial_mode(self, mode=None):
        def mode_in(mode):
            if ((isinstance(mode, str) or isinstance(mode, unicode)) and
                    (unicode(mode.upper()) in SerialData.LXM_SERIAL_TYPES.keys())):
                return SerialData.LXM_SERIAL_TYPES[mode]
            elif ((isinstance(mode, str) or isinstance(mode, unicode)) and
                  (unicode(mode) in SerialData.LXM_SERIAL_TYPES.values())):
                return unicode(mode)
            elif isinstance(mode, int) and (mode >= 0) and (mode < len(SerialData.LXM_MODE_VALUES)):
                return SerialData.LXM_MODE_VALUES[mode]
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

    def open_serial_port(self):
        self.portLock.acquire()
        if not self.isOpen():
            if not os.path.exists(self.port):
                if self.msgQueue is not None:
                    self.msgQueue.put((self.txThread.threadID, None,
                                       'Serial port {port} does not exist.'.format(port=self.port)))
                self.portLock.release()
                return False
            try:
                self.open()
            except serial.SerialException:
                if not os.path.exists(self.port):
                    if self.msgQueue is not None:
                        self.msgQueue.put(
                            (self.txThread.threadID, None,
                             ('SerialException while opening port {port}, ' +
                              'and the port dissapeared after open atempt.'.format(port=self.port))))
                else:
                    if self.msgQueue is not None:
                        self.msgQueue.put(
                            (self.txThread.threadID, None,
                             'SerialException while opening port {port}.'.format(port=self.port)))
                self.portLock.release()
                return False
            if not self.isOpen():
                if self.msgQueue is not None:
                    self.msgQueue.put(
                        (self.txThread.threadID, None,
                         'Serial port {port} would not open with specified port configuration.'.format(port=self.port)))
                self.portLock.release()
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
                iflag, oflag, cflag, lflag, ispeed, ospeed, cc = termios.tcgetattr(self.fd)
                iflag |= (TERMIOS.IGNBRK | TERMIOS.IGNPAR)
                termios.tcsetattr(self.fd, TERMIOS.TCSANOW, [iflag, oflag, cflag, lflag, ispeed, ospeed, cc])
        if self.msgQueue is not None:
            self.msgQueue.put((self.txThread.threadID, {'port': self.port}, PORT_OPENED))
        self.portLock.release()
        return True

    def close_serial_port(self):
        self.portLock.acquire()
        if self.isOpen():
            if ENABLE_RTS_LINE:
                # set RTS to off
                self.setRTS(False)
            if ENABLE_DTR_LINE:
                # set DTR to off
                self.setDTR(False)
            # close the port
            self.close()
        if self.msgQueue is not None:
            self.msgQueue.put((self.txThread.threadID, {'port': self.port}, PORT_CLOSED))
        self.portLock.release()

    #
    # These methods determine how the port is used
    #
    def thread_send_startup(self):
        self.sentPackets = []
        # opent the port
        if not self.open_serial_port():
            raise BaseException

    def thread_send_start(self):
        if ENABLE_RTS_LINE:
            self.portLock.acquire()
            # set RTS to on
            self.setRTS(True)
            self.portLock.release()
            time.sleep(SERIAL_PORT_WARMUP_TIME)

    def send_data(self):
        start_time = time.time()
        if self.packetSource.queue.empty():
            return False
        # get the dataTuple from the Queue
        dataTuple = None
        try:
            while dataTuple is None:
                dataTuple = self.packetSource.queue.get_nowait()
        except Queue.Empty:
            return False
        # notify we are using a packet
        self.packetSource.packetUsed.set()
        # write the data
        try:
            if self.msgQueue is not None:
                self.msgQueue.put(
                    (self.txThread.threadID, None,
                     'Started  TX on {packetLength} byte packet {packetID} @ {time}'.format(
                         packetID=dataTuple[1], time=(time.time() - start_time), packetLength=dataTuple[2])))
            self.write(dataTuple[0])
            if self.msgQueue is not None:
                self.msgQueue.put(self.txThread.threadID, None,
                    'Finished TX on {packetLength} byte packet {packetID} @ {time}'.format(
                        packetID=dataTuple[1], time=(time.time() - start_time), packetLength=dataTuple[2]))
        except serial.SerialTimeoutException:
            if self.msgQueue is not None:
                self.msgQueue.put(self.txThread.threadID, None, 'SerialException durring packet write')
            return False
        # store tuple of packet info: (packetID, packetLength, hash)
        self.sentPackets.append(dataTuple[1:])
        return True

    def thread_send_stop(self):
        if (self.fd > 0):
            if ENABLE_RTS_LINE:
                self.portLock.acquire()
                if ENABLE_TCDRAIN:
                    termios.tcdrain(self.fd)
                time.sleep(SERIAL_PORT_COOLDOWN_TIME)
                # set RTS to off
                self.setRTS(False)
                self.portLock.release()
        # use the message queue to send self.sentPackets
        if self.msgQueue is not None:
            self.msgQueue.put((self.txThread.threadID, self.sentPackets, REPORT_DATA_RECIEVED))

    def thread_get_startup(self):
        # reset the readBuffer
        self.readBuffer = []
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
                self.readBuffer.append((data, (time.time() - start_time)),)
            else:
                reading = False
        if bytes_read is 0:
            return False
        return True

    def thread_get_stop(self):
        # send the readBuffer in the message queue
        if self.msgQueue is not None:
            self.msgQueue.put((self.txThread.threadID, self.readBuffer, 'Data read before timeout.'))


if __name__ == '__main__':
    import tests.serialData_test

    tests.serialData_test.runtests
