# TODO: Convert this to use argparse (once python 3.2 is updated to fix bug)

import optparse
import socket

import config
import version

def get_parser():
	ret = optparse.OptionParser(version="%prog " + version.string)
	ret.add_option("-v", "--verbose", dest="verbosity", action="count")
	ret.add_option("-f", "--config-file", dest="configfile")
	ret.add_option("-p", "--port", dest="port", type='int', help="force port to listen on (overrides config file)")
	ret.add_option("-s", "--seed", dest="cmd_line_seeds", default=[], action="append", help="seed in addr,port format")
	ret.add_option("-o", "--other-hosts-file", dest="other_hosts_file", help="file to load other hostnames from (one per line)")
	ret.add_option("-n", "--processes", dest="processes", type='int', help="number of compute processes (overrides config file, default=cpu_count*2)")
	return ret

vals, args = get_parser().parse_args()
config.parse(vals.configfile)

if not hasattr(vals, 'port'):
	vals.port = int(config.get('vmesh', 'port'))
	# fail if no port specified (cannot be on an ephemeral port since it must be discoverable)

if not hasattr(vals, 'processes'):
	try:
		vals.processes = int(config.get('vmesh', 'processes'))
	except config.NoOption:
		# default to cpu_count * 2
		vals.processes = None

try:
	seedfilename = vals.other_hosts_file
except NameError:
	seedfilename = None

vals.connections = int(config.get('vmesh', 'connections'))
vals.timeout = int(config.get('vmesh', 'timeout'))

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
if seedfilename is not None:
	with open(seedfilename, 'r') as otherhostsfile:
		port = int(config.get('vmesh', 'port')) # don't use cmdline port override here
		for hostname in otherhostsfile:
			addrinfo = socket.getaddrinfo(hostname, port, socket.AF_INET, socket.SOCK_STREAM)
			assert len(addrinfo) == 1, 'Multiple address resolutions: %s' % str(addrinfo)
			# addrinfo looks like [(fam, type, proto, canonname, (address, port))]
			address = addrinfo[0][4][0]
			vals.seeds.append((address, port))

