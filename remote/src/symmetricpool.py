#!/usr/bin/python3

import multiprocessing
import queue
import unittest

def run_loop(tasks=None, results=None):
	if tasks is None:
		return
	while(True):
		func_name, args, kwargs = tasks.get()
		if func_name is None: # stop sentinel
			break
		if args is None:
			args = []
		if kwargs is None:
			kwargs = dict()
		result = functions[func_name](*args, **kwargs)
		if result is not None:
			results.put(result)

class SymmetricPool:
	def __init__(self, count=1):
		self._processes = []
		self._results = multiprocessing.Queue()
		self._functions = dict()
		for _ in range(count):
			q = multiprocessing.Queue()
			p = multiprocessing.Process(target=run_loop, kwargs={'tasks':q, 'results':self._results})
			p.start()
			self._processes.append((p, q))

	def do_all(self, func_name, args=None, kwargs=None):
		for process, queue in self._processes:
			queue.put((func_name, args, kwargs))
	
	def end(self):
		self.do_all(None) # stop sentinel
		for _, queue in self._processes:
			queue.close()
		for process, _ in self._processes:
			process.join()
	
	def dump_results(self):
		while(True):
			try:
				r = self._results.get_nowait()
				print(r)
			except queue.Empty:
				break

def task():
	ret = dict()
	ret['init_size'] = len(vpush.get_soup())
	soup_size = random.randint(0,1000)
	vpush.get_soup().set_size(soup_size, 100, 100)
	ret['final_size'] = len(vpush.get_soup())
	return ret

def soup_size():
	return {'soup_size': len(vpush.get_soup())}

functions = {'task':task,
			 'soup_size': soup_size}

class TestMultiprocessing(unittest.TestCase):
	def setUp(self):
		vpush.get_soup().clear()
		self._processes = SymmetricPool(4)
	
	def test_multiprocessing(self):
		self._processes.do_all('task')
		self._processes.do_all('soup_size')

	def tearDown(self):
		self._processes.end()
		#self._processes.dump_results()

if __name__ == '__main__':
	unittest.main()

