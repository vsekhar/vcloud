#!/usr/bin/env python

import argparse, ConfigParser, sys, os

# create safe argv (for logging, etc.)
def hider(x):
	if x.startswith('--access-key') or x.startswith('--secret-key'):
		return x.partition('=')[0] + '=[hidden]'
	else:
		return x
safeargv = map(hider, sys.argv)

# parse command line
parser = argparse.ArgumentParser(description='vmesh-init.py: initial package script')
parser.add_argument('--local', default=False, action='store_true', help='run in local/debug mode (log to screen, no AWS metadata)')
parser.add_argument('--reset', default=False, action='store_true', help='reset metadata and exit')
parser.add_argument('--log', type=str, help='log file')
parser.add_argument('--config-file', type=str, help='config file')
parser.add_argument('--access-key', type=str, help='access key')
parser.add_argument('--secret-key', type=str, help='secret key')
parsed_args = parser.parse_args()

# parse config file
if not parsed_args.config_file:
	parsed_args.config_file = os.path.dirname(__file__) + os.sep + 'config'
config = ConfigParser.ConfigParser()
config.read(parsed_args.config_file)

# pull vmesh config into module namespace
for option in config.options('vmesh'):
	setattr(sys.modules[__name__], option, config.get('vmesh', option))

# vmesh defaults
try:
	if kernel_processes < 1:
		kernel_processes = 1
except NameError:
	kernel_processes = None

# pull kernel config into args.kernel
class kernel:
	pass
for option in config.options('kernel'):
	setattr(kernel, option, config.get('kernel', option))

# pull in command-line options (this is done after parsing the config file to
# allow command-line options to override config file options)
sys.modules[__name__].__dict__.update(parsed_args.__dict__)

# debug
if __name__ == '__main__':
	print sys.modules[__name__].__dict__

