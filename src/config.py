import configparser

# one list for each section, storing value names, type, and default

params = [
	(
		'vcloud',
		[
			('aws_access_key_id', str, ''),
			('aws_secret_key', str, ''),
			('nodes', int, 1)
		]
	),
	(
		'vmesh',
		[
			('connections', int, 3),
			('peers', int, 100),
			('peer_timeout', int, 30),
		]
	),
	(
		'kernel',
		[
			('max_population', int, 0),
			('max_memory', int, 1024),
			('max_cpu_per_org', int, 10)
		]
	)
]

def read_config(filename):
	config = configparser.ConfigParser()
	config.read(filename)
	
	ret = dict()
	for (sec_name, sec_params) in params:
		section_dict = dict()
		for (param_name, typ, default) in sec_params:
			try:
				section_dict[param_name] = typ(config.get(sec_name, param_name))
			except configparser.NoOptionError:
				section_dict[param_name] = default
		ret[sec_name] = section_dict

	return ret

if __name__ == '__main__':
	# print parsed dict for testing: python3 <scriptname> <configfile>
	import sys
	print(read_config(sys.argv[1]))

