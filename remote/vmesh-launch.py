#!/usr/bin/env python

version = (1,0,0)

import time
import string
import random

import args # processes args
import peers # starts server socket

def random_string(length = 8):
	return ''.join([random.choice(string.letters + string.digits) for _ in range(length)])

if __name__ == '__main__':
	if args.reset:
		peers.clear_hosts()

	# management intervals
	peer_mgmt_interval = 3
	peer_mgmt_time = time.time()

	kernel_interval = 3
	kernel_time = time.time()

	clean_up_interval = 30
	clean_up_time = time.time()

	# initialization
	peers.update_node()

	# main run loop
	# TODO: Need exit condition
	while(1):
		peers.poll()

		cur_time = time.time()

		# kernel processing
		if cur_time - kernel_time > kernel_interval:
			if peers.connections:
				kernel_time = cur_time
				msg = random_string()
				random.choice(peers.connections.values()).send_msg('kernel', msg)

		# peer processing
		if cur_time - peer_mgmt_time > peer_mgmt_interval:
			peer_mgmt_time = cur_time
			peers.top_up()
			peers.update_node()
			print 'connections: ',
			for c in peers.connections.values():
				print c.peer_id,
			print " unknowns: %d" % len(peers.unknown_connections)

		# clean-up
		if cur_time - clean_up_time > clean_up_interval:
			peers.purge_old_peers()

