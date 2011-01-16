import peers
import datetime

def read(filename):
	with open(filename, 'r') as seed_file:
		now = datetime.datetime.utcnow()
		for line in seed_file:
			(address, _, port) = line.partition(':')
			port=int(port)
			peers.aware[(address,port)] = now

