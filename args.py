
import sys
import os
import argparse
import ast
import ConfigParser

# command line
parser = argparse.ArgumentParser(description='cloudlaunch.py: launch scripts in the cloud')
parser.add_argument('-l', '--local', default=False, action='store_true', help='run locally')
parser.add_argument('-u', '--upload-only', default=False, action='store_true', help='upload the package, then exit')
parser.add_argument('-s', '--script-only', default=False, action='store_true', help='process and print user data script, then exit')
parser.add_argument('-f', '--config-file', default=None, help='config file to use (default=\'~/.vcloud\')')
parser.add_argument('-c', '--configuration', default='DEFAULT', help='configuration name in config file (default=\'DEFAULT\')')
parser.add_argument('-d', '--debug', default=False, action='store_true', help='run in debug mode (more output)')
_args = parser.parse_args()

# configuration file
if not _args.config_file:
	homedir = os.getenv('USERPROFILE') or os.getenv('HOME')
	_args.config_file = os.path.join(homedir, '.vcloud')

config = ConfigParser.SafeConfigParser()
config.read(_args.config_file)

# combined getter
def get(name, section=None):
	global _args
	try:
		return getattr(_args, name) # command-line overrides configuration file
	except AttributeError:
		global config, config_name
		return ast.literal_eval(config.get(section or _args.configuration, name))

