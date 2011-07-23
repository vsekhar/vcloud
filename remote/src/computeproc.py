import multiprocessing
from queue import Empty
import time

class ComputeProcess(multiprocessing.Process):
	def __init__(self, stop=multiprocessing.Event(),
						checkpoint=multiprocessing.Event(),
						inqueue=multiprocessing.Queue(),
						outqueue=multiprocessing.Queue(),
						group=None, target=None, name=None,
						args=None, kwargs=None):
		multiprocessing.Process.__init__(self)
		self.inqueue = inqueue
		self.outqueue = outqueue
		self.stopevent = stop
		self.checkpointevent = checkpoint
	
	def process_in_msgs(self):
		try:
			while(1):
				msg = self.inqueue.get_nowait()
				# send to kernel
		except Empty:
			pass
	
	def process_out_msgs(self):
		while(0):	# while kernel has msgs
			# self.outqueue.put_nowait(self.kernel.get_msg())
			pass
	
	def advance_kernel(self):
		# kernel advancement code
		time.sleep(1)
	
	def do_checkpoint(self):
		# do checkpoint (use self.name for a unique process ID)
		time.sleep(1)
		return True

	def run(self):
		try:
			while(not self.stopevent.is_set()):
				self.process_in_msgs()
				self.advance_kernel()
			
				if self.checkpointevent.is_set():
					if(self.do_checkpoint()):
						self.checkpointevent.clear()
			
				self.process_out_msgs()
		except KeyboardInterrupt:
			pass
