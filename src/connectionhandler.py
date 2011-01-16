from asynchat import async_chat
import datetime
import peercmds
import peers

MAX_MSG_LEN = 1024*1024 # 1 megabyte
COMMAND_TERMINATOR = b'\n'

class ConnectionHandler(async_chat):
	def __init__(self, socket, remote_server_port=None):
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
		
		# check for self-connection
		peercmds.dispatch(self, 'whatis_your_id')
		
		if self.remote_server_port is None:
			# request it
			self.remote_server_port = None
			self.push("server_port\n".encode('ascii'))
		
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

	def send_msg(self, binary_msg):
		msg_hdr = 'msg %d\n' % len(binary_msg)
		self.push(msg_hdr.encode('ascii') + binary_msg)
	
	def send_txt(self, txt):
		self.push((txt+'\n').encode('ascii'))

