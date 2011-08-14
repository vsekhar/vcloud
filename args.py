
import sys
import os
import argparse
from ast import literal_eval as parse
import ConfigParser

# command line
parser = argparse.ArgumentParser(description='cloudlaunch.py: launch scripts in the cloud')
parser.add_argument('-l', '--local', default=False, action='store_true', help='run locally')
parser.add_argument('-u', '--upload-only', default=False, action='store_true', help='upload the package, then exit')
parser.add_argument('-s', '--script-only', default=False, action='store_true', help='process and print user data script, then exit')
parser.add_argument('-f', '--config-file', default=None, help='config file to use (default=\'~/.vcloud\')')
parser.add_argument('-c', '--configuration', default='DEFAULT', help='configuration name in config file (default=\'DEFAULT\')')
parser.add_argument('--list-configurations', default=False, action='store_true', help='list configurations, then exit')
parser.add_argument('-n', '--count', default=argparse.SUPPRESS, help='number of nodes to start')
parser.add_argument('-d', '--debug', default=False, action='store_true', help='run in debug mode (more output)')
_args = parser.parse_args()

# configuration file
if not _args.config_file:
	homedir = os.getenv('USERPROFILE') or os.getenv('HOME')
	_args.config_file = os.path.join(homedir, '.vcloud')

config = ConfigParser.SafeConfigParser()
config.read(_args.config_file)

# handle inheritance
inherit_processed = set()

def process_inheritance(section):
	inherit_processed.add(section)

	# does it inherit anything?
	if config.has_option(section, 'inherit'):
		src = parse(config.get(section, 'inherit'))

		# recurse if needed
		if src not in inherit_processed:
			process_inheritance(src)

		# process current section
		cur_values = list(config.items(section)) # stash (dest overrides src)
		for name, value in config.items(src):
			config.set(section, name, value) # get source values
		for name, value in cur_values:
			config.set(section, name, value) # restore overrides

for section in config.sections():
	process_inheritance(section)

# combined getter (defaults to active configuration, unless a section is specified)
def get(name, section=None):
	""" Argument getter (combines command-line and config file, with command-line
		taking precedence) """
	global _args
	try:
		return getattr(_args, name) # command-line overrides configuration file
	except AttributeError:
		global config, config_name
		return parse(config.get(section or _args.configuration, name))

