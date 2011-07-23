import multiprocessing
import random
import options
from queue import Empty, Full

from computeproc import ComputeProcess

class ComputePool:
	def __init__(self, processes=options.vals.processes):
		if not processes:
			processes = multiprocessing.cpu_count() * 2
		self._stop = multiprocessing.Event()
		self._outqueue = multiprocessing.Queue()
		self._pool = [ComputeProcess(stop=self._stop, outqueue=self._outqueue) for _ in range(processes)]

	def __len__(self):
		return len(self._pool)
	
	def __iter__(self):
		return iter(self._pool)
	
	def start(self):
		[p.start() for p in self._pool]
	
	def cancel(self):
		self._stop.set()
	
	def join(self):
		[p.join() for p in self._pool]
	
	def terminate(self):
		[p.terminate() for p in self._pool]
	
	def checkpoint(self):
		[p.checkpointevent.set() for p in self._pool]

	def insert_random(self, msg):
		random.choice(self._pool).inqueue.put_nowait(msg)
	
	def msgs(self):
		try:
			while(1):
				yield self._outqueue.get_nowait()
		except Empty:
			pass

