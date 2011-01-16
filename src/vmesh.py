import random
import string
import asyncore
import multiprocessing

import config
import serversocket
import connectionhandler
import peers

id=''.join([random.choice(string.digits) for _ in range(8)])
server_socket = None
vhost_port = None
sendqueue = multiprocessing.Queue()
recvqueue = multiprocessing.Queue()
poll = asyncore.poll
sockets = asyncore.socket_map
connections = None
timeout = None
port = None

def init(port_override=None):
	global server_socket, port, connections, timeout
	if port_override:
		port = port_override
	else:
		port = config.getint('vmesh', 'port')
	connections = config.getint('vmesh', 'connections')
	timeout = config.getint('vmesh', 'timeout')
	server_socket = serversocket.ServerSocket('', vport)
	print("Vmesh(%s): %d, (vhost @ %d)" % (id, server_socket.port, vport))

def manage_peers():
	if len(sockets) < connections:
		try:
			addr_port, timestamp = aware.popitem()
		except KeyError:
			pass
		else:
			ConnectionHandler()
			
	pass
	# periodic peer management
		# request updated peer lists from peers
		# cull stale peer entries
		# spawn new connections if needed
		# send msgs from sendqueue

