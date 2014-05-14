# msgMonitor
import threading
import Queue

# Message are placed onto the Queue named msgQueue.
# These messages are a tiple of three items. A threadId, message data,
# and a string message.
# threadId: This gives which thread is sending the message.
#     If the thread is the main thread then the threadId is None.
# message data: Either a dictionary of key, value pairs or None for no data sent.
#     The key, value pairs will be used in formatting the message string.
#     The keys in SPECIAL_MSG_DATA_KEYS will be used else where and for the
#     formatting will be empty strings.
# string message: is eithere an int, string, or unicode. If the type is int,
#     there is a lookup dictionary in messageQueueMessages for common messages.
#     Otherwise use the string message with the message data as it's
#     format parameters.

# the queue for ordering, storing and then displaying thread messages
msgQueue = Queue.Queue()

# distionary of all threads
threadList = {}
threadListLock = threading.Lock()

def getNextThreadID(thread_obj):
	threadListLock.acquire()
	inUseIDs = set(l_threadList.keys())
	availableIDs = set(range(65535)) - inUseIDs
	if len(availableIDs) is 0:
		l_threadListLock.release()
		raise threading.ThreadError
	threadID = availableIDs.pop()
	threadList[threadID] = thread_obj
	threadListLock.release()
	return threadID



def joinAllThreads():
	threadListLock.acquire()
	for curThread in l_threadList:
		if not curThread is None:
			curThread.join()
			threadList[curThread.threadID] = None
	threadListLock.release()
'''
class MsgMonitor(threading.Thread):
	pass
'''

if __name__ == '__main__':
	import tests.msgMonitor_test
	tests.msgMonitor_test.runtests
