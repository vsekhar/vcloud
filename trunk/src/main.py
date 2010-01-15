'''
Created on 2009-12-30
'''
import pymesh
import peermanager
import options
import traceback

from util.print import print_addresses

def main():
    options.parse_cmd_line()
    p = pymesh.PyMesh()
    print(p.server.address_port)
    p.start()
    
    # server command loop
    while 1:
        try:
            command = input('>>> ')
            command = command.strip()

            if command == 'x':
                break
                
            # print list of connections
            elif command == 'c':
                print_addresses(peermaps.get_connections(None))
            
            # print list of peers
            elif command == 'p':
                print_addresses(peermaps.get_peers())
            
            # print stats
            elif command == 's':
                print('Connections: %s (target: %s)'
                      % (len(peermaps.socket_map), options.map.connections))
                print('Peers: %s' % len(peermaps.peer_map))
            
            # reset connections
            elif command == 'r':
                peermanager.peers.close_all()
            
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
    
    p.cancel()
    p.join()


if __name__ == '__main__':
    main()
    