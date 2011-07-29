import logging
import sys
import time
import pwd
import os

import args

log = logging.getLogger('vmesh-launch')
log.setLevel(logging.DEBUG if args.debug else logging.INFO)
formatter = logging.Formatter(fmt='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# setup logging to file
userinfo = pwd.getpwuid(os.getuid())
if args.local:
	logfilepath = args.log # use current directory
else:
	logfilepath = userinfo.pw_dir + os.sep + args.log # user's home dir
logfile = open(logfilepath, 'a')
fh = logging.StreamHandler(stream=logfile) # don't use FileHandler since we have to redirect below
fh.setFormatter(formatter)
log.addHandler(fh)

# setup logging to console
sh = logging.StreamHandler()
sh.setFormatter(formatter)
log.addHandler(sh)

if not args.interactive:
	# no one is watching, so capture python exception errors and the like
	global old_stdout, old_stderr
	log.info('STDOUT and STDERR redirected to log file: %s' % logfile.name)
	old_stdout = sys.stdout
	old_stderr = sys.stderr
	sys.stdout = logfile
	sys.stderr = logfile

# boto is normally a bit too noisy
logging.getLogger('boto').setLevel(logging.WARNING)

# announce startup
log.info('### Vmesh starting (python %d.%d.%d, timestamp %d) ###' % (sys.version_info[:3] + (time.time(),)))
if args.debug:
	log.info('Debug logging mode enabled')
log.debug('Working directory: %s' % os.getcwd())
log.debug('sys.argv: %s', str(sys.argv))

