import optparse

import config
import version

def get_parser():
	ret = optparse.OptionParser(version="%prog " + version.string)
	ret.add_option("-v", "--verbose", dest="verbosity", action="count")
	ret.add_option("-f", "--config-file", dest="configfile")
	ret.add_option("-p", "--port", dest="port", type='int', help="force port to listen on (overrides config file)")
	ret.add_option("-s", "--seed", dest="cmd_line_seeds", default=[], action="append", help="seed in addr,port format")
	return ret

vals=optparse.Values()
args=None

def parse_cmd_line():
	global vals
	(vals, args) = get_parser().parse_args(values=vals)

def init():
	parse_cmd_line()
	config.parse(vals.configfile)
	seedfilename=None
	try:
		seedfilename = config.get('vmesh', 'seed_file')
	except config.NoOption as e:
		pass

	# set port
	try:
		vals.port
	except AttributeError:
		vals.port = int(config.get('vmesh', 'port'))

	# merge seed lists
	vals.seeds = []
	if seedfilename is not None:
		with open(seedfilename, 'r') as file:
			for name in file:
				vals.seeds.append((name, vals.port))
	if hasattr(vals, 'cmd_line_seeds'):
		for addr_port in vals.cmd_line_seeds:
			address, _, port = addr_port.partition(':')
			vals.seeds.append((address, int(port)))

