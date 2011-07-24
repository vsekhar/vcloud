import datetime
import pickle
import hmac
import random
import logger
import string

from asynchat import async_chat
from multiprocessing.connection import deliver_challenge, answer_challenge, AuthenticationError
from os import urandom

import args

COMMAND_TERMINATOR = b'\n'
node_id=''.join([random.choice(string.digits) for _ in range(8)])

class Message:
	def __init__(self, cmd, payload=None):
		self.cmd = cmd
		self.payload = payload

	def __str__(self):
		return 'Message(%s, %s, %s)' % (self.cmd, self.data, self.payload)
#
# Handles basic message communication, and timestamping
#
class BaseConnectionHandler(async_chat):
	def __init__(self, socket, timestamp=None):
		async_chat.__init__(self, sock=socket)
		self.socket=socket
		self.peer_address_port=self.socket.getpeername()
		self.peer_address=self.peer_address_port[0]
		self.peer_port=self.peer_address_port[1]
		
		self.set_terminator(COMMAND_TERMINATOR)
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
			# process binary, reset for ascii
			self.dispatch(pickle.loads(data))
			self.set_terminator(COMMAND_TERMINATOR)

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

	def send(self, cmd, payload=None):
		data = pickle.dumps(Message(cmd=cmd, payload=payload))
		msg_hdr = '%d\n' % len(data)
		self.push(msg_hdr.encode('ascii') + data)
	
CHALLENGE = b'#CHALLENGE#'
WELCOME = b'#WELCOME#'
FAILURE = b'#FAILURE#'
AUTH_MESSAGE_LENGTH = 32

#
# Handles command dispatching and authentication
#
class ConnectionHandler(BaseConnectionHandler):
	def __init__(self, socket, server, id=None, timestamp=None):
		BaseConnectionHandler.__init__(self, socket, timestamp)
		self._auth_key = args.authentication_secret.encode()
		self._authenticated=False
		self.server = server

		self.command_table = dict()
		self.add_command('whatis_your_id', self.whatis_your_id)
		self.add_command('my_id_is', self.my_id_is)
		self.add_command('challenge', self.auth_challenge)
		self.add_command('response', self.auth_response)
		self.add_command('hello', self.hello)
		self.add_command('kernel', self.kernel)
		
		if self.id is None:
			# Incoming connection, so authenticate and request server port
			self.start_challenge()
			self.send('whatis_your_id')

	def add_command(command, func):
		self.command_table[command] = func

	def dispatch(self, msg):
		# run code depending on msg type, payload, etc.
		try:
			self.command_table[msg.cmd](msg.payload)
		except KeyError:
			logger.error('Received invalid command: %s' % msg.cmd)

	def whatis_your_id(self, _):
		self.send('my_id_is', node_id)

	def my_id_is(self, payload):
		if payload == node_id:
			self.close_when_done()
			logger.debug('self-connection detected: dropping')

	def hello(self, _):
		self.send('hello-to-you')

	def kernel(self, payload):
		if not self._authenticated:
			self.start_challenge()
			return
		logger.debug('kernel message received')

	def start_challenge(self):
		self._auth_msg = urandom(AUTH_MESSAGE_LENGTH)
		self._auth_msg_digest = hmac.new(self._auth_key, self._auth_msg).digest()
		self.send('cmd', 'challenge', CHALLENGE + self._auth_msg)

	def auth_challenge(self, payload):
		assert payload[:len(CHALLENGE)] == CHALLENGE, 'payload = %r' % payload
		payload = payload[len(CHALLENGE):]
		digest = hmac.new(self._auth_key, payload).digest()
		self.send('cmd', 'response', digest)

	def auth_response(self, payload):
		if payload == self._auth_msg_digest:
			self._authenticated = True

