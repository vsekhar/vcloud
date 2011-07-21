#!/usr/bin/python

import boto
import sys

price='0.40'
ami='ami-e2af508b'
instance_type='m1.small'
count=1
persistent=True
keypair_name='cdk11744-nix'
security_groups=['default', 'Cluster']


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
	if args.debug:
		with open('data', mode='wb') as f:
			f.write(zipped_user_data)
	elif args.spot_instances:
		reservation = conn.request_spot_instances(
								price=price,
								image_id=ami,
								count=count,
								instance_type=instance_type,
								type='persistent' if persistent else 'one-time',
								key_name=keypair_name,
								security_groups=security_groups,
								user_data=zipped_user_data
								)
	else:
		reservation = conn.run_instances(
								image_id=ami,
								min_count=count,
								max_count=count,
								key_name=keypair_name,
								security_groups=security_groups,
								instance_type=instance_type,
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
	parser.add_argument('-d', '--debug', default=False, action='store_true', help='run in debug mode')
	parser.add_argument('-f', '--script-file', type=str, default='./userdatascript.py', help='script file to process and launch (default=./user-data-script.py)')
	parser.add_argument('-s', '--spot-instances', default=False, action='store_true', help='run with spot instances instead of on-demand')
	return parser.parse_args()

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

