import logging as _logging
import sys
import time

import args

# pull in names from logging module
pull_names = ['info', 'debug', 'critical', 'warning', 'error', 'getLogger', 'CRITICAL', 'INFO', 'DEBUG', 'WARNING', 'ERROR', 'basicConfig']
for name in pull_names:
	setattr(sys.modules[__name__], name, getattr(_logging, name))

# setup logging
if args.interactive:
	logfile = sys.stdout
else:
	logfile = open(args.log, 'a')
	old_stdout = sys.stdout
	old_stderr = sys.stderr
	sys.stdout = logfile
	sys.stderr = logfile

basicConfig(stream=logfile, level=DEBUG,
			format='%(asctime)s: %(message)s',
			datefmt='%m/%d/%Y %I:%M:%S %p')


getLogger('boto').setLevel(CRITICAL)
info('vmesh logging starting (python %d.%d.%d, timestamp %d)' % (sys.version_info[:3] + (time.time(),)))
debug('argv: %s' % args.safeargv)


