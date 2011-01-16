import optparse

import version

def get_parser():
	ret = optparse.OptionParser(version="%prog " + version.string)
	ret.add_option("-v", "--verbose", dest="verbosity", action="count")
	ret.add_option("-f", "--config-file", dest="configfile")
	return ret

vals=optparse.Values()
args=None

def parse_cmd_line():
	global vals
	(vals, args) = get_parser().parse_args(values=vals)

