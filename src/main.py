#!/usr/bin/python3

import os

import vhost
import vmesh
import options
import config
import peers
import seedfile
import multiprocessing

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

	if seedfilename is not None: seedfile.read(seedfilename)
	vhost_port = int(config.get('vmesh', 'vhost_port'))
	
	cancel = multiprocessing.Event()
	num_processes = multiprocessing.cpu_count() * 2
	pool = multiprocessing.Pool(processes=num_processes)
	# start the pool processes, communicating somehow with them as to their ports

	try:
		vhost.run_forever(vhost_port)
	except KeyboardInterrupt:
		cancel.set()
	finally:
		pool.close()
		pool.join()

