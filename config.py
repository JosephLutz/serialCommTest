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
