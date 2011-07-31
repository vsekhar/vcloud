#!/usr/bin/env python

import argparse, sys, os

# create safe argv (for logging, etc.)
def hider(x):
	if x.startswith('--access-key') or x.startswith('--secret-key'):
		return x.partition('=')[0] + '=[hidden]'
	else:
		return x
safeargv = list(map(hider, sys.argv))

# parse command line
parser = argparse.ArgumentParser(description='vmesh-launch.py: initial package script')
parser.add_argument('-c', '--reset', default=False, action='store_true', help='reset metadata at startup')
parser.add_argument('-l', '--local', default=False, action='store_true', help='run in local/debug mode (no AWS metadata, implies --interactive)')
parser.add_argument('--log', type=str, default='vmesh.log', help='log file')
parser.add_argument('-i', '--interactive', default=False, action='store_true', help='interactive (don\' redirect console to logfile)')
parser.add_argument('-d', '--debug', default=argparse.SUPPRESS, action='store_true', help='debug (print more output)')
parser.add_argument('--list', default=False, action='store_true', help='list hosts and exit (do not register this host)')
parser.add_argument('--config-file', type=str, help='config file')
parser.add_argument('--access-key', type=str, help='access key')
parser.add_argument('--secret-key', type=str, help='secret key')
parsed_args = parser.parse_args()

if parsed_args.local:
	parsed_args.interactive = True

# parse config file
config_parser = argparse.ArgumentParser(description='vmesh-launch config file parser')
config_parser.add_argument('--connections', type=int, default=3)
config_parser.add_argument('--sdb-domain', type=str, default='vmesh')
config_parser.add_argument('--kernel-interval', type=int, default=3)
config_parser.add_argument('--peer-mgmt-interval', type=int, default=3)
config_parser.add_argument('--checkpoint-interval', type=int, default=120)
config_parser.add_argument('--clean-up-interval', type=int, default=30)
config_parser.add_argument('--peer-entry-lifetime', type=int, default=120)
config_parser.add_argument('--debug', default=argparse.SUPPRESS, action='store_true')
from multiprocessing import cpu_count
config_parser.add_argument('--kernel-processes', type=int, default=cpu_count() * 2)

if not parsed_args.config_file:
	parsed_args.config_file = os.path.dirname(__file__) + os.sep + 'config'
config_data = [line.strip() for line in open(parsed_args.config_file).readlines() if not line.strip().startswith('#') and not line.strip() == '']
config_args = config_parser.parse_args(config_data)

# pull args into module namespace
sys.modules[__name__].__dict__.update(config_args.__dict__)
sys.modules[__name__].__dict__.update(parsed_args.__dict__) # command-line overrides config file

try:
	debug
except NameError:
	# No debug option specified anywhere, so make it false
	debug = False

# debug
if __name__ == '__main__':
	print(sys.modules[__name__].__dict__)

