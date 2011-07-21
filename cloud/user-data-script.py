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

def restart(with_sudo=False, add_args=[]):
	import os, sys
	if with_sudo:
		command = 'sudo'
		new_args = ['sudo'] + sys.argv
		new_args += ['--vmesh-trying-for-sudo']
	else:
		command = sys.argv[0]
		new_args = sys.argv
		new_args = filter(lambda x: not x.startswith('--vmesh-trying-for-sudo'), new_args)
	new_args += add_args
	sys.stdout.flush()
	os.execvp(command, new_args)
	# exit(0)

def upgrade_and_install():
	import apt
	global args

	cache = apt.Cache()
	try:
		cache.update()
		cache.open(None)
		cache.upgrade()
		for pkg in packages:
			cache[pkg].mark_install()
		cache.commit():
	except apt.cache.LockFailedException:
		if not args.vmesh_trying_for_sudo:
			logging.info("Need super-user rights, restarting with sudo...")
			restart(with_sudo=True)
		else:
			raise
	logging.info("Upgrade/install complete, restarting without sudo...")
	restart(with_sudo=False, add_args=['--skip-update'])

if __name__ == '__main__':
	import sys
	global args
	args = parse_args()

	# setup logging
	if args.debug:
		logfile = sys.stdout
	else:
		logfile = open(logfilename, 'a')
		global old_stdout, old_stderr
		old_stdout = sys.stdout
		old_stderr = sys.stderr
		sys.stdout = logfile
		sys.stderr = logfile

	logging.basicConfig(stream=logfile, level=logging.INFO,
						format='%(asctime)s: %(message)s',
						datefmt='%m/%d/%Y %I:%M:%S %p')

	logging.info('Vmesh version: %d.%d.%d' % version)
	logging.info('Python version: %d.%d.%d' % sys.version_info[:3])

	if not args.skip_update:
		logging.info("Upgrading and installing...")
		upgrade_and_install()
	else:
		logging.info("Running user_code...")
		user_code()

