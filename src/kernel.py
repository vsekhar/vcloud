'''
Created on 2010-10-11
'''

import basekernel
import queue
import sys
import time
from threading import Thread, Event, Lock
from util.repeattimer import RepeatTimer

class KernelFunctionWrapper:
	def __init__(self, lock, function):
		self.lock = lock
		self.function = function

	def __call__(self, *args):
		with self.lock:
			return self.function(*args)


class KernelLocker:
	"""KernelLocker serializes commands to the kernel
	
	Kernels are generally not thread-safe, so only one command should be
	issued at a time."""
	
	def __init__(self, kmod):
		self.kmod = kmod
		self.lock = Lock()
	
	def __getattr__(self, attr):
		try:
			return KernelFunctionWrapper(self.lock, self.kmod.__dict__[attr])
		except NameError:
			print('Kernel code does not have attribute ', attr)
			raise

class KernelRunner(Thread):
	def __init__(self, kernel, sendinterval=1, msgsperinterval=10):
		Thread.__init__(self, name="kernel_runner")
		self.sendinterval = sendinterval
		self.msgsperinterval = msgsperinterval
		self.kernel = kernel
		self.kl = self.kernel.kl
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
				[self.outqueue.put(m) for m in self.kl.send(self.msgsperinterval)]
				self.lastsend = time.time()
			
			# process incoming
			msgs = []
			try:
				while(1):
					msgs.append(self.inqueue.get_nowait())
			except queue.Empty:
				if len(msgs): self.kl.receive(msgs)
			
			# do some work
			self.kl.advance(1)
	
	def cancel(self):
		self.cancelevent.set()

class Kernel(basekernel.BaseKernel):
	def __init__(self, p, k, greeting, kernelconfig):

		# dynamic kernel module
		from sys import path
		newpath = path[0] + "/" + p
		path.insert(1,newpath)
		self.kl = KernelLocker(__import__(k))		# we never store the module itself
		assert(self.kl.greet() == greeting)			# id the kernel
		assert(self.kl.initialize(kernelconfig))	# initialize it
		
		# set up message passing
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
				if count >= max_n:
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
		[self.inqueue.put(m) for m in msgs]
		return len(msgs)
	
	def listnodes(self):
		return self.kl.listnodes()

