#!/usr/bin/python3

import os

import options
import config
import vmesh
import computeproc
import random

import peers

if __name__ == '__main__':
	options.parse_cmd_line()
	config.parse()
	seedfilename=None
	try:
		seedfilename = config.get('vmesh', 'seed_file')
	except config.NoOption as e:
		print(e)

	if seedfilename is not None: peers.read_seed_file(seedfilename)
	try:
		for addr_port in options.vals.seeds:
			address, _, port = addr_port.partition(':')
			peers.add_peer((address, int(port)))
	except AttributeError:
		pass
	
	pool = computeproc.ComputePool()
	pool.start()
	try:
		port=int(options.vals.port)
	except AttributeError:
		vmesh.init()
	else:
		vmesh.init(port)

	try:
		while(1):
			vmesh.poll(0)
			vmesh.manage_peers()
			sockets = len(vmesh.sockets)
			for msg in pool.msgs():
				if random.randint(1, num_processes+sockets) > num_processes:
					vmesh.sendqueue.put_nowait(msg)
				else:
					pool.insert_random(msg)
	except KeyboardInterrupt:
		pool.cancel()
	finally:
		pool.join()

