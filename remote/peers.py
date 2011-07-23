import aws, logging, args

def register_node(hostname):
	logging.info('Registering: %s' % (aws.metadata['public-hostname']))
	dom = aws.get_sdb_domain(args.domain)
	record = dom.get_item(hostname)
	if record is None:
		record = dom.new_item(hostname)
	import time
	cur_time = time.time()
	record['timestamp'] = cur_time
	record.save()
	
	# purge old records
	lifetime = 3600 # def = 3600 = 1 hour
	query = dom.select("SELECT timestamp FROM %s WHERE timestamp is not null ORDER BY timestamp ASC" % args.domain)
	for item in query:
		if float(item['timestamp']) < cur_time - lifetime:
			item.delete()
		else:
			break # it's a sorted list

def print_hosts():
	dom = aws.get_sdb_domain(args.domain)
	for item in dom:
		print item.name, item['timestamp']


