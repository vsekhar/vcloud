import optparse

import config
import version

def get_parser():
	ret = optparse.OptionParser(version="%prog " + version.string)
	ret.add_option("-v", "--verbose", dest="verbosity", action="count")
	ret.add_option("-f", "--config-file", dest="configfile")
	ret.add_option("-p", "--port", dest="port", type='int', help="force port to listen on (overrides config file)")
	ret.add_option("-s", "--seed", dest="cmd_line_seeds", default=[], action="append", help="seed in addr,port format")
	ret.add_option("-n", "--processes", dest="processes", type='int', help="number of compute processes (overrides config file, default=cpu_count*2)")
	return ret

vals=optparse.Values()
args=None

(vals, args) = get_parser().parse_args(values=vals)
config.parse(vals.configfile)
seedfilename=None
try:
	seedfilename = config.get('vmesh', 'seed_file')
except config.NoOption as e:
	pass

if not hasattr(vals, 'port'):
	vals.port = int(config.get('vmesh', 'port'))

if not hasattr(vals, 'processes'):
	try:
		vals.processes = int(config.get('vmesh', 'processes'))
	except config.NoOption:
		# default to cpu_count * 2
		vals.processes = None

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

