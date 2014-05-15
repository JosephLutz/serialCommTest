import hashlib

#
# Config values for packetGenerator class
#

# Initial number of packets in the queue
INITIAL_PACKET_NUMBER = 0

# Wait time before checking the thread is still running
PACKET_GENERATOR_WAIT_TIMEOUT = 1.0

# The size of the packets to generate.
#  random lengths (within constraints) if set to None
PACKET_SIZE = None

#algorithm used to generate the hash
PACKET_GENERATOR_HASHLIB_ALGORITHM = hashlib.sha256

#Total number of random bytes generated
RAND_DATA_SIZE = 10240

#Minimum length of the data in the packet
MIN_PACKET_DATA_LENGTH = 10

#Length of the largest packet
MAX_PACKET_LENGTH = 65535

#Largest packet number
# TODO: need to make the packetID rollover when it reaches this number
MAX_PACKET_ID = 1024


#
# RxThread and TxThread config values
#

ENABLE_SYNC_RX_TX_THREADS = True


#
# serialData config values
#

#Time for read to return when no character is received within this timeframe
SERIAL_PORT_READ_TIMEOUT = 0.02

#number of characters to read at a time
NUM_BYTES_TO_READ = 512

#use tcdrain to determine when the last character was transmitted
ENABLE_TCDRAIN = True

#Use the RTS line, SERIAL_PORT_WARMUP_TIME, and SERIAL_PORT_COOLDOWN_TIME
ENABLE_RTS_LINE = True

#Use the DTR line
ENABLE_DTR_LINE = True

#Time from setting RTS to sending the first character
SERIAL_PORT_WARMUP_TIME = 0.001

#Time from last character sent to clearing RTS
SERIAL_PORT_COOLDOWN_TIME =1.0



#
# threadMonitor configuration
#

START_THREAD_ID = 1
# MAX_THREAD_ID = 65535
MAX_THREAD_ID = 65



#
# msgMonitor configuration
#


#
# msgMonitor values
#

# Special keys used to transfer other data (in msgQueue), than string
# formatting arguments.
SPECIAL_MSG_DATA_KEYS = (
	# list of sent packets
	#     [(packetID, packetLength, hash), ...]
	'SENT_DATA',
	# data recieved (list of tuples, each containing data read and time since last read)
	#     [(data, time), ...]
	'RECIEVED_DATA',
)
# descriptive index number to SPECIAL_MSG_DATA_KEYS
SPECIAL_MSG__SENT_DATA, SPECIAL_MSG__RECIEVED_DATA = (0, 1)


# common thread messages. Use messageQueueMessages with these keys to refrence
# the common message.
(
	THREAD_CREATED,
	THREAD_READY,
	THREAD_SYNC_WAIT,
	THREAD_STARTING,
	THREAD_STOPPED,
	GENERATE_DATA,
	CREATE_SERIAL_PORT,
	SERIAL_PORT_OPENED,
	SERIAL_PORT_CLOSED,
	PORT_NOT_EXIST,
	SERIALEXCEPTION_OPEN_DISAPEAR,
	SERIALEXCEPTION_OPEN,
	PORT_NOT_OPEN,
	START_PACKET,
	FINISH_PACKET,
	SERIAL_TIMEOUT,
	REPORT_SENT_DATA,
	REPORT_RECIEVED_DATA,
) = range(18)
# message Queue text for the messages
messageQueueMessages = {
	# rxThread and txThread
	THREAD_CREATED: u'{thread_type} THREAD CREATED',
	THREAD_READY: u'{thread_type} THREAD READY',
	THREAD_SYNC_WAIT: u'{thread_type} THREAD SYNC WAIT',
	THREAD_STARTING: u'{thread_type} THREAD STARTING',
	THREAD_STOPPED: u'{thread_type} THREAD STOPPED',
	# packetGenerator
	GENERATE_DATA: u'Generating {bytes} bytes of random data for packet data',
	#serialData
	CREATE_SERIAL_PORT: u'Created serial port {port}',
	SERIAL_PORT_OPENED: u'Serial port {port} opened',
	SERIAL_PORT_CLOSED: u'Serial port {port} closed',
	PORT_NOT_EXIST: u'Serial port {port} does not exist.',
	SERIALEXCEPTION_OPEN_DISAPEAR: u'SerialException while opening port {port}, and the port dissapeared after open atempt.',
	SERIALEXCEPTION_OPEN: u'SerialException while opening port {port}.',
	PORT_NOT_OPEN: u'Serial port {port} would not open with specified port configuration.',
	START_PACKET: u'Started TX on {packetLength} byte packet {packetID} @ {time}',
	FINISH_PACKET: u'Finished TX on {packetLength} byte packet {packetID} @ {time}',
	SERIAL_TIMEOUT: u'SerialTimeoutException durring packet write',
	REPORT_SENT_DATA: u'Data recieved',
	REPORT_RECIEVED_DATA: u'Data read before timeout.',
}
