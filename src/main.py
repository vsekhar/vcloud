#!/usr/bin/python3

import os

import options
import config
import vmesh
import computeproc
import random

def make_child(initial, port, vhost_port):
	def child(initial, port, vhost_port):
		if initial:
			vmesh.init(vhost_port, listen_port=port)
			vmesh.run_forever()
		else:
			peers.add_peer(('127.0.0.1', port))
			vmesh.init(vhost_port)
			vmesh.run_forever()


if __name__ == '__main__':
	options.parse_cmd_line()
	config.parse()
	seedfilename=None
	try:
		seedfilename = config.get('vmesh', 'seed_file')
	except config.NoOption as e:
		print(e)

	if seedfilename is not None: peers.read_seed_file(seedfilename)
	
	num_processes = multiprocessing.cpu_count() * 2
	pool = computeproc.ComputePool(num_processes)
	pool.start()
	try:
		port= options.vals.port
	except AttributeError:
		vmesh.init()
	else:
		vmesh.init(port)

	while(1):
		try:
			vmesh.poll(0)
			vmesh.manage_peers()
			sockets = len(vmesh.sockets)
			for msg in pool.msgs:
				if random.randint(1, num_processes+sockets) > num_processes:
					vmesh.sendqueue.put_nowait(msg)
				else:
					pool.insert_random(msg)
		except KeyboardInterrupt:
			pool.cancel()
		finally:
			pool.join()

