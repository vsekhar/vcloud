#!/usr/bin/env python

packages = []
logfilename = 'vmesh.log'

################################################
# End user modifiables
################################################

### VMESH_INCLUDE: CREDENTIALS.py
# above line gets you access_key, secret_key, bucket, package, and script,
# access them as CREDENTIALS.access_key, etc.

import logging

internal_packages = ['python-boto', 'screen', 'htop']

def parse_args():
	import argparse

	parser = argparse.ArgumentParser(description='user-data-script.py: initial python instance startup script')
	parser.add_argument('-R', '--reset', default=False, action='store_true', help='reset local environment before running')
	parser.add_argument('-i', '--interactive', default=False, action='store_true', help='interactive (don\'t redirect console to logfile)')
	parser.add_argument('-l', '--local', default=False, action='store_true', help='run in local mode (use fake AWS metadata, skip apt package updates and cleanup temporaries afterwards, implies --interactive)')
	parser.add_argument('-d', '--debug', default=False, action='store_true', help='run in debug mode (additional reporting, etc.)')
	parser.add_argument('-s', '--skip-update', default=False, action='store_true', help='skip apt package updates')
	parser.add_argument('--vmesh-trying-for-sudo', default=False, action='store_true', help='INTERNAL: flag used in permissions escalation')

	args = parser.parse_args()
	if args.local:
		args.interactive = True

	return args

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

def user_info():
	import pwd, os
	global args
	if args.local:
		return pwd.getpwuid(os.getuid())
	else:
		return pwd.getpwnam(CREDENTIALS.user.strip())

def setup_logging():
	import time, sys, os
	global args, log

	log = logging.getLogger('user-data-script')
	log.setLevel(logging.DEBUG if args.debug else logging.INFO)
	formatter = logging.Formatter(fmt='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
	
	# setup logging to file
	userinfo = user_info()
	if args.local:
		logfilepath = logfilename # use current directory
	else:
		logfilepath = userinfo.pw_dir + os.sep + logfilename # user's home dir
	logfile = open(logfilepath, 'a')
	os.fchown(logfile.fileno(), userinfo.pw_uid, userinfo.pw_gid)
	fh = logging.StreamHandler(stream=logfile) # don't use FileHandler since we have to chown an open file
	fh.setFormatter(formatter)
	log.addHandler(fh)

	# setup logging to console
	sh = logging.StreamHandler()
	sh.setFormatter(formatter)
	log.addHandler(sh)

	if not args.interactive:
		# no one is watching, so capture python exception errors and the like
		global old_stdout, old_stderr
		log.info('STDOUT and STDERR redirected to log file: %s' % logfile.name)
		old_stdout = sys.stdout
		old_stderr = sys.stderr
		sys.stdout = logfile
		sys.stderr = logfile

	# boto is normally a bit too noisy
	logging.getLogger('boto').setLevel(logging.WARNING)

	# announce startup
	log.info('### Vmesh user-data script starting (python %d.%d.%d, timestamp %d) ###' % (sys.version_info[:3] + (time.time(),)))
	log.debug('sys.argv: %s', str(sys.argv))

def upgrade_and_install():
	global args, log
	if args.skip_update or args.local:
		log.info('Skipping upgrade/install')
		return
	else:
		import apt
		cache = apt.Cache()
		try:
			log.info('Updating package info...')
			cache.update()
			cache.open(None)
			cache.upgrade()
			install_packages = set(internal_packages + packages)
			for pkg in install_packages:
				cache[pkg].mark_install()
			log.info('Upgrading and installing...')
			cache.commit()
		except apt.cache.LockFailedException:
			if not args.vmesh_trying_for_sudo:
				log.info("Need super-user rights to upgrade and install, restarting with sudo...")
				restart(with_sudo=True, add_args=['--vmesh-trying-for-sudo'])
			else:
				raise
		log.info("Upgrade/install complete, restarting without sudo...")
		restart(with_sudo=False, add_args=['--skip-update'], remove_args=['--vmesh-trying-for-sudo'])

def get_s3_bucket():
	import boto
	global args, log
	if args.local:
		s3conn = boto.connect_s3()
	else:
		s3conn = boto.connect_s3(CREDENTIALS.access_key, CREDENTIALS.secret_key)
	b = s3conn.get_bucket(CREDENTIALS.bucket)
	if not b:
		log.critical('Bucket %s does not exist' % CREDENTIALS.bucket)
		exit(1)
	return b

class TempDir:
	def __init__(self, dir=None, delete=True, prompt=False):
		self.dir = dir
		self.delete = delete
		self.prompt = prompt
		self.exists = False
		self.tdir = None

	def __del__(self):
		self.checked_remove()

	def __enter__(self):
		return self.create()

	def __exit__(self, exc_type, exc, tb):
		self.checked_remove()

	def create(self):
		import tempfile
		if self.tdir is not None:
			self.remove()
		self.tdir = tempfile.mkdtemp(dir=self.dir)
		return self.tdir
	
	def checked_remove(self):
		if self.tdir is not None and self.delete:
			if self.prompt:
				print 'TempDir (%s): Press any key to clean up' % self.tdir
				raw_input()
			self.remove()

	def remove(self):
		import shutil
		shutil.rmtree(self.tdir)
		self.tdir = None

def execv_package():
	global args, log

	bucket = get_s3_bucket()
	key = bucket.get_key(CREDENTIALS.package)
	if not key:
		log.critical('Key %s in bucket %s does not exist' % (CREDENTIALS.package, CREDENTIALS.bucket))
		exit(1)

	userinfo = user_info()
	username = userinfo.pw_name
	homedir = userinfo.pw_dir

	import subprocess, tempfile, tarfile, sys, os
	with tempfile.SpooledTemporaryFile(max_size=10240, mode='w+b', dir=homedir) as tf:
		with TempDir(dir=homedir, delete=args.local, prompt=True) as td:
			log.info('Downloading %s from bucket %s' % (CREDENTIALS.package, CREDENTIALS.bucket))
			key.get_contents_to_file(tf)
			tf.seek(0)
			tar = tarfile.open(fileobj=tf)
			tar.extractall(path=td)

			# build command to drop permissions, run inside a screen, and provide access credentials
			script_path = td + os.sep + CREDENTIALS.script
			script_args = '--access-key=%s --secret-key=%s' % (CREDENTIALS.access_key, CREDENTIALS.secret_key)
			if args.local:
				script_args += ' --local'
			if args.interactive:
				script_args += ' --interactive'
			if args.debug:
				script_args += ' --debug'
			command = 'sudo -u %s screen -dmS vmesh bash -ilc \"%s %s\"'
			command %= (username, script_path, script_args)

			import shlex
			command_seq = shlex.split(command)

			log.info('Running package script with command: %s' % command)
			log.info('--- Vmesh user-data-script complete ---')
			logging.shutdown()
			errno = subprocess.check_call(args=command_seq)
			sys.exit(errno)

def reset_local_environment():
	import os
	username, homedir = user_info()
	os.system('rm -rf %s' % homedir + os.sep + 'tmp*')
	os.system('rm -f %s' % logfilename)

if __name__ == '__main__':
	import sys
	global args
	args = parse_args()
	
	setup_logging()
	if args.reset:
		reset_local_environment()
	upgrade_and_install()
	execv_package() # doesn't return

