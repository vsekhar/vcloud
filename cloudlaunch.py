#!/usr/bin/env python

"""
Requires boto 2.0+ (boto1.9b, included with Ubuntu 11.04, has a bug
that makes it impossible to make persistent spot instance requests)

NB: boto 1.9b will work on remote machines, only this script needs 2.0

Get and use latest boto using:
	git clone git://github.com/boto/boto.git
	export PYTHONPATH=$PYTHONPATH:/<path_to_boto>/boto  # in .bashrc
"""

import boto
import sys

include_prefix = '### VMESH_INCLUDE:'

def parse_args():
	import argparse

	parser = argparse.ArgumentParser(description='cloudlaunch.py: launch scripts in the cloud')
	parser.add_argument('-l', '--local', default=False, action='store_true', help='run locally')
	parser.add_argument('-u', '--upload-only', default=False, action='store_true', help='only upload the package, do not start instances')
	parser.add_argument('-f', '--script-file', type=str, default='./userdatascript.py', help='script file to process and launch (default=./user-data-script.py)')
	parser.add_argument('-m', '--ami', type=str, default='ami-e2af508b', help='AMI to start (default=\'ami-e2af508b\', Ubuntu 11.04 Natty Server 32-bit us-east-1)')
	parser.add_argument('-n', '--count', type=int, default=1, help='number of instances to start (default=1)')
	parser.add_argument('-t', '--instance-type', type=str, default='m1.small', help='instance type (default=m1.small)')
	parser.add_argument('-k', '--key-pair', type=str, default='cdk11744-nix', help='key pair name (default=cdk11744-nix)')
	parser.add_argument('-g', '--security-group', type=str, action='append', help='enable security group for instances (default=\'default\')')
	parser.add_argument('-s', '--spot-instances', default=False, action='store_true', help='run with spot instances (default is on-demand instances)')
	parser.add_argument('-p', '--persistent', default=False, action='store_true', help='make request persistent (valid only for spot instance requests)')
	parser.add_argument('-r', '--price', type=float, default=0.04, help='price (valid only for spot instance requests, default=0.04)')
	parser.add_argument('-d', '--package-directory', type=str, help='startup directory to package and send to nodes (default=<script_dir>/remote)')
	parser.add_argument('-b', '--debug', default=False, action='store_true', help='run in debug mode')
	args = parser.parse_args()

	# complex defaults
	if not args.security_group:
		args.security_group = ['default']
	if not args.package_directory:
		import os
		args.package_directory = os.path.dirname(__file__) + os.sep + 'remote/'

	return args

def process_script(script_filename):
	import os
	ret = ''
	with open(script_filename) as user_data:
		for line in user_data:
			if line.strip().startswith(include_prefix):
				include_filename = line[len(include_prefix):].strip()
				namespacename, _, _ = include_filename.partition('.')
				ret += 'class %s:\n' % namespacename
				with open(os.path.dirname(script_filename) + os.sep + include_filename) as includefile:
					for includeline in includefile:
						ret += '\t' + includeline
			else:
				ret += line
	return ret

def upload_package():
	import boto, tempfile, tarfile, StringIO, sys
	import CREDENTIALS # to get desired bucket and package name
	global args

	# prepare and upload package
	with tempfile.SpooledTemporaryFile(max_size=10240) as tf:
		tar = tarfile.open(fileobj=tf, mode='w:gz')
		tar.add(name=args.package_directory, arcname='.', recursive=True)
		tar.close()
	
		s3conn = boto.connect_s3()
		b = s3conn.get_bucket(CREDENTIALS.bucket)
		if not b:
			b = s3conn.create_bucket(CREDENTIALS.bucket)
		k = b.get_key(CREDENTIALS.package)
		if not k:
			k = b.new_key(CREDENTIALS.package)
		print 'Uploading package %s' % CREDENTIALS.package
		def report_progress(at, total):
			print '\r%f%%' % (at/total),
			sys.stdout.flush()
		k.set_contents_from_file(tf, cb=report_progress)
		print ' done'

class ScopedTemporaryFile:
	def __init__(self, executable=False):
		import tempfile
		self.file = tempfile.NamedTemporaryFile(delete=False)
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
	import tempfile, os, stat, sys
	tf = ScopedTemporaryFile(executable=True)
	tf.file.writelines(user_data)
	tf.close()
	import subprocess, sys
	sys.stdout.flush()
	new_args = [tf.name, '--local']
	if args.debug:
		new_args += ['--debug']
	proc = subprocess.Popen(new_args, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
	exit(proc.wait())

def launch_remote(user_data):
	import boto, StringIO, gzip, contextlib
	global args

	# prepare gzipped user-data
	with contextlib.closing(StringIO.StringIO()) as sio:
		zipper = gzip.GzipFile(fileobj=sio, mode='wb')
		zipper.write(user_data)
		zipper.close()
		zipped_user_data = sio.getvalue()

	ec2conn = boto.connect_ec2()
	if args.spot_instances:
		reservation = ec2conn.request_spot_instances(
								price=str(args.price),
								image_id=args.ami,
								count=args.count,
								instance_type=args.instance_type,
								type=('persistent' if args.persistent else 'one-time'),
								key_name=args.key_pair,
								security_groups=args.security_group,
								user_data=zipped_user_data
								)
	else:
		reservation = ec2conn.run_instances(
								image_id=args.ami,
								min_count=args.count,
								max_count=args.count,
								key_name=args.key_pair,
								security_groups=args.security_group,
								instance_type=args.instance_type,
								user_data=zipped_user_data
								)
	return reservation

def main():
	global args
	args = parse_args()
	upload_package()
	if not args.upload_only:
		script = process_script(args.script_file)
		if args.local:
			launch_local(user_data=script)
		else:
			resv = launch_remote(user_data=script)
			print resv

if __name__ == '__main__':
	main()

