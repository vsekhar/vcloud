#!/usr/bin/env python

version = (1,0,0)

import args, peers
import logging

def setup_logging():
	# setup logging
	import sys, time
	if args.local:
		logfile = sys.stdout
	else:
		logfile = open(args.log, 'a')
		global old_stdout, old_stderr
		old_stdout = sys.stdout
		old_stderr = sys.stderr
		sys.stdout = logfile
		sys.stderr = logfile

	logging.basicConfig(stream=logfile, level=logging.DEBUG,
						format='%(asctime)s: %(message)s',
						datefmt='%m/%d/%Y %I:%M:%S %p')

	logging.getLogger('boto').setLevel(logging.CRITICAL)
	logging.info('vmesh logging %d.%d.%d starting (python %d.%d.%d, timestamp %d)' % (version + sys.version_info[:3] + (time.time(),)))
	logging.debug('argv: %s' % args.safeargv)


if __name__ == '__main__':
	setup_logging()
	peers.register_node()
	peers.purge_old_peers()
	if args.local:
		peers.print_hosts()

