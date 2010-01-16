'''
Created on 2009-12-29

Asyncore/asynchat wrapped sockets, no threading
'''

import queue
import datetime
import options

from threading import Thread, Event
from peermanager import peers
from serversocket import ServerSocket

class VMesh():
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.server_socket = ServerSocket(options.map.bind_address, options.map.bind_port, self)
        self.address_port = self.server_socket.address_port
        self.address = self.address_port[0]
        self.port = self.address_port[1]
        self.add_seeds(options.map.seeds)
        self.loop_thread = Thread(target=self.loop, name='MeshServer_loop')
        self.finished = Event()
    
    def add_seeds(self, seeds):
        errors = []
        for seed in seeds:
            addr, _, port_str = seed.partition(':')
            try:
                port = int(port_str)
            except ValueError:
                errors.append(seed)
                continue
            peers.add_peer((addr, port))

        if len(errors) > 0:
            err = 'Bad seeds: ' + errors[0]
            for seed in errors[1:]:
                err.append(', ' + seed)
            raise Exception(err)
    
    def start(self):
        self.loop_thread.start()
        self.kernel.start()
    
    def cancel(self):
        self.kernel.cancel()
        self.finished.set()
        peers.close_all()
        self.server_socket.handle_close()
    
    def join(self):
        self.kernel.join()
        self.loop_thread.join()
    
        
    def get_stats(self):
        return "stats not implemented"
    
    def handle_incoming_message(self, msg):
        self.kernel.put_message(msg)
            
    def loop(self):
        fetch_peers_timestamp = datetime.datetime.utcnow()
        add_connection_timestamp = fetch_peers_timestamp
        cull_peers_timestamp = fetch_peers_timestamp
        
        while peers.socket_count():
            peers.poll_sockets(timeout=0)
            
            # get and send all the msgs the kernel can give us
            msgs = self.kernel.get_messages(None)
            connections = peers.get_random_connection_list(len(msgs))
            if len(connections) == 0:
                # no connections
                self.kernel.put_messages(msgs)
            else:
                for (msg, connection) in zip(msgs, connections):
                    msg_hdr = 'm ' + str(len(msg)) + '\n'
                    msg_data = msg_hdr.encode('ascii') + msg
                    connection.push(msg_data)

            # perform peer maintenance tasks
            now = datetime.datetime.utcnow()
            if now - fetch_peers_timestamp > datetime.timedelta(seconds=5):
                peers.fetch_peers(options.map.peers)
                fetch_peers_timestamp = now
            if now - add_connection_timestamp > datetime.timedelta(seconds=5):
                peers.add_connection_from_peers(options.map.connections, server=self)
                add_connection_timestamp = now
            if now - cull_peers_timestamp > datetime.timedelta(seconds=5):
                peers.cull_peers(round(options.map.peers * 0.9))
                cull_peers_timestamp = now
