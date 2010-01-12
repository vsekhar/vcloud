'''
Created on 2009-12-29

Asyncore/asynchat wrapped sockets, no threading
'''

import socket
import queue
import asyncore
import datetime
import options

from threading import Thread, Event
from peermanager import peers

class MeshServer(asyncore.dispatcher):
    
    timeout = 0.5

    def __init__(self, inqueue, outqueue):
        self.inqueue = inqueue
        self.outqueue = outqueue
        self.requested_address = (options.map.bind_address, options.map.bind_port)

        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr = (options.map.bind_address, options.map.bind_port)
        self.bind(self.addr)
        self.address = self.socket.getsockname()
        self.listen(1)
        
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
    
    def cancel(self):
        self.finished.set()
        peers.close_all()
        self.loop_thread.join()
        self.handle_close()
    
    def handle_accept(self):
        if not self.finished.is_set():
            (sock, addr) = self.accept()
            print('Received connection (%s:%s)' % (addr[0], addr[1]))
            peers.accept_connection(sock=sock, addr=addr, server=self)
    
    def handle_close(self):
        self.close()
    
    def get_stats(self):
        return "stats not implemented"
            
    def loop(self):
        fetch_peers_timestamp = datetime.datetime.utcnow()
        add_connection_timestamp = datetime.datetime.utcnow()
        cull_peers_timestamp = datetime.datetime.utcnow()
        
        while peers.socket_count():
            peers.poll_sockets(timeout=0)
            try:
                while 1:
                    msg = self.outqueue.get_nowait()
                    try:
                        random_channel = peers.get_random_connection()
                        msg_hdr = 'm ' + str(len(msg)) + '\n'
                        msg_data = msg_hdr.encode('ascii') + msg
                        random_channel.push(msg_data)
                    except (IndexError, KeyError):
                        # no connections
                        self.inqueue.put(msg)
            except queue.Empty:
                pass

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
