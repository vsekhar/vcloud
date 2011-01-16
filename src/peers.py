import asyncore
import datetime

connections=asyncore.socket_map
aware=dict()

def make_deltas(d):
	now = datetime.datetime.utcnow()
	return {k:now-v for k,v in d.items()}

def add_peer(address_port, timestamp=None):
	if timestamp is None:
		timestamp = datetime.datetime.utcnow()
	aware[address_port] = timestamp

