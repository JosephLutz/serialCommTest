import threading
import traceback
import unittest
import Queue
import time

import rxThread
import serialData
import packetGenerator

BYTES = 10240
PORTS = [
	'/dev/serial/by-path/platform-musb-hdrc.0.auto-usb-0:1.1:1.0',
	'/dev/serial/by-path/platform-musb-hdrc.0.auto-usb-0:1.1:1.2',
	'/dev/serial/by-path/platform-musb-hdrc.0.auto-usb-0:1.1:1.4',
	'/dev/serial/by-path/platform-musb-hdrc.0.auto-usb-0:1.1:1.6',
	'/dev/serial/by-path/platform-musb-hdrc.0.auto-usb-0:1.2:1.0',
	'/dev/serial/by-path/platform-musb-hdrc.0.auto-usb-0:1.2:1.2',
	'/dev/serial/by-path/platform-musb-hdrc.0.auto-usb-0:1.2:1.4',
	'/dev/serial/by-path/platform-musb-hdrc.0.auto-usb-0:1.2:1.6',
]

allRunning = True

def try_run_threads(port_threads):
	global allRunning	# NOTE: Not needed here
	# catch any exception that may occure durring execution
	try:
		ports_not_released = port_threads[:]
		# start each port thread running
		for (threadEvent, rx, tx) in port_threads:
			tx.start()
			rx.start()
		# wait for rx and tx to both dataGetObj.threadGetStartup() (open serial port) and then to sync
		while len(ports_not_released) is not 0:
			release = []
			# Allow context switch
			time.sleep(0.0)
			# loop through each port_threads and check if it can be released
			for port_threads in ports_not_released:
				(threadEvent, rx, tx) = port_threads
				if rx.syncRxTxEvent.is_set() and tx.syncRxTxEvent.is_set():
					# release both threads to run
					threadEvent.set()
					release.append(port_threads)
			# remove the released thread from ports_not_released
			for port_threads in release:
				ports_not_released.pop(port_threads)
		
		# loop while threads are running
		startTime = time.time()
		while allRunning:
			time.sleep(0.5)
	except:
		# EXCEPTION OCCURED - clean up all threads and get them to stop
		print '\n' + getExceptionInfo()
		# clean up port threads
		for (threadEvent, rx, tx) in port_threads:
			# clean up the RxThread, TxThread, and threadEvent
			if not rx.syncRxTxEvent.is_set():
				rx.syncRxTxEvent.set()
			if not tx.syncRxTxEvent.is_set():
				tx.syncRxTxEvent.set()
			if not threadEvent.is_set():
				threadEvent.set()
			tx.running = False
			tx.running = False
			try:
				# may cause aditional error if lock is held
				# and in particular place in code flow
				rx.runLock.release()
			except:
				pass
			try:
				# may cause aditional error if lock is held
				# and in particular place in code flow
				tx.runLock.release()
			except:
				pass
	else:
		# STOP ALL THREADS GRACEFULLY
		for (threadEvent, rx, tx) in port_threads:
			# TxThread
			tx.runLock.acquire()
			tx.running = False
			tx.runLock.release()
			# RxThread
			rx.runLock.acquire()
			rx.running = False
			rx.runLock.release()
		raise
	finally:
		# JOIN all threads started in run_threads(port_threads)
		thread_list = []
		for (threadEvent, rx, tx) in port_threads:
			thread_list += [rx, tx]
		while len(thread_list):
			for index in range(len(thread_list)):
				if not thread_list[index].is_alive():
					print '\nThread {name} has terminated'.format(name=thread_list[index].threadName)
					thread_list[index].join()
					thread_list.pop(index)
					# start from the beginning again
					break
			print '\r{num} threads still running', ' '*6,
		print ''

def create_serial_port_threads(port, threadId, pktGenThread, msgQueue):
	ser = serialData.SerialData(
	        port=port, 
	        packetSource=pktGenThread, 
	        msgQueue=msgQueue,
	        readTimeout=0.1,
	        writeTimeout=None,
	        interCharTimeout=None)
	tx_threadId = threadId
	rx_threadId = threadId + 1
	threadEvent = threading.Event()
	rx = rxThread.RxThread('RX {port}'.format(port=sendObj.port),
		rx_threadId, ser, msgQueue, threadEvent)
	tx = txThread.TxThread('TX {port}'.format(port=sendObj.port),
		tx_threadId, ser, msgQueue, threadEvent)
	return (threadEvent, rx, tx)

def main():
	threadId = 1
	msgQueue = Queue.Queue()
	pktGenThread = packetGenerator.PacketGenerator('PacketGenerator',
		threadID=threadId, msgQueue=msgQueue, numBytes=BYTES,
		printableChars=False)
	try:
		pktGenThread.start()
		# create threads for each RX and TX port thread
		port_threads = []
		threadId += 1
		for port in PORTS:
			# notify packet generating thread there is more packets that need to be made
			pktGenThread.acquire()
			pktGenThread.number += 2
			pktGenThread.packetUsed.set()
			pktGenThread.release()
			# Create the threads and events for the port
			port_threads.append(create_serial_port_threads(port, threadId, pktGenThread, msgQueue))
			threadId += 2	# RX and TX threads
		# run the threads
		try_run_threads(pktGenThread, port_threads)
	except:
		# EXCEPTION OCCURED - clean up all threads and get them to stop
		print '\n' + getExceptionInfo()
		# clean up pktGenThread
		if not pktGenThread.packetUsed.is_set():
			pktGenThread.packetUsed.set()
		pktGenThread.running = False
		try:
			# may cause aditional error if lock is held
			# and in particular place in code flow
			pktGenThread.runLock.release()
		except:
			pass
	finally:
		# Stop the pktGenThread
		pktGenThread.runLock.acquire()
		pktGenThread.running = False
		pktGenThread.runLock.release()
		# JOIN pktGenThread
		pktGenThread.join()


if __name__ == '__main__':
	main()




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
