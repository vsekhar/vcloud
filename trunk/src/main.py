'''
Created on 2009-12-30
'''
import vmesh
import options
import traceback
import mockkernel

from util.print import print_addresses
from peermanager import peers

def main():
    options.parse_cmd_line()

    k = mockkernel.Kernel('mockkernel')
    v = vmesh.VMesh(k)
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
                print_addresses(peers.get_connections(None))
            
            # print list of peers
            elif command == 'p':
                print_addresses(peers.get_peers())
            
            # print stats
            elif command == 's':
                print('Connections: %s (target: %s)'
                      % (len(peers.socket_map), options.map.connections))
                print('Peers: %s' % len(peers.peer_map))
            
            # reset connections
            elif command == 'r':
                peers.close_all()
            
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
    
    v.cancel()
    v.join()


if __name__ == '__main__':
    main()
    