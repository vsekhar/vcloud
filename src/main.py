import serversocket
import asyncore
import options

if __name__ == '__main__':
	svr = serversocket.ServerSocket('', 10240)
	while(1):
		# handle some IO
		asyncore.poll(0)
		
		# read/write kernel msg queues
		
		# periodic peer management
			# request updated peer lists from peers
			# cull stale peer entries
			# spawn new connections if needed

