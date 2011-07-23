#!/usr/bin/python

import vmesh
import computepool

if __name__ == '__main__':
	pool = computepool.ComputePool()
	pool.start()

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

