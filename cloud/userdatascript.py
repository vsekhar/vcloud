#!/usr/bin/python

packages = ()

logfilename = 'user-data-script.log'
vmesh_domain = 'vmesh'
version = (1,0,0)

### VMESH_INCLUDE: CREDENTIALS.py
# above line gets you access_key, secret_key, bucket, package, and script,
# access them as CREDENTIALS.access_key, etc.

import logging

def get_archive():
	pass

def get_domain():
	import boto
	global args
	if args.local:
		sdb = boto.connect_sdb()
	else:
		sdb = boto.connect_sdb(CREDENTIALS.access_key, CREDENTIALS.secret_key)
	dom = sdb.lookup(vmesh_domain)
	if dom is None:
		dom = sdb.create_domain(vmesh_domain)
	return dom

def register_node(hostname):
	dom = get_domain()
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

def print_hosts():
	dom = get_domain()
	for item in dom:
		print item.name, item['timestamp']

def user_code():
	global metadata, args
	metadata = get_metadata()
	logging.info('Registering: %s' % (metadata['public-hostname']))
	register_node(metadata['public-hostname'])
	if args.local:
		print_hosts()
	# get archive

################################################
# End user modifiables
################################################

internal_packages = ('python-boto')

def parse_args():
	import argparse

	parser = argparse.ArgumentParser(description='user-data-script.py: initial python instance startup script')
	parser.add_argument('--local', default=False, action='store_true', help='run in local/debug mode (log to screen, no AWS metadata)')
	parser.add_argument('--skip-update', default=False, action='store_true', help='skip apt package updates')
	parser.add_argument('--vmesh-trying-for-sudo', default=False, action='store_true', help='INTERNAL: flag used in permissions escalation')

	return parser.parse_args()

def get_metadata():
	global args
	if args.local:
		return {'public-hostname': 'localhost',
				'ami-launch-index': 0,
				'ami-id': 'ami-localdebug'}
	else:
		import boto.utils
		return boto.utils.get_instance_metadata()

def restart(with_sudo=False, add_args=[], remove_args=[]):
	import os, sys
	if with_sudo:
		command = 'sudo'
		new_args = ['sudo'] + sys.argv
	else:
		command = sys.argv[0]
		new_args = sys.argv

	def myfilter(s):
		for remove_arg in remove_args:
			if s.startswith(remove_arg):
				return False
		return True

	new_args = filter(myfilter, new_args)
	new_args += add_args
	sys.stdout.flush()
	os.execvp(command, new_args)
	# exit(0)

def upgrade_and_install():
	global args
	if args.skip_update or args.local:
		logging.info('Skipping upgrade/install')
		return
	else:
		import apt
		cache = apt.Cache()
		try:
			cache.update()
			cache.open(None)
			cache.upgrade()
			install_packages = set(internal_packages) + set(packages)
			for pkg in install_packages:
				cache[pkg].mark_install()
			logging.info('Upgrading and installing...')
			cache.commit()
		except apt.cache.LockFailedException:
			if not args.vmesh_trying_for_sudo:
				logging.info("Need super-user rights to upgrade and install, restarting with sudo...")
				restart(with_sudo=True, add_args=['--vmesh-trying-for-sudo'])
			else:
				raise
		logging.info("Upgrade/install complete, restarting without sudo...")
		restart(with_sudo=False, add_args=['--skip-update'], remove_args=['--vmesh-trying-for-sudo'])

def setup_logging():
	import sys, time
	global args
	# setup logging
	if args.local:
		logfile = sys.stdout
	else:
		logfile = open(logfilename, 'a')
		global old_stdout, old_stderr
		old_stdout = sys.stdout
		old_stderr = sys.stderr
		sys.stdout = logfile
		sys.stderr = logfile

	logging.basicConfig(stream=logfile, level=logging.DEBUG,
						format='%(asctime)s: %(message)s',
						datefmt='%m/%d/%Y %I:%M:%S %p')

	logging.getLogger('boto').setLevel(logging.CRITICAL)
	logging.info('### Vmesh %d.%d.%d starting (python %d.%d.%d, timestamp %d) ###' % (version + sys.version_info[:3] + (time.time(),)))
	logging.debug('sys.argv: %s', str(sys.argv))

if __name__ == '__main__':
	global args
	args = parse_args()
	
	setup_logging()
	upgrade_and_install()
	#de-escalate privilages
	user_code()

