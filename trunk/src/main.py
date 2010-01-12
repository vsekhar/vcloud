'''
Created on 2009-12-30
'''
import pymesh
import peermaps
import options
import traceback

from util.print import print_addresses

def main():
    options.parse_cmd_line()
    p = pymesh.PyMesh()
    print(p.server.address)
    p.start()
    
    # server command loop
    while 1:
        command = input('>>> ')
        command = command.strip()
        try:
            if command == 'x':
                p.cancel()
                exit(0)
                
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
            
            # no-op
            elif command == '':
                pass
            
            # unknown command
            else:
                print('Unknown command')
        except Exception:
            traceback.print_exc()


if __name__ == '__main__':
    main()
    