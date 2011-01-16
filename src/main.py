#!/usr/bin/python3

import os

import options
import config
import vmesh
import computeproc
import random

import peers

if __name__ == '__main__':
	options.init()
	
	pool = computeproc.ComputePool()
	pool.start()
	vmesh.init(listen_port=options.vals.port, seeds=options.vals.seeds)

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

