import threading
import xmlrpc.client
import xmlrpc.server
import time
import random

import orgqueues
from addressedrequesthandler import MyXMLRPCRequestHandler

class PeerError(Exception): pass

class Peer:
    def __init__(self, peers):
        self.peers = peers
    
    def __enter__(self):
        self.address, self.port, self.errors = peers.pop()
        return self.address, self.port, self.errors
    
    def __exit__(self, type, value, traceback):
        if type is PeerError:
            self.errors = self.errors + 1
            peers.add((address, port, errors))
            return True
        else:
            peers.add((address, port, errors))
            return False


class Peers:
    def __init__(self):
        self.peers = {}
        self.lock = threading.RLock()
    
    def add(self, address, port, errors):
        with self.lock:
            if not (address,port) in self.peers or errors > self.peers[(address, port)]:
                self.peers[(address, port)] = errors 
        
    def add_new(self, address_port):
        with self.lock:
            if not address_port in self.peers:
                self.peers[address_port] = 0

    def pop(self):
        with self.lock:
            ((address, port), errors) = self.peers.popitem()
            return (address, port, errors)
    
    def get_all(self):
        with self.lock:
            return list(self.peers.items())
    
    def __len__(self):
        with self.lock:
            return len(peers)


class PeerManager:
    def __init__(self, peers_to_maintain, first_peer=None):
        
        # setup peers lists
        self.peers_to_maintain = peers_to_maintain
        self.connected = Peers()
        self.aware = Peers()
        if first_peer:
            self.aware.add_new(first_peer)
            
        # setup and start XML-RPC server
        self.XML_server = xmlrpc.server.SimpleXMLRPCServer(
                                address_port,
                                MyXMLRPCRequestHandler,
                                logRequests=False)
        self.XML_server.register_function(self.X_remote_transfer)
        self.XML_server.register_function(self.X_get_peers)
        self.XML_server_thread = threading.Thread(target=self.XML_server.serve_forever)
        self.XML_server_thread.setDaemon(True)
        self.XML_server_thread.start()
        
        # start peerslist loop
        self.stop = False
        self.thread = threading.Thread(target=self.mainloop)
        self.thread.setDaemon(True)
        self.thread.start()
            
    def X_remote_transfer(self, org, port, host):
        self.aware.add_new((host, port))
        try:
            orgqueues.inqueue.put(org)
            return True
        except:
            return False
        
    def X_get_peers(self, port, host):
        self.aware.add_new((host, port))
        peers = self.connected.get_all()
        filtered_peers = [(x,y) for x,y in peers
                       if not y.learned_from == (host, port)
                       and not x == (host, port)]
        return filtered_peers
    
    def stop(self):
        self.stop = True
        
    def mainloop(self):
        while not self.stop:
            if len(self.connected) < self.peers_to_maintain:
                try:
                    self.connected.add(self.aware.pop())
                    if not key in self.connected:
                        self.connected[key] = peer
                except KeyError:
                    # don't have any peeps
                    pass
            sleep(random.random())