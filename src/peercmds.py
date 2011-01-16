import vmesh
import msgs

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

commandtable=Table()

def add(name, function, binary=False):
	global commandtable
	commandtable.register(name, function, binary)


def dispatch(handler, commandline, binary_data=None):
	global commandtable
	(command, _, params) = commandline.partition(' ')
	func, is_binary = commandtable.get(command)
	if is_binary:
		if binary_data is None:
			raise BinaryCommand(int(params))
		if int(params) != len(binary_data):
			raise BadData("Expected %d bytes, got %d" % (int(params), len(binary_data)))
		func(handler, binary_data)
	else:
		func(handler, params)

def whatis_your_port(handler, _):
	handler.send_txt('my_port_is %s' % vmesh.server_socket.port)

def whatis_your_id(handler, _):
	handler.send_txt('my_id_is %s' % vmesh.id)

def whatis_my_port(handler, _):
	handler.send_txt('your_port_is %s' % handler.remote_server_port)

def my_port_is(handler, data):
	handler.remote_server_port = int(data)

def my_id_is(handler, data):
	if data == vmesh.id:
		handler.preserve=False
		handler.close_when_done()

def hello(handler, _):
	handler.send_txt('hello-to-you')
	handler.preserve = False	# only humans say hello

def msg(handler, binary_data):
	msgs.incoming.append(binary_data)	

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

def close(handler, _):
	handler.close_when_done()

def bad(handler, _):
	handler.close_when_done()

add('whatis_my_port', whatis_my_port)
add('whatis_your_port', whatis_your_port)
add('whatis_your_id', whatis_your_id)
add('my_port_is', my_port_is)
# add('your_port_is', your_port_is)	# diagnostics only
add('my_id_is', my_id_is)
add('hello', hello)
add('msg', msg, binary=True)
add('peers', send_peers)
add('my_peers', get_peers)
add('kill', kill)
add('close', close)
add('bad', bad)
	

