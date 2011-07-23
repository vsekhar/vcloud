#!/usr/bin/python

import boto
import sys

include_prefix = '### VMESH_INCLUDE:'

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

def launch_remote(user_data):
	import boto, StringIO, gzip
	global args
	conn = boto.connect_ec2()
	sio = StringIO.StringIO()
	zipper = gzip.GzipFile(fileobj=sio, mode='wb')
	zipper.write(user_data)
	zipper.close()
	zipped_user_data = sio.getvalue()
	sio.close()
	if args.spot_instances:
		reservation = conn.request_spot_instances(
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
		reservation = conn.run_instances(
								image_id=args.ami,
								min_count=args.count,
								max_count=args.count,
								key_name=args.key_pair,
								security_groups=args.security_group,
								instance_type=args.instance_type,
								user_data=zipped_user_data
								)
	return reservation

class ScopedTemporaryFile:
	def __init__(self):
		import tempfile
		self.file = tempfile.NamedTemporaryFile(delete=False)
		self.name = self.file.name

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
	import tempfile, os, stat
	tf = ScopedTemporaryFile()
	tf.file.writelines(user_data)
	tf.mkexec()
	tf.close()
	import subprocess, sys
	proc = subprocess.Popen([tf.name, '--local'], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
	proc.wait()

def parse_args():
	import argparse

	parser = argparse.ArgumentParser(description='cloudlaunch.py: launch scripts in the cloud')
	parser.add_argument('-l', '--local', default=False, action='store_true', help='run locally')
	# parser.add_argument('-d', '--debug', default=False, action='store_true', help='run in debug mode')
	parser.add_argument('-f', '--script-file', type=str, default='./userdatascript.py', help='script file to process and launch (default=./user-data-script.py)')
	parser.add_argument('-m', '--ami', type=str, default='ami-e2af508b', help='AMI to start (default=\'ami-e2af508b\', Ubuntu 11.04 Natty Server 32-bit us-east-1)')
	parser.add_argument('-n', '--count', type=int, default=1, help='number of instances to start (default=1)')
	parser.add_argument('-t', '--instance-type', type=str, default='m1.small', help='instance type (default=m1.small)')
	parser.add_argument('-k', '--key-pair', type=str, default='cdk11744-nix', help='key pair name (default=cdk11744-nix)')
	parser.add_argument('-g', '--security-group', type=str, action='append', help='enable security group for instances (default=\'default\')')
	parser.add_argument('-s', '--spot-instances', default=False, action='store_true', help='run with spot instances (default is on-demand instances)')
	parser.add_argument('-p', '--persistent', default=False, action='store_true', help='make request persistent (valid only for spot instance requests)')
	parser.add_argument('-r', '--price', type=float, default=0.40, help='price (valid only for spot instance requests, default=0.40)')
	args = parser.parse_args()

	# security group default only if no others specified
	if not args.security_group:
		args.security_group = ['default']

	return args

def main():
	global args
	args = parse_args()
	script = process_script(args.script_file)
	if args.local:
		launch_local(script)
	else:
		resv = launch_remote(user_data=script)
		print resv

if __name__ == '__main__':
	main()

