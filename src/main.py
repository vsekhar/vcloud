#!/usr/bin/python3

import options

import vmesh
import computepool

if __name__ == '__main__':
	options.init()
	
	pool = computepool.ComputePool()
	pool.start()
	vmesh.init(listen_port=options.vals.port, seeds=options.vals.seeds)

	try:
		while(1):
			vmesh.poll(0)
			vmesh.manage_peers()
			vmesh.process_msgs(pool)
			if 0: # test for checkpoint interval
				pool.checkpoint()

	except KeyboardInterrupt:
		pool.cancel()
	finally:
		pool.join()

