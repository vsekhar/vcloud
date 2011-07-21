#!/usr/bin/python

packages = ['python-boto']

logfilename = 'user-data-script.log'
version = (1,0,0)

### VMESH_INCLUDE: CREDENTIALS.py
# above line gets you access_key, secret_key, bucket, package, and script,
# access them as CREDENTIALS.access_key, etc.

import logging

def get_archive():
	pass

def register_node():
	pass

def get_metadata():
	global args
	if args.debug:
		return {'hostname': 'localhost', 'index': 0}
	else:
		import boto.utils
		return boto.utils.get_instance_metadata()

def user_code():
	import boto
	global metadata
	metadata = get_metadata()
	hostname = metadata['hostname']
	logging.info('Hostname: %s' % hostname)


	# get archive
	# register node

################################################
# End user modifiables
################################################

def parse_args():
	import argparse

	parser = argparse.ArgumentParser(description='user-data-script.py: initial python instance startup script')
	parser.add_argument('--debug', default=False, action='store_true', help='run in debug mode (log to screen, no AWS metadata)')
	parser.add_argument('--skip-update', default=False, action='store_true', help='skip apt package updates')
	parser.add_argument('--vmesh-trying-for-sudo', default=False, action='store_true', help='INTERNAL: flag used in permissions escalation')

	return parser.parse_args()

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
	if args.skip_update:
		logging.info('Skipping upgrade/install')
		return
	else:
		import apt
		cache = apt.Cache()
		try:
			cache.update()
			cache.open(None)
			cache.upgrade()
			for pkg in packages:
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
	import sys
	global args
	# setup logging
	if args.debug:
		logfile = sys.stdout
		level = logging.DEBUG
	else:
		logfile = open(logfilename, 'a')
		global old_stdout, old_stderr
		old_stdout = sys.stdout
		old_stderr = sys.stderr
		sys.stdout = logfile
		sys.stderr = logfile
		level = logging.INFO

	logging.basicConfig(stream=logfile, level=level,
						format='%(asctime)s: %(message)s',
						datefmt='%m/%d/%Y %I:%M:%S %p')

	logging.info('Vmesh %d.%d.%d starting (python %d.%d.%d)' % (version + sys.version_info[:3]))
	logging.debug('sys.argv: %s', str(sys.argv))

if __name__ == '__main__':
	import sys
	global args
	args = parse_args()
	
	setup_logging()
	upgrade_and_install()
	user_code()

