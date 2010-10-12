'''
Created on 2010-10-11
'''

import basekernel
import queue
import sys
import time
from threading import Thread, Event
from util.repeattimer import RepeatTimer

class KernelRunner(Thread):
	def __init__(self, kernel, sendinterval=1, msgsperinterval=10):
		Thread.__init__(self, name="kernel_runner")
		self.sendinterval = sendinterval
		self.msgsperinterval = msgsperinterval
		self.kernel = kernel
		self.kmod = self.kernel.kmod
		self.inqueue = self.kernel.inqueue
		self.outqueue = self.kernel.outqueue
		self.cancelevent = Event()
		self.lastsend = time.time()
	
	def run(self):
		while 1:
			if self.cancelevent.is_set():
				return
			
			# process outgoing
			if time.time() - self.lastsend > self.sendinterval:
				for _ in range(self.msgsperinterval):
					self.outqueue.put(self.kmod.send(self.msgsperinterval))
				self.lastsend = time.time()
			
			# process incoming
			try:
				while(1):
					self.kmod.receive(self.inqueue.get_nowait())
			except queue.Empty:
				pass
			
			# do some work
			self.kmod.advance(1)
	
	def cancel(self):
		self.cancelevent.set()

class Kernel(basekernel.BaseKernel):
	def __init__(self, p, k, greeting, kernelconfig):

		# dynamic kernel module
		from sys import path
		newpath = path[0] + "/" + p
		path.insert(1,newpath)
		__import__(k)
		self.kmod = sys.modules[k]
		assert(self.kmod.greet() == greeting)		# id the kernel
		assert(self.kmod.initialize(kernelconfig))	# initialize it
		
		# management structures
		self.inqueue = queue.Queue()
		self.outqueue = queue.Queue()
		self.run_thread = KernelRunner(kernel = self)

	def start(self):
		'''starts the kernel (must not block)'''
		self.run_thread.start()
    
	def cancel(self):
		'''signals that the kernel should finish up (must not block)'''
		self.run_thread.cancel()
    
	def join(self):
		'''blocks until the kernel is actually stopped
		you usually need to run cancel() before join() in order to signal that
		the kernel should finish up, if you don't, then join() basically just
		waits for the kernel to finish naturally, which may or may not ever happen'''
		self.run_thread.join()
    
	def get_message(self):
		return self.get_messages(1)[0]
    
	def get_messages(self, max_n=1):
		'''returns at most max_n=1 kernel messages as a list
		Must not block. Must be thread-safe. Kernel messages are sent by vmesh
		as-is over a socket as binary data, with no encoding applied'''
		ret = []
		try:
			count = 0
			while(1):
				ret.append(self.outqueue.get_nowait())
				++count
				if max_n is not None and count > max_n:
					break
		except queue.Empty:
			pass

		return ret
    
	def put_message(self, msg):
		return self.put_messages([msg])
    
	def put_messages(self, msgs):
		'''applies received kernel messages to the kernel, returns number processed
		Must not block. Must be thread-safe. msgs must be a list of messages.
		If all msgs cannot be consumed, function should return how many were.
			E.g.:
				msgs = [1,2,3,4,5]
				while msgs:
				    count = self.put_messages(msgs)
				    msgs = msgs[count:]
		'''
		for msg in msgs:
			self.inqueue.put(msg)
		return len(msgs)
	
	def listnodes(self):
		return self.kmod.listnodes()

