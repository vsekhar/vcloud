#!/usr/bin/env python

packages = []
logfilename = 'user-data-script.log'

################################################
# End user modifiables
################################################

### VMESH_INCLUDE: CREDENTIALS.py
# above line gets you access_key, secret_key, bucket, package, and script,
# access them as CREDENTIALS.access_key, etc.

import logging

internal_packages = ['python-boto']

def parse_args():
	import argparse

	parser = argparse.ArgumentParser(description='user-data-script.py: initial python instance startup script')
	parser.add_argument('--local', default=False, action='store_true', help='run in local mode (log to screen, no AWS metadata)')
	parser.add_argument('--debug', default=False, action='store_true', help='run in debug mode (additional reporting, pauses before cleanup, etc.)')
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
	logging.info('### Vmesh user-data script starting (python %d.%d.%d, timestamp %d) ###' % (sys.version_info[:3] + (time.time(),)))
	logging.debug('sys.argv: %s', str(sys.argv))

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
			install_packages = set(internal_packages + packages)
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

def get_s3_bucket():
	import boto
	global args
	if args.local:
		s3conn = boto.connect_s3()
	else:
		s3conn = boto.connect_s3(CREDENTIALS.access_key, CREDENTIALS.secret_key)
	b = s3conn.get_bucket(CREDENTIALS.bucket)
	if not b:
		logging.critical('Bucket %s does not exist' % CREDENTIALS.bucket)
		exit(1)
	return b

def run_package():
	import tarfile, tempfile, shutil, os
	global args

	bucket = get_s3_bucket()
	key = bucket.get_key(CREDENTIALS.package)
	if not key:
		logging.critical('Key %s in bucket %s does not exist' % (CREDENTIALS.package, CREDENTIALS.bucket))
		exit(1)

	with tempfile.SpooledTemporaryFile(max_size=10240, mode='w+b') as tf:
		td = tempfile.mkdtemp()
		logging.info('Downloading %s from bucket %s' % (CREDENTIALS.package, CREDENTIALS.bucket))
		key.get_contents_to_file(tf)
		tf.seek(0)
		tar = tarfile.open(fileobj=tf)
		tar.extractall(path=td)
		import subprocess, sys
		command = [td + os.sep + CREDENTIALS.script]
		command += ['--log=%s' % logfilename]
		command += ['--access-key=%s' % CREDENTIALS.access_key]
		command += ['--secret-key=%s' % CREDENTIALS.secret_key]
		if args.local:
			command += ['--local']
		logging.shutdown()
		sys.stdout.flush()
		try:
			proc = subprocess.Popen(command, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
			errno = proc.wait()
		except KeyboardInterrupt:
			errno = 1
		if args.local:
			if args.debug:
				print "Press any key to clean-up",
				raw_input()
			import shutil
			shutil.rmtree(td)
	exit(errno)

if __name__ == '__main__':
	global args
	args = parse_args()
	
	setup_logging()
	upgrade_and_install()
	# de-escalate privilages?
	run_package()

