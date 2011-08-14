#!/usr/bin/env python

"""
Requires boto 2.0+ (boto1.9b, included with Ubuntu 11.04, has a bug
that makes it impossible to make persistent spot instance requests)

NB: boto 1.9b will work on remote machines, only this script needs 2.0

Get and use latest boto using:
	git clone git://github.com/boto/boto.git
	export PYTHONPATH=$PYTHONPATH:/<path_to_boto>/boto  # in .bashrc
"""

import aws
import sys
import os

import args

# script processing constants
user_data_script_file = 'userdatascript.py'
include_prefix = '### VMESH_CONFIG'
config_to_include = ['node_access_key', 'node_secret_key', 'install_packages', 'bucket', 'package', 'package_script', 'user']

temp_prefix = 'vmeshtmp'

def process_script():
	import os
	ret = ''
	filename = os.path.dirname(__file__) + os.sep + user_data_script_file
	with open(filename) as user_data:
		for line in user_data:
			if line.strip().startswith(include_prefix):
				ret += 'class CONFIG:\n'
				for value in config_to_include:
					ret += '\t%s = %s\n' % (value, repr(args.get(value)))
				ret += '\n'
			else:
				ret += line
	return ret

def upload_package():
	import tempfile, tarfile, StringIO, sys
	import CREDENTIALS

	pkg_dir = args.get('package_dir')

	# prepare and upload package
	with tempfile.SpooledTemporaryFile(max_size=10240) as tf:
		tar = tarfile.open(fileobj=tf, mode='w:gz')
		tar.add(name=pkg_dir, arcname='.', recursive=True)
		tar.close()
	
		b = aws.s3.get_bucket(CREDENTIALS.bucket)
		if not b:
			b = s3conn.create_bucket(CREDENTIALS.bucket)
		k = b.get_key(CREDENTIALS.package)
		if not k:
			k = b.new_key(CREDENTIALS.package)

		print 'Uploading package %s:' % CREDENTIALS.package
		def report_progress(at, total):
			print '\r%d%%' % ((at/total)*100),
			sys.stdout.flush()
		k.set_contents_from_file(tf, cb=report_progress)
		print ' done'

class ScopedTemporaryFile:
	def __init__(self, executable=False, dir=None):
		import tempfile
		self.file = tempfile.NamedTemporaryFile(delete=False, prefix=temp_prefix, dir=dir)
		self.name = self.file.name
		if executable:
			self.mkexec()

	def __del__(self):
		import os
		if not self.file.closed:
			self.close()
		os.remove(self.name)

	def close(self):
		self.file.flush()
		self.file.close()

	def mkexec(self):
		import os, stat
		os.fchmod(self.file.fileno(), stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)

	def name(self):
		return self.file.name

def launch_local(user_data):
	import os, subprocess, sys, pwd
	homedir = pwd.getpwuid(os.getuid()).pw_dir
	tf = ScopedTemporaryFile(executable=True, dir=homedir)
	tf.file.writelines(user_data)
	tf.close()
	sys.stdout.flush()
	new_args = [tf.name, '--local']
	if args.get('debug'):
		new_args += ['--debug']
	try:
		errno = subprocess.check_call(args=new_args, cwd=homedir, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
	except KeyboardInterrupt:
		errno = 1
	exit(errno)

def launch_remote(user_data):
	import StringIO, gzip
	from contextlib import closing

	# prepare gzipped user-data
	with closing(StringIO.StringIO()) as sio:
		with closing(gzip.GzipFile(fileobj=sio, mode='wb')) as zipper:
			zipper.write(user_data)
		zipped_user_data = sio.getvalue()

	if args.get('spot_instances'):
		requests = aws.ec2.request_spot_instances(
								price=args.get('price'),
								image_id=args.get('ami'),
								count=args.get('count'),
								instance_type=args.get('instance_type'),
								type=('persistent' if args.get('persistent') else 'one-time'),
								key_name=args.get('key_pair'),
								security_groups=args.get('security_groups'),
								user_data=zipped_user_data
								)
		return requests
	else:
		reservation = aws.ec2.run_instances(
								image_id=args.get('ami'),
								min_count=args.get('count'),
								max_count=args.get('count'),
								key_name=args.get('key_pair'),
								security_groups=args.get('security_groups'),
								instance_type=args.get('instance_type'),
								user_data=zipped_user_data
								)
		return reservation

def main():
	import sys
	if args.get('list_configurations'):
		for section in args.config.sections():
			print section
		return

	script = process_script()
	if args.get('script_only'):
		print script
		sys.exit(0)

	upload_package()
	if args.get('upload_only'):
		sys.exit(0)

	elif args.get('local'):
		launch_local(user_data=script)
	else:
		request_response = launch_remote(user_data=script)
		print request_response

if __name__ == '__main__':
	main()

