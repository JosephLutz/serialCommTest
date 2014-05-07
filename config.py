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

