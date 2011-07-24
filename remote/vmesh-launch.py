#!/usr/bin/env python

version = (1,0,0)

import args
import peers
import serversocket

if __name__ == '__main__':
	if args.reset:
		peers.clear_hosts()
	else:
		# main run loop
		while(1):
			peers.purge_old_peers()
			peers.update_node()
			peer_deficit = args.connections - len(serversocket.connections)
			if peer_deficit > 0:
				for peer in peers.new_peers(num=peer_deficit):
					serversocket.new_connection((peer.name, int(peer.port)))
			if args.local:
				peers.print_peers()
				if raw_input().strip() == 'q':
					break

