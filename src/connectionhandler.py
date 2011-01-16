from asynchat import async_chat
import datetime
import peercmds
import peers
import config
import pickle
from multiprocessing.connection import deliver_challenge, answerChallenge

MAX_MSG_LEN = 1024*1024 # 1 megabyte
COMMAND_TERMINATOR = b'\n'

class ConnectionHandler(async_chat):
	def __init__(self, socket, remote_server_port=None, timestamp=None):
		async_chat.__init__(self, sock=socket)
		self.socket=socket
		self.peer_address_port=self.socket.getpeername()
		self.peer_address=self.peer_address_port[0]
		self.peer_port=self.peer_address_port[1]
		self.remote_server_port=remote_server_port
		self.preserve=True
		
		self.set_terminator(COMMAND_TERMINATOR)
		self.deferred_line=None
		self.ibuffer=[]
		
		# authenticate
		
		# send check for self-connection
		self.send_txt("whatis_your_id")
		
		try:
			if self.remote_server_port is None:
				# Incoming connection, so authenticate and request server port
				deliver_challenge(self.socket, config.get('vmesh', 'secret'))
				self.send_txt("whatis_your_port")
			else:
				# Outgoing connection, so answer challenge
				answerChallenge(self.socket, config.get('vmesh', 'secret'))
		except AuthenticationError:
			self.preserve=False
			self.close_when_done()
		
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
			# looking for more_data
			peercmds.dispatch(self, self.deferred_line, data)
			self.set_terminator(COMMAND_TERMINATOR)
			self.deferred_line=None
		else:
			# looking for one-liner
			data = data.decode('ascii').strip()
			try:
				peercmds.dispatch(self, data)
			except peercmds.BinaryCommand as b:
				self.set_terminator(len(b))
				self.deferred_line=data
			except peercmds.BadCommand:
				self.push('bad'.encode('ascii'))
				self.close_when_done()

	def handle_write(self):
		async_chat.handle_write(self)
		self.update_timestamp()

	def handle_read(self):
		async_chat.handle_read(self)
		self.update_timestamp()
	
	def handle_close(self):
		async_chat.handle_close(self)
		if self.preserve:
			vmesh.peers[self.addr_port] = self.timestamp
	
	def update_timestamp(self):
		self.timestamp = datetime.datetime.utcnow()

	def send_txt(self, txt):
		self.push((txt+'\n').encode('ascii'))
	
	def send_obj(self, obj):
		data = pickle.dumps(obj)
		msg_hdr = "obj %d\n" % len(data)
		self.push(msg_hdr.encode('ascii') + data)

