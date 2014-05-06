# msgMonitor
import threading
import Queue

THREAD_CREATED, STARTING, STOPPED, THREAD_READY = (0,1,2,3)
THREAD_SYNC_WAIT, CREATE_SERIAL_PORT, PORT_OPENED = (4,5,6)
PORT_CLOSED, GENERATE_DATA, REPORT_DATA_RECIEVED = (7,8,9)

messageQueueMessages = {
	THREAD_CREATED:'THREAD CREATED',
	STARTING:'STARTING',
	STOPPED:'STOPPED',
	THREAD_READY:'THREAD READY',
	THREAD_SYNC_WAIT:'THREAD SYNC WAIT',
	CREATE_SERIAL_PORT:'Created serial port {port}',
	PORT_OPENED:'Serial port {port} opened',
	PORT_CLOSED:'Serial port {port} closed',
	GENERATE_DATA:'Generating {bytes} bytes of random data for packet data',
	REPORT_DATA_RECIEVED:'Data recieved'
}

# the queue for ordering, storing and then displaying the messages
msgQueue = Queue.Queue()

# distionary of all threads
l_threadList = {}
l_threadListLock = threading.Lock()

def setThread(newThread):
	def _getNextThreadID():
		inUseIDs = set(l_threadList.keys())
		availableIDs = set(range(65535)) - inUseIDs
		if len(availableIDs) is 0:
			return None
		return availableIDs.pop()
	returnVal = False
	l_threadListLock.acquire()
	if newThread.threadID is None:
		nextThreadID = _getNextThreadID()
		if nextThreadID is not None:
			newThread.threadID = nextThreadID
			returnVal = True
	elif newThread.threadID not in l_threadList:
		l_threadList[newThread.threadID] = newThread
		returnVal = True
	#else:
	#	if l_threadList[newThread.threadID] is newThread:
	#		returnVal = True
	l_threadListLock.release()
	return returnVal
'''
def joinThreads(jThread):
	if isinstance(jthread, threading.Thread):
		jThread = [jThread]
	done = (len(jThread) is 0)
	while not done:
		for curThread in jThread:
			if not curThread.is_alive():
				break
		curThread.join()
		l_threadListLock.acquire()
		l_threadList[curThread.threadID] = None
		l_threadListLock.release()
		jThread.remove(curThread)
		done = (len(jThread) is 0)
def joinAllThreads():
		l_threadListLock.acquire()
		for curThread in l_threadList:
			if not curThread is None:
				curThread.join()
				l_threadList[curThread.threadID] = None
		l_threadListLock.release()


class MsgMonitor(threading.Thread):
	pass
'''

if __name__ == '__main__':
	import tests.msgMonitor_test
	tests.msgMonitor_test.runtests
