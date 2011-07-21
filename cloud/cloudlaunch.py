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

def user_data_script(filename):
	import os, gzip, tempfile
	combined_temp_file = tempfile.NamedTemporaryFile()
	user_data_gzip = gzip.GzipFile(fileobj=combined_temp_file, mode='wt')

	with open(os.path.dirname(__file__) + os.sep + filename) as user_data:
		for line in user_data:
			if line.strip().startswith(include_prefix):
				filename = line[len(include_prefix):].strip()
				namespacename, _, _ = filename.partition('.')
				user_data_gzip.write('class %s:\n' % namespacename)
				with open(os.path.dirname(__file__) + os.sep + filename) as includefile:
					for includeline in includefile:
						user_data_gzip.write('\t' + includeline)
			else:
				user_data_gzip.write(line)

	user_data_gzip.close()
	combined_temp_file.flush()
	return combined_temp_file

def print_gzipped_file(filename):
	import gzip
	with gzip.GzipFile(filename=filename, mode='rt') as readfile:
		for line in readfile:
			print line,

def launch(user_data):
	import boto
	conn = boto.connect_ec2()
	reservation = conn.request_spot_instances(
							price=price,
							image_id=ami,
							count=count,
							instance_type=instance_type,
							type='persistent' if persistent else 'one-time',
							key_name=keypair_name,
							security_groups=security_groups,
							user_data=user_data
							)
	return reservation

def load_binary_data(datafilename):
	ret = b''
	with open(datafilename, mode='rb') as data_file:
		while True:
			data = data_file.read(1024*1024)
			if len(data):
				ret += data
			else:
				break
	return ret

def main():
	import sys
	# create the user-data-script (merging in includes)
	if len(sys.argv) > 1:
		filename = sys.argv[1]
	else:
		filename = 'user-data-script.py'
	gzipped_file = user_data_script(filename)
	# print_gzipped_file(gzipped_file.name)
	spot_resv = launch(user_data=load_binary_data(gzipped_file.name))

if __name__ == '__main__':
	main()

