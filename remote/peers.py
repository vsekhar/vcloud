import aws, logging, args

def get_peers():
	dom = aws.get_sdb_domain(args.sdb_domain)
	return dom.select("SELECT timestamp FROM %s WHERE timestamp is not null ORDER BY timestamp ASC" % args.sdb_domain)

def purge_old_peers(lifetime=3600):
	import time
	cur_time = time.time()
	oldest_time = cur_time - lifetime
	peers = get_peers()
	for peer in peers:
		if float(peer['timestamp']) < oldest_time:
			peer.delete()
		else:
			break # peers are sorted oldest-first

def register_node():
	hostname = aws.metadata['public-hostname']
	logging.info('Registering: %s' % hostname)
	dom = aws.get_sdb_domain(args.sdb_domain)
	record = dom.get_item(hostname)
	if record is None:
		record = dom.new_item(hostname)
	import time
	cur_time = time.time()
	record['timestamp'] = cur_time
	record.save()
	
def print_hosts():
	peers = get_peers()
	for peer in peers:
		print peer.name, peer['timestamp']


