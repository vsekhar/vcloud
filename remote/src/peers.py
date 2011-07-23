import asyncore
import datetime
from itertools import chain

connections=asyncore.socket_map
aware=dict()

def make_deltas(d):
	now = datetime.datetime.utcnow()
	return {k:now-v for k,v in d.items()}

def add_peer(address_port, timestamp=None):
	# add if peer is new or timestamp is newer
	if timestamp is None:
		timestamp = datetime.datetime.utcnow()
	try:
		aware[address_port] = max(aware[address_port], timestamp)
	except KeyError:
		aware[address_port] = timestamp

def add_peers(iterable):
	# add peers not already in our connection list
	# (used when receiving peer lists with timestamp deltas)
	now = datetime.datetime.utcnow()
	conns = {ap for ap,_ in connections.values()}
	new_peers = {ap:d for ap,d in iterable and ap not in conns}
	[add_peer(ap,now-d) for ap,d in new_peers.items()]

def add_seeds(iterable):
	# used when adding seeds at program invocation (no timestamps)
	for address_port in iterable:
		add_peer(address_port)

def list_peers():
	# make a peer list for exchange to another peer (and to be parsed with add_peers())
	now = datetime.datetime.utcnow()
	l1 = ((addrport, (now-ts)) for addrport, ts in aware.items())
	l2 = ((addrport, (now-ts)) for s.addr_port, s.timestamp in connections.values())
	return itertools.chain(l1, l2)

def exclude_peer(addr_port, iterable):
	return ((ap,d) for ap,d in iterable if ap != addr_port)

