import random
import string
import asyncore
import multiprocessing
import socket

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
		port = int(config.get('vmesh', 'port'))
	connections = int(config.get('vmesh', 'connections'))
	timeout = int(config.get('vmesh', 'timeout'))
	server_socket = serversocket.ServerSocket('', port)
	print("Vmesh(%s): %d" % (id, server_socket.port))

def manage_peers():
	if len(sockets) < connections:
		try:
			addr_port, timestamp = peers.aware.popitem()
		except KeyError:
			pass
		else:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect(addr_port)
			connectionhandler.ConnectionHandler(socket=sock, remote_server_port=addr_port[1],
						timestamp=timestamp)
			
	# periodic peer management
		# request updated peer lists from peers
		# cull stale peer entries
		# spawn new connections if needed
		# send msgs from sendqueue

