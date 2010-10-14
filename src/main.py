'''
Created on 2009-12-30
'''
import traceback

import options
import config
import kernel
#import mockkernel
import vmesh

from util.print import print_addresses

def main():
	options.parse_cmd_line()
	vmconfig, kconfig = config.read_config(options.map.config_file)
	if vmconfig['verbosity'] > 1:
		print(vmconfig, kconfig)

	k = kernel.Kernel(vmconfig['kernel_path'], vmconfig['kernel'], vmconfig['kernel_greeting'], kconfig)
	v = vmesh.VMesh(k, vmconfig)

	if vmconfig['verbosity'] > 1:
		nodes = list(k.listnodes())
		print(nodes)
		print('%d nodes' % len(nodes))

	print(v.address_port)
	v.start()
    
    # server command loop
	while 1:
		try:
		    command = input('>>> ')
		    command = command.strip()

		    if command == 'x':
		        break
		        
		    # print list of connections
		    elif command == 'c':
		        print_addresses(v.peermgr.get_connections(None))
		    
		    # print list of peers
		    elif command == 'p':
		        print_addresses(v.peermgr.get_peers())
		    
		    # print stats
		    elif command == 's':
		        print('Connections: %s (target: %s)'
		              % (len(v.peermgr.socket_map), vmconfig['connections']))
		        print('Peers: %s' % len(v.peermgr.peer_map))
		    
		    # reset connections
		    elif command == 'r':
		        v.peermgr.close_all()
		    
		    # no-op
		    elif command == '':
		        pass
		    
		    # unknown command
		    else:
		        print('Unknown command')

		except KeyboardInterrupt:
		    break
		except Exception:
		    traceback.print_exc()

	print("Terminating...")
	v.cancel()
	v.join()


if __name__ == '__main__':
    main()
    
