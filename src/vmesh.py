import random
import string
import asyncore

import serversocket
import peers


id=''.join([random.choice(string.digits) for _ in range(8)])
server_socket = None
vhost_port = None

def init(vport, listen_port=0):
	global server_socket, vhost_port
	server_socket = serversocket.ServerSocket('', listen_port)
	vhost_port = vport
	print("Vmesh(%s): %d, (vhost @ %d)" % (id, server_socket.port, vhost_port))

def run_forever():
	while(1):
		asyncore.poll(0)

		# read/write kernel msg queues
		# checkin with vhost at 127.0.0.1:vhost_port

		# periodic peer management
			# request updated peer lists from peers
			# cull stale peer entries
			# spawn new connections if needed

