#!/usr/bin/python3

class BadCommand(Exception): pass
class BadData(Exception): pass
class BinaryCommand(Exception):
	def __init__(self, length):
		self.length = length
	
	def __len__(self):
		return self.length

class Table:
	def __init__(self):
		self.d=dict()
	
	def register(self, command, function, binary=False):
		self.d[command]=(function, binary)
	
	def get(self, command):
		try:
			return self.d[command]
		except KeyError:
			raise BadCommand(command)

class CommandDispatcher:
	def __init__(self):
		self.table=Table()

		self.add('my_server_port', CommandDispatcher.remote_server_port)
		self.add('server_port', CommandDispatcher.req_server_port)
		self.add('hello', CommandDispatcher.hello)
		self.add('msg', CommandDispatcher.msg, binary=True)
		self.add('peers', CommandDispatcher.send_peers)
		self.add('my_peers', CommandDispatcher.get_peers)
		self.add('kill', CommandDispatcher.kill)

	def add(self, name, function, binary=False):
		self.table.register(name, function, binary)
	
	def dispatch(self, handler, commandline, binary_data=None):
		(command, _, params) = commandline.partition(' ')
		func, is_binary = self.table.get(command)
		if is_binary:
			if binary_data is None:
				raise BinaryCommand(int(params))
			if int(params) != len(binary_data):
				raise BadData("Expected %d bytes, got %d" % (int(params), len(binary_data)))
			func(handler, binary_data)
		else:
			func(handler, params)

	def remote_server_port(handler, data):
		handler.remote_server_port = int(data)
	
	def req_server_port(handler, _):
		handler.send_txt('my_server_port %d\n' % handler.port)
	
	def hello(handler, _):
		handler.send_txt('hello-to-you\n')
	
	def msg(handler, binary_data):
		# send the binary data to the kernel somehow
		pass
	
	def send_peers(handler, _):
		# send peers with timecode deltas
		# reply command is 'my_peers'
		pass
	
	def get_peers(handler, data):
		# process peers from data and add them
		# note that they are send with time-code deltas
		pass
	
	def kill(handler, _):
		# kill this peer
		pass
	
dispatcher = CommandDispatcher()

