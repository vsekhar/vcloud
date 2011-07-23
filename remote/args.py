import argparse, sys

parser = argparse.ArgumentParser(description='vmesh-init.py: initial package script')
parser.add_argument('--local', default=False, action='store_true', help='run in local/debug mode (log to screen, no AWS metadata)')
parser.add_argument('--log', type=str, help='log file')
parser.add_argument('--domain', type=str, default='vmesh', help='SimpleDB domain to use for vmesh metadata (default=vmesh)')
parser.add_argument('--access-key', type=str, help='access key')
parser.add_argument('--secret-key', type=str, help='secret key')
parsed_args = parser.parse_args()

# allow access using 'args.access_key', etc.
sys.modules[__name__].__dict__.update(parsed_args.__dict__)

def hider(x):
	if x.startswith('--access-key') or x.startswith('--secret-key'):
		return x.partition('=')[0] + '=[hidden]'
	else:
		return x
safeargv = map(hider, sys.argv)

