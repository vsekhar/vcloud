#!/usr/bin/python3

import options
import config

if __name__ == "__main__":
	options.parse_cmd_line()
	cfg = config.read_config(options.map.config_file)
	print(cfg)
	pass

