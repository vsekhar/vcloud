'''
Created on 2010-10-11
'''

import configparser

def load_value(config, name, section, d):
	d[name] = config.get(section, name)

def read_config(filename):
	config = configparser.ConfigParser()
	config.read(filename)
	
	# vmesh
	d1 = dict()
	d1['connections'] = config.getint('vmesh', 'connections')
	d1['bind_address'] = config.get('vmesh', 'bind_address')
	d1['bind_port'] = config.getint('vmesh', 'bind_port')
	d1['seeds'] = eval(config.get('vmesh', 'seeds'))
	d1['peers'] = config.getint('vmesh', 'peers')
	d1['peer_timeout'] = config.getint('vmesh', 'peer_timeout')

	d1['verbosity'] = config.getint('vmesh', 'verbosity')

	d1['kernel'] = config.get('vmesh', 'kernel')
	d1['kernel_path'] = config.get('vmesh', 'kernel_path')
	
	# kernel
	d2 = dict(config.items(d1['kernel']))
	
	return d1,d2

# for testing, invoke from command line with config file as first argument
if __name__ == '__main__':
	from sys import argv, path
	d1, d2 = read_config(argv[1])
	print(d1, d2)
	newpath = path[0] + "/" + d1['kernel_path']
	path.insert(1,newpath)
	import_str = 'import ' + d1['kernel'] + ' as kernel'
	exec(import_str)
	kernel.greet()


