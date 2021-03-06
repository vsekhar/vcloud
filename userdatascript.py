#!/usr/bin/env python

logfilename = 'vcloud.log'

################################################
# End user modifiables
################################################

### VMESH_CONFIG
# above line gets you access_key, secret_key, install_packages, bucket, package, type, and script,
# access them as CONFIG.access_key, etc.

import logging
install_packages = ['python-boto', 'screen', 'htop']
if CONFIG.type == 'twisted':
	install_packages.append('python-twisted')
try:
	install_packages += list(CONFIG.install_packages)
except AttributeError:
	pass
repositories = list(CONFIG.repositories)

temp_prefix = 'vmeshtmp'

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
	logging.shutdown()
	sys.stdout.flush()
	os.execvp(command, new_args)
	# exit(0)

def user_info():
	import pwd, os
	global args
	if args.local:
		return pwd.getpwuid(os.getuid())
	else:
		return pwd.getpwnam(CONFIG.user.strip())

def get_logfile_path():
	global args
	if args.local:
		return logfilename # use current directory
	else:
		userinfo = user_info()
		return os.path.join(userinfo.pw_dir, logfilename) # user's home dir

def setup_logging():
	import time, sys, os
	global args, log

	log = logging.getLogger('user-data-script')
	log.setLevel(logging.DEBUG if args.debug else logging.INFO)
	formatter = logging.Formatter(fmt='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
	
	# setup logging to file
	logfile = open(get_logfile_path(), 'a')
	userinfo = user_info()
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
			# repos
			from softwareproperties.SoftwareProperties import SoftwareProperties
			sp = SoftwareProperties()
			for repo in repositories:
				if sp.add_source_from_line(repo):
					log.info('Adding repository: %s' % repo)
				else:
					log.error('Error adding repository: %s' % repo)
			sp.sourceslist.save()

			# packages
			log.info('Updating package info...')
			cache.update()
			cache.open(None)
			cache.upgrade()
			log.info('Marking packages for install: %s' % ' '.join(install_packages))
			for pkg in install_packages:
				try:
					cache[pkg].mark_install()
				except KeyError:
					log.error('Could not mark package for install: %s' % pkg)
			log.info('Committing package changes')
			cache.commit()
		except apt.cache.LockFailedException:
			if not args.vmesh_trying_for_sudo:
				log.info("Need super-user rights to upgrade and install, restarting (with sudo)")
				restart(with_sudo=True, add_args=['--vmesh-trying-for-sudo'])
			else:
				log.error('Could not acquire apt cache lock (someone else is installing stuff, or this user is not a sudoer)')
				raise
		log.info("Upgrade/install complete, restarting (no sudo)")
		restart(with_sudo=False, add_args=['--skip-update'], remove_args=['--vmesh-trying-for-sudo'])

def get_s3_bucket():
	import boto
	global args, log
	if args.local:
		s3conn = boto.connect_s3()
	else:
		s3conn = boto.connect_s3(CONFIG.node_access_key, CONFIG.node_secret_key)
	b = s3conn.get_bucket(CONFIG.bucket)
	if not b:
		log.critical('Bucket %s does not exist' % CONFIG.bucket)
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
		self.create()
		return self

	def __exit__(self, exc_type, exc, tb):
		self.checked_remove()

	def create(self):
		import tempfile
		if self.tdir is not None:
			self.remove()
		self.tdir = tempfile.mkdtemp(dir=self.dir, prefix=temp_prefix)
	
	def checked_remove(self):
		if self.tdir is not None and self.delete:
			if self.prompt:
				print 'TempDir (%s): Press any key to clean up (\'q ENTER\' to cancel cleanup)' % self.tdir
				try:
					response = raw_input()
				except KeyboardInterrupt:
					pass
				else:
					if response.lower() != 'q':
						self.remove()

	def remove(self):
		import shutil
		shutil.rmtree(self.tdir)
		self.tdir = None

def run_package():
	global args, log

	bucket = get_s3_bucket()
	key = bucket.get_key(CONFIG.package)
	if not key:
		log.critical('Key %s in bucket %s does not exist' % (CONFIG.package, CONFIG.bucket))
		exit(1)

	userinfo = user_info()
	username = userinfo.pw_name
	homedir = userinfo.pw_dir

	import subprocess, tempfile, tarfile, sys, os, shlex
	with tempfile.SpooledTemporaryFile(max_size=10240, mode='w+b', dir=homedir, prefix=temp_prefix) as tf:
		with TempDir(dir=homedir, delete=args.local, prompt=True) as td:
			log.info('Downloading %s from bucket %s' % (CONFIG.package, CONFIG.bucket))
			key.get_contents_to_file(tf)
			tf.seek(0)
			tar = tarfile.open(fileobj=tf)
			tar.extractall(path=td.tdir)

			script_args = '--access-key=%s --secret-key=%s' % (CONFIG.node_access_key, CONFIG.node_secret_key)
			for arg in ['local', 'interactive', 'debug']: # pass-through args
				if getattr(args, arg):
					script_args += ' --%s' % arg

			new_env = dict(os.environ)

			if CONFIG.type == 'twisted':
				new_env['PYTHONPATH'] += ':' + td.tdir
				command = 'twistd'
				if args.local:
					command += ' -n'
				else:
					command += ' --uid=%d' % userinfo.pw_uid
					command += ' --gid=%d' % userinfo.pw_gid
				command += ' --rundir=%s' % td.tdir	# run in package dir...
				command += ' --logfile=%s' % get_logfile_path() # but log to user's homedir
				command += ' ' + CONFIG.package_script
				command += ' ' + script_args

			else: # default to script type
				script_path = os.path.join(td.tdir, CONFIG.package_script)
				if args.local:
					command = '%s %s'
				else: # daemonize
					command = 'sudo -u %s screen -dmS vcloud bash -ilc \"%%s %%s\"' % username
				command %= (script_path, script_args)

			log.debug('Running package with command: %s' % command)
			log.info('--- Vcloud user-data-script complete ---')
			logging.shutdown() # log file may be reused by package

			command_seq = shlex.split(command)
			try:
				return subprocess.check_call(args=command_seq, cwd=homedir, env=new_env)
			except KeyboardInterrupt:
				# KeyboardInterrupt propagates up through all scripts
				td.prompt = False # user exited, so cleanup if local
				return 0

def reset_local_environment():
	import os
	userinfo = user_info()
	homedir = userinfo.pw_dir
	os.system('rm -rf %s' % homedir + os.sep + temp_prefix + '*')
	os.system('rm -f %s' % homedir + os.sep + logfilename)

if __name__ == '__main__':
	import sys
	global args
	args = parse_args()
	
	if args.reset:
		reset_local_environment()

	setup_logging()
	upgrade_and_install()
	return run_package()

