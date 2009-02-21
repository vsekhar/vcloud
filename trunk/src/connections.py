from __future__ import with_statement
import threading
import random
import sys

class Empty(BaseException):
    pass

class Peer:
    def __init__(self, learned_from):
        self.senderrors = 0
        self.learned_from = learned_from
    
    def senderror(self):
        self.senderrors = self.senderrors+1
        
    def ok(self):
        self.senderrors = 0
    
    def __gt__(self, other):
        return self.senderrors > other.senderrors
    
class ConnectionsManager:
    def __init__(self, timeout):
        self.connections = {}
        self.awareness = {}
        self.connections_lock = threading.RLock()
        self.awareness_lock = threading.RLock()
        self.timeout = timeout
        self.max_errors = 3
        self.stale_collector_loop = threading.Thread(target=self.stale_collector)
        self.stale_collector_loop.setDaemon(True)
        self.stale_collector_loop.start()
    
    def aware(self, address):
        with self.awareness_lock:
            try:
                self.awareness[address].update()
            except KeyError:
                self.awareness[address] = Peer(address)
    
    def aware_peer(self, peer):
        with self.awareness_lock:
            self.awareness[peer.address_port] = peer
    
    def aware_dict(self, new_peers, new_learned_from):
        with self.awareness_lock:
            for key in new_peers:
                p = new_peers[key]
                p.learned_from = new_learned_from
                self.awareness[key] = p

    def update(self, address):
        with self.connections_lock:
            if address in list(self.connections.keys()):
                self.connections[address].update()
    
    def connection_error(self, address):
        with self.connections_lock:
            try:
                self.connections[address].senderror()
            except KeyError:
                pass
    
    def connection_ok(self, address):
        with self.connections_lock:
            self.connections[address].ok()
            
    def get_random_connection(self):
        with self.connections_lock:
            if len(self.connections) == 0:
                raise Empty
            return random.choice(list(self.connections.keys()))
        
    def get_all_connections(self):
        with self.connections_lock:
            return list(self.connections.items())
    
    def add_peer(self, address, peer_record):
        with self.connections_lock:
            self.connections[address] = peer_record
        print("Adding connection: ", address, " learned from ", peer_record.learned_from)
    
    def add(self):
        try:
            with self.awareness_lock:        
                with self.connections_lock:
                        stop = False
                        while True:
                            key = random.choice(self.awareness)
                            peer = self.awareness[key]
                            if key not in self.connections:
                                self.add_peer(key, peer)
                                break
        except KeyError:
            return False
        except IndexError:
            return False
        return True
        
    def drop_peer(self, peer):
        with self.connections_lock:
            del self.connections[peer]
        print("Dropping connection: ", peer)
    
    def drop(self):
        with self.connections_lock:
            worst_peer = max(self.connections.values())
            if worst_peer.senderrors < self.max_errors:
                self.aware
            del self.connections[worst_peer.address_port]
    
    def stale_collector(self):
        while True:
            connections_to_delete = []
            with self.connections_lock:
                for k,v in self.connections.items():
                    if v.senderrors > self.max_errors:
                        self.drop_peer(k)
                    
            time.sleep(random.random())
    
    def empty(self):
        with self.connections_lock:
            return len(self.connections) == 0
    
    def count(self):
        with self.connections_lock:
            return len(self.connections)