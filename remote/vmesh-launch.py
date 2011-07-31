#!/usr/bin/env python

version = (1,0,0)

import time
import string
import random

import args # processes args
import peers # starts server socket

from logger import log

def random_string(length = 8):
	return ''.join([random.choice(string.letters + string.digits) for _ in range(length)])

if __name__ == '__main__':
	if args.list:
		for host in peers.hosts():
			print(host.name, host['timestamp'])
		exit(0)

	if args.reset:
		peers.clear_hosts()

	# management intervals
	peer_mgmt_time = time.time()
	kernel_time = time.time()
	checkpoint_time = time.time()
	clean_up_time = time.time()

	# initialization
	peers.update_node()
	peers.purge_old_peers()

	# main run loop
	try:
		while(1):
			peers.poll()

			cur_time = time.time()

			# kernel processing
			if cur_time - kernel_time > args.kernel_interval:
				try:
					random_id = random.choice(list(peers.connections.keys()))
					connection = peers.connections[random_id]
				except IndexError:
					pass
				else:
					msg = random_string()
					connection.send_msg('kernel', msg)
				finally:
					kernel_time = cur_time

			# peer processing
			if cur_time - peer_mgmt_time > args.peer_mgmt_interval:
				peer_mgmt_time = cur_time
				peers.top_up()
				peers.update_node()
				if args.debug:
					s = 'connections: '
					for c in peers.connections.values():
						s += c.peer_id + ' '
					s += 'unknowns: %d' % len(peers.unknown_connections)
					log.debug(s)

			# checkpoint
			if cur_time - checkpoint_time > args.checkpoint_interval:
				# do checkpoint (stopping the kernel?)
				# tell kernels to checkpoint themselves?
				pass

			# clean-up
			if cur_time - clean_up_time > args.clean_up_interval:
				peers.purge_old_peers()
	except KeyboardInterrupt:
		pass

