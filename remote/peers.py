import asyncore
import logger

import args
import aws
import serversocket

hostname = aws.metadata['public-hostname']
port = serversocket.serversocket.port
logger.info('Hostname: %s:%s' % (hostname, port))

def hosts_query():
	dom = aws.get_sdb_domain(args.sdb_domain)
	return dom.select('SELECT timestamp FROM %s WHERE timestamp is not null ORDER BY timestamp ASC' % args.sdb_domain)

def hosts():
	for host in hosts_query():
		yield host

def clear_hosts():
	for host in hosts():
		host.delete()

def peers():
	for host in hosts():
		if host.name == hostname:
			continue
		else:
			yield host

def new_peers(num=1):
	# generate peers not currently connected to
	count = 0
	hostnames = set(serversocket.connections.values())
	for peer in peers():
		if peer.name

def print_peers():
	import time
	print 'Peers (hostname, port, age):'
	cur_time = time.time()
	for peer in peers():
		print peer.name, peer.port, cur_time - float(peer['timestamp'])

def purge_old_peers(lifetime=3600):
	import time
	cur_time = time.time()
	oldest_time = cur_time - lifetime
	for peer in peers():
		if float(peer['timestamp']) < oldest_time:
			peer.delete()
		else:
			break # peers are sorted oldest-first

def update_node():
	dom = aws.get_sdb_domain(args.sdb_domain)
	record = dom.get_item(hostname)
	if record is None:
		record = dom.new_item(hostname)
	import time
	cur_time = time.time()
	record['port'] = port
	record['timestamp'] = cur_time
	record.save()
	

