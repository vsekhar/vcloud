import datetime
import pickle
import hmac

from asynchat import async_chat
from multiprocessing.connection import deliver_challenge, answer_challenge, AuthenticationError
from os import urandom

import peers
import config
import vmesh

MAX_MSG_LEN = 1024*1024 # 1 megabyte
COMMAND_TERMINATOR = b'\n'

class BadCommand(Exception): pass
class BadData(Exception): pass
class BinaryCommand(Exception):
	def __init__(self, length):
		self.length = length
	
	def __len__(self):
		return self.length

#
# Handles moving closed connections to 'aware' list, basic txt and binary
# communication, and timestamping
#
class BaseConnectionHandler(async_chat):
	def __init__(self, socket, remote_server_port=None, timestamp=None):
		async_chat.__init__(self, sock=socket)
		self.socket=socket
		self.peer_address_port=self.socket.getpeername()
		self.peer_address=self.peer_address_port[0]
		self.peer_port=self.peer_address_port[1]
		self.remote_server_port=remote_server_port
		self._preserve=False
		
		self.set_terminator(COMMAND_TERMINATOR)
		self.deferred_line=None
		self.ibuffer=[]

		if timestamp:
			self.timestamp = timestamp
		else:
			self.update_timestamp()
		
	def collect_incoming_data(self, data):
		self.ibuffer.append(data)

	def found_terminator(self):
		data = b''.join(self.ibuffer)
		self.ibuffer = []
		if isinstance(self.get_terminator(), int):
			# got more_data for a binary command
			self.dispatch(self.deferred_line, data)
			self.set_terminator(COMMAND_TERMINATOR)
			self.deferred_line=None
		else:
			# got just one line for a non-binary command
			data = data.decode('ascii').strip()
			try:
				self.dispatch(data)
			except BinaryCommand as b:
				self.set_terminator(len(b))
				self.deferred_line=data
			except BadCommand:
				self.push('bad'.encode('ascii'))
				self.close_when_done()

	def dispatch(self, data, binary_data=None):
		raise NotImplemented

	def handle_write(self):
		async_chat.handle_write(self)
		self.update_timestamp()

	def handle_read(self):
		async_chat.handle_read(self)
		self.update_timestamp()
	
	def handle_close(self):
		async_chat.handle_close(self)
		if self._preserve:
			peers.aware[self.peer_address_port] = self.timestamp
	
	def update_timestamp(self):
		self.timestamp = datetime.datetime.utcnow()

	def send_txt(self, txt):
		self.push((txt+'\n').encode('ascii'))
	
	def send_binary(self, hdr, data):
		msg_hdr=hdr + " %d\n" % len(data)
		self.push(msg_hdr.encode('ascii') + data)
	
	def send_obj(self, obj):
		data = pickle.dumps(obj)
		msg_hdr = "obj %d\n" % len(data)
		self.push(msg_hdr.encode('ascii') + data)
	
	def set_preserve(preserve=True):
		self._preserve = preserve

CHALLENGE = b'#CHALLENGE#'
WELCOME = b'#WELCOME#'
FAILURE = b'#FAILURE#'
AUTH_MESSAGE_LENGTH = 32

#
# Handles command dispatching and authentication
#
class ConnectionHandler(BaseConnectionHandler):
	def __init__(self, socket, remote_server_port=None, timestamp=None):
		BaseConnectionHandler.__init__(self, socket, remote_server_port, timestamp)
		self._auth_key = config.get('vmesh', 'secret').encode()
		self._authenticated=False
		self.commandtable = dict()

		self.add('whatis_my_port', self.whatis_my_port)
		self.add('whatis_your_port', self.whatis_your_port)
		self.add('whatis_your_id', self.whatis_your_id)
		self.add('my_port_is', self.my_port_is)
		# self.add('your_port_is', self.your_port_is)	# diagnostics only
		self.add('my_id_is', self.my_id_is)
		self.add('challenge', self.auth_challenge, binary=True)
		self.add('response', self.auth_response, binary=True)
		self.add('authenticated', self.authenticated)
		self.add('hello', self.hello)
		self.add('obj', self.obj, binary=True)
		
		if self.remote_server_port is None:
			# Incoming connection, so authenticate and request server port
			self.start_challenge()
			self.send_txt("whatis_your_port")

		# send check for self-connection
		self.send_txt("whatis_your_id")
		
	def add(self, command, function, binary=False):
		self.commandtable[command] = (function, binary)
		
	def dispatch(self, commandline, binary_data=None):
		(command, _, params) = commandline.partition(' ')
		try:
			function, is_binary = self.commandtable[command]
		except KeyError:
			raise BadCommand("Bad command %s" % command)
		if is_binary:
			if not binary_data:
				raise BinaryCommand(int(params))
			assert int(params) == len(binary_data), 'got %d, needed %d' % (len(binary_data), int(params))
			function(binary_data)
		else:
			function(params)

	def whatis_your_port(self, _):
		self.send_txt('my_port_is %s' % vmesh.server_socket.port)

	def whatis_your_id(self, _):
		self.send_txt('my_id_is %s' % vmesh.id)

	def whatis_my_port(self, _):
		self.send_txt('your_port_is %s' % self.remote_server_port)

	def my_port_is(self, data):
		self.remote_server_port = int(data)

	def my_id_is(self, data):
		if data == vmesh.id:
			self.preserve=False
			self.close_when_done()

	def hello(self, _):
		self.send_txt('hello-to-you')
		self.preserve = False	# only humans say hello

	def obj(self, data):
		if not self._authenticated:
			self.send_txt('not_authenticated')
			return

		obj = pickle.loads(data)
		if obj.name == "msg":
			vmesh.recvqueue.put_nowait(obj.binary_data)
		elif obj.name == "peers":
			peers.add_peers(obj.peers)
		elif obj.name == "request_peers":
			newobj = Object()
			newobj.name = "peers"
			all_peers = peers.list_peers()
			peers = peers.exclude_peer(all_peers, self.peer_address_port)
			newobj.peers = [peers]
			self.send_obj(newobj)
		else:
			self.send_txt("Bad obj: %s" % str(obj))
			raise BadData("Bad obj: %s" % str(obj))

	def start_challenge(self):
		self._auth_msg = urandom(AUTH_MESSAGE_LENGTH)
		self._auth_msg_digest = hmac.new(self._auth_key, self._auth_msg).digest()
		self.send_binary("challenge", CHALLENGE + self._auth_msg)

	def auth_challenge(self, data):
		assert data[:len(CHALLENGE)] == CHALLENGE, 'data = %r' % data
		data = data[len(CHALLENGE):]
		digest = hmac.new(self._auth_key, data).digest()
		self.send_binary("response", digest)

	def auth_response(self, data):
		if data == self._auth_msg_digest:
			self._authenticated = True

	def authenticated(self, _):
		self.send_txt(str(self._authenticated))

