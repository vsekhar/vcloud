import asyncore
import datetime
import pickle
import socket

from asynchat import async_chat

import logger
import args
import aws

class Message:
	def __init__(self, cmd, payload=None):
		self.cmd = cmd
		self.payload = payload

	def __str__(self):
		return 'Message(%s, %s)' % (self.cmd, self.payload)

#
# Handles basic message communication, and timestamping
# Requires sub-class to overload dispatch() for actual processing
#
class BaseConnectionHandler(async_chat):

	COMMAND_TERMINATOR = b'\n'

	def __init__(self, socket):
		async_chat.__init__(self, sock=socket)
		self.set_terminator(self.COMMAND_TERMINATOR)
		self.ibuffer=[]
		self.update_timestamp()

	def collect_incoming_data(self, data):
		self.ibuffer.append(data)

	def found_terminator(self):
		data = b''.join(self.ibuffer)
		self.ibuffer = []
		if isinstance(self.get_terminator(), int):
			# process binary, reset for ascii length parameter
			self.dispatch(pickle.loads(data))
			self.set_terminator(self.COMMAND_TERMINATOR)

		else:
			# start collecting binary
			length = int(data.decode('ascii').strip())
			self.set_terminator(length)

	def handle_write(self):
		async_chat.handle_write(self)
		self.update_timestamp()

	def handle_read(self):
		async_chat.handle_read(self)
		self.update_timestamp()

	def update_timestamp(self):
		self.timestamp = datetime.datetime.utcnow()

	def send_msg(self, cmd, payload=None):
		data = pickle.dumps(Message(cmd=cmd, payload=payload))
		msg_hdr = str(len(data))
		msg_hdr = msg_hdr.encode('ascii') + self.COMMAND_TERMINATOR
		self.push(msg_hdr + data)

CHALLENGE = b'#CHALLENGE#'
WELCOME = b'#WELCOME#'
FAILURE = b'#FAILURE#'
AUTH_MESSAGE_LENGTH = 32

connections = {}
unknown_connections = set()

#
# Handles id tracking, command dispatching and authentication
#
class ConnectionHandler(BaseConnectionHandler):

	def __init__(self, socket, server, id=None):
		BaseConnectionHandler.__init__(self, socket)
		self._auth_key = args.authentication_secret.encode()
		self.server = server

		self.peer_id = id
		unknown_connections.add(self)
		if self.peer_id is not None:
			# Outgoing connection
			self.send_msg('my_id_is', node_id)	# push my id to peer

	def handle_close(self):
		unknown_connections.discard(self) # if still unknown, otherwise no-op
		try:
			del connections[self.peer_id]
		except KeyError:
			pass
		BaseConnectionHandler.handle_close(self)

	def my_id_is(self, payload):
		if payload == node_id:
			logger.warning('self-connection detected: dropping')
			self.close_when_done()
		elif payload in connections:
			logger.debug('duplicate connection: dropping')
			self.close_when_done()
		else:
			self.peer_id = payload
			connections[self.peer_id] = self
			unknown_connections.discard(self)
			self.send_msg('id_ack')

	def id_ack(self, _):
		connections[self.peer_id] = self
		unknown_connections.discard(self)

	def hello(self, _):
		self.send_msg('hello-to-you')

	def kernel(self, payload):
		logger.debug('kernel message received: %s' % payload)

	command_table = {
		'my_id_is': my_id_is,
		'id_ack': id_ack,
		'hello': hello,
		'kernel': kernel
	}

	def dispatch(self, msg):
		# run code depending on msg type, payload, etc.
		try:
			self.command_table[msg.cmd](self, msg.payload)
		except KeyError:
			logger.error('Received invalid command: %s' % msg.cmd)

class ServerSocket(asyncore.dispatcher):
    def __init__(self, bind_address='', port=0):
        asyncore.dispatcher.__init__(self)
        self.create_socket(asyncore.socket.AF_INET,
                           asyncore.socket.SOCK_STREAM)
        self.bind((bind_address, port))
        self.port = int(self.socket.getsockname()[1])
        self.listen(1)

    def handle_accept(self):
        sock, address = self.accept()
        logger.debug('incoming connection from %s' % str(address))
        ConnectionHandler(socket=sock, server=self, id=None) # incoming connection

    def handle_close(self):
        self.close()

poll = asyncore.poll
serversocket = ServerSocket()
hostname = aws.metadata['public-hostname']
node_id = hostname + ':' + str(serversocket.port)
logger.info('Node ID: %s' % node_id)
sdb_domain = aws.get_sdb_domain(args.sdb_domain)

def new_connection(id):
	addr,_,port = id.partition(':')
	port = int(port)
	sock = socket.create_connection((addr,port))
	logger.debug('outgoing connection to %s' % id)
	ConnectionHandler(socket=sock, server=serversocket, id=id) # outgoing connection

def hosts(ascending=False):
	query_string = 'SELECT timestamp FROM %s WHERE timestamp is not null ORDER BY timestamp ' % args.sdb_domain
	query_string += 'ASC' if ascending else 'DESC'
	q = sdb_domain.select(query_string)
	for host in q:
		yield host

def clear_hosts():
	for host in hosts():
		host.delete()

def top_up():
	deficit = int(args.connections) - len(connections)
	if deficit > 0:
		count = 0
		for host in hosts():
			if count >= deficit:
				return # done
			if host.name == node_id:
				continue # skip self
			if host.name in connections:
				continue # skip dupes
			try:
				new_connection(host.name)
				count += 1
			except socket.error:
				pass

def print_peers():
	import time
	print 'Peers (hostname, port, age):'
	cur_time = time.time()
	for host in hosts():
		print host.name, cur_time - float(host['timestamp'])

def purge_old_peers(lifetime=int(args.peer_entry_lifetime)):
	import time
	cur_time = time.time()
	oldest_time = cur_time - lifetime
	for host in hosts(ascending=True):
		if float(host['timestamp']) < oldest_time:
			host.delete()
		else:
			break # hosts are sorted oldest-first

def update_node():
	dom = aws.get_sdb_domain(args.sdb_domain)
	record = dom.get_item(node_id)
	if record is None:
		record = dom.new_item(node_id)
	import time
	cur_time = time.time()
	record['timestamp'] = cur_time
	record.save()
	

