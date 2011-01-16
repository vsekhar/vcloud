import asyncore
import datetime
from itertools import chain

connections=asyncore.socket_map
aware=dict()

def make_deltas(d):
	now = datetime.datetime.utcnow()
	return {k:now-v for k,v in d.items()}

def add_peer(address_port, timestamp=None):
	if timestamp is None:
		timestamp = datetime.datetime.utcnow()
	aware[address_port] = timestamp

def add_peers(iterable):
	now = datetime.datetime.utcnow()
	[add_peer(ap,now-d) for ap,d in iterable]

def read_seed_file(filename):
	with open(filename, 'r') as seed_file:
		now = datetime.datetime.utcnow()
		for line in seed_file:
			(address, _, port) = line.partition(':')
			port=int(port)
			aware[(address,port)] = now

def list_peers():
	now = datetime.datetime.utcnow()
	l1 = (addrport, now-ts for addrport, ts in aware.items())
	l2 = (addrport, now-ts for s.addr_port, s.timestamp in connections.values())
	return itertools.chain(l1, l2)

def exclude_peer(addr_port, iterable):
	return (ap,d for ap,d in iterable if ap != addr_port)

