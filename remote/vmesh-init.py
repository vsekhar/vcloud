#!/usr/bin/env python

version = (1,0,0)
vmesh_domain = 'vmesh'

import logging, boto

def get_sdb_domain():
	global args
	if args.local:
		sdb = boto.connect_sdb()
	else:
		sdb = boto.connect_sdb(args.access_key, args.secret_key)
	dom = sdb.lookup(vmesh_domain)
	if dom is None:
		dom = sdb.create_domain(vmesh_domain)
	return dom

def register_node(hostname):
	logging.info('Registering: %s' % (metadata['public-hostname']))
	dom = get_sdb_domain()
	record = dom.get_item(hostname)
	if record is None:
		record = dom.new_item(hostname)
	import time
	cur_time = time.time()
	record['timestamp'] = cur_time
	record.save()
	
	# purge old records
	lifetime = 3600 # def = 3600 = 1 hour
	query = dom.select("SELECT timestamp FROM %s WHERE timestamp is not null ORDER BY timestamp ASC" % vmesh_domain)
	for item in query:
		if float(item['timestamp']) < cur_time - lifetime:
			item.delete()
		else:
			break # it's a sorted list

def get_metadata():
	global args, metadata
	if args.local:
		metadata = {'public-hostname': 'localhost',
				'ami-launch-index': 0,
				'ami-id': 'ami-localdebug'}
	else:
		import boto.utils
		metadata = boto.utils.get_instance_metadata()

def print_hosts():
	dom = get_sdb_domain()
	for item in dom:
		print item.name, item['timestamp']

def setup_logging():
	import sys, time
	global args
	# setup logging
	if args.local:
		logfile = sys.stdout
	else:
		logfile = open(args.log, 'a')
		global old_stdout, old_stderr
		old_stdout = sys.stdout
		old_stderr = sys.stderr
		sys.stdout = logfile
		sys.stderr = logfile

	logging.basicConfig(stream=logfile, level=logging.DEBUG,
						format='%(asctime)s: %(message)s',
						datefmt='%m/%d/%Y %I:%M:%S %p')

	logging.getLogger('boto').setLevel(logging.CRITICAL)
	logging.info('vmesh-init.py %d.%d.%d starting (python %d.%d.%d, timestamp %d)' % (version + sys.version_info[:3] + (time.time(),)))
	def hider(x):
		if x.startswith('--access-key') or x.startswith('--secret-key'):
			return x.partition('=')[0] + '=[hidden]'
		else:
			return x
	commandline = map(hider, sys.argv)
	logging.debug('sys.argv: %s' % commandline)

def parse_args():
	import argparse
	global args

	parser = argparse.ArgumentParser(description='vmesh-init.py: initial package script')
	parser.add_argument('--local', default=False, action='store_true', help='run in local/debug mode (log to screen, no AWS metadata)')
	parser.add_argument('--log', type=str, help='log file')
	parser.add_argument('--access-key', type=str, help='access key')
	parser.add_argument('--secret-key', type=str, help='secret key')

	args = parser.parse_args()

if __name__ == '__main__':
	global metadata, args
	parse_args()
	setup_logging()
	get_metadata()
	register_node(metadata['public-hostname'])
	if args.local:
		print_hosts()

