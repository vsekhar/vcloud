import configparser

vals=None

class NoOption(Exception): pass

def parse(filename):
	global vals
	config = configparser.ConfigParser()
	config.read(filename)
	vals = config

def get(section, name):
	try:
		return vals.get(section, name)
	except configparser.NoOptionError:
		raise NoOption("Option not found: %s->%s" % (section, name))

