#!/usr/bin/python

import boto
import os
import sys
import tempfile
import gzip

include_prefix = '### VMESH_INCLUDE:'

def user_data_script(filename):
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
	
	# Debug
	if True:
		with gzip.GzipFile(filename=combined_temp_file.name, mode='rt') as readfile:
			for line in readfile:
				print line,

	return combined_temp_file

def main():
	# create the user-data-script (merging in includes)
	if len(sys.argv) > 1:
		filename = sys.argv[1]
	else:
		filename = 'user-data-script.py'
	gzipped_file = user_data_script(filename)

	# use boto to launch the spot instances request
	
	

if __name__ == '__main__':
	main()
