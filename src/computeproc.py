import multiprocessing
import time
import random
from queue import Empty, Full

class ComputeProcess(multiprocessing.Process):
	def __init__(self, group=None, target=None, name=None, args=None, kwargs=None):
		multiprocessing.Process.__init__(self)
		self.inqueue = multiprocessing.Queue()
		self.outqueue = multiprocessing.Queue()
		self.stopevent = multiprocessing.Event()
	
	def run():
		while(not self.stopevent.is_set()):
			# do kernel stuff
			time.sleep(1)

class ComputePool:
	def __init__(self, processes=multiprocessing.cpu_count()):
		self._pool = [ComputeProcess() for _ in range(processes)]

	def __len__(self):
		return len(self._pool)
	
	def start(self):
		map(lambda p: p.start(), self._pool)
	
	def cancel(self):
		map(lambda p: p.stopevent.set(), self._pool)
	
	def join(self):
		map(lambda p: p.join(), self._pool)
	
	def terminate(self):
		map(lambda p: p.terminate(), self._pool)

	def insert_random(self, msg):
		random.choice(self._pool).inqueue.put_nowait(msg)
	
	def msgs(self):
		for p in self._pool:
			try:
				while(1):
					yield p.outqueue.get_nowait()
			except Empty:
				pass
		raise StopIteration

