# Library imports
from __future__ import with_statement
import xmlrpc.server
import xmlrpc.client
import queue
import threading
import time
import random

# My imports
from addressedrequesthandler import AddressedXMLRPCRequestHandler

# User constants
peer_timeout = 60
peer_max_errors = 3
peers_to_maintain = 3

class Peer:
    def __init__(self, addr_port, time=time.time(), errors=0):
        self.addr_port = addr_port
        self.time = time
        self.errors = errors
    
    def error(self):
        self.errors = self.errors + 1
    
    def ok(self):
        self.time = time.time()
        self.errors = 0
    
    def timedout(self):
        if time.time() - self.time > peer_timeout:
            return True
        else:
            return False
        
    def erroredout(self):
        if self.errors > peer_max_errors:
            return True
        else:
            return False
    
    def mash(self, newpeer):
        if not self.addr_port == newpeer.addr_port:
            raise Exception("Tried to mash peers without matching addresses/ports")
        if newpeer.time > self.time:
            self.time = newpeer.time
            self.errors = newpeer.errors

class Proxy:
    def __init__(self, addr_port):
        self.host, self.port = addr_port
        self.uri = "http://" + self.host + ":" + str(self.port)
        self.do = xmlrpc.client.ServerProxy(self.uri)

class Sender:
    def __init__(self, outqueue, manager):
        self.outqueue = outqueue
        self.manager = manager
        
        self.stop = False
        self.send_thread = threading.Thread(target=self.send_loop, name="send_thread")
        self.send_thread.setDaemon(True)
        self.send_thread.start()
    
    def stop(self):
        self.stop = True
    
    def send_loop(self):
        while not self.stop:
            org = self.outqueue.get() #blocking
            while True:
                try:
                    peer = self.manager.getpeer() #blocking
                    proxy = Proxy(peer.addr_port)
                    if proxy.do.X_message(org, self.manager.port):
                        peer.ok()
                        break
                except IOError:
                    peer.error()
                    self.outqueue.put(org)
                finally:
                    self.manager.returnpeer(peer)

class PeerManager:
    def __init__(self, addr_port, inqueue, outqueue, first_peer=None):
        self.connections = dict()
        self.aware = dict()
        self.lock = threading.RLock()
        self.inqueue = inqueue
        self.outqueue = outqueue
        self.id = random.random()
        
        # XML RPC Server
        self.XMLServer = xmlrpc.server.SimpleXMLRPCServer(
                                                          addr_port,
                                                          AddressedXMLRPCRequestHandler,
                                                          logRequests=False)
        self.XMLServer.register_function(self.X_message)
        self.XMLServer.register_function(self.X_getpeers)
        self.XMLServer.register_function(self.X_join)
        self.address, self.port = self.XMLServer.server_address
        
        self.XMLServer_thread = threading.Thread(target=self.XMLServer.serve_forever, name="XMLThread")
        self.XMLServer_thread.setDaemon(True)
        self.XMLServer_thread.start()
        
        # Join first peer
        if first_peer is not None:
            proxy = Proxy(first_peer)
            if proxy.do.X_join(self.id, self.port):
                with self.lock:
                    self.connections[first_peer] = Peer(first_peer)

        # Peer management threads
        self.stop = False
        self.resupply_thread = threading.Thread(target=self.resupply_loop, name="ResupplyThread")
        self.resupply_thread.setDaemon(True)
        self.resupply_thread.start()
        self.kill_thread = threading.Thread(target=self.kill_loop, name="KillThread")
        self.kill_thread.setDaemon(True)
        self.kill_thread.start()
        
        # Sender
        self.sender = Sender(self.outqueue, self)
        
        # Debug the locking
        self.heartbeat_thread = threading.Thread(target=self._heartbeat, name="HeartbeatThread")
        self.heartbeat_thread.setDaemon(True)
        self.heartbeat_thread.start()

    def _heartbeat(self):
        while True:
            with self.lock:
                print("Heartbeat")
            time.sleep(1)

    def acceptable(self, addr_port):
        "Checks whether receiving from a given peer is ok"
        with self.lock:
            if addr_port in self.connections:
                self.connections[addr_port].ok()
                return True
            else:
                self.aware[addr_port] = Peer(addr_port)
                return False
    
    def _join(self, id, addr_port):
        if id == self.id:
            print("Selfing out")
            return "SELF"
        host, port = addr_port
        with self.lock:
            if addr_port in self.connections:
                print("Joining: " + host + ":" + str(port))
                return "OK"
            elif len(self.connections) < peers_to_maintain:
                self.connections[addr_port] = Peer(addr_port)
                print("Joining: " + host + ":" + str(port))
                return "OK"
            else:
                self.aware[addr_port] = Peer(addr_port)
                return "NO"
    
    def returnpeer(self, peer):
        "Puts a peer back into the connections list"
        with self.lock:
            self.connections[peer.addr_port] = peer
    
    def getpeer(self):
        "Gets a peer from the connections list, blocks until there is one"
        while True:
            try:
                with self.lock:
                    k,v = self.connections.popitem()
                return v
            except KeyError:
                pass
            time.sleep(random.random() / 2.0)
    
    def _getpeers(self, addr_port):
        host,port = addr_port
        with self.lock:
            # return connection and awares, but NOT the requester
            c = self.connections
            a = self.aware
            requester = {(host, port)}
            return list(set(c).union(a).difference(requester))
        
    def stop(self):
        "Stops the manage_loop and kill_loop threads"
        self.stop = True
    
    def kill_loop(self):
        "Kill connections that have timed-out or have too many errors"
        while not self.stop:
            with self.lock:
                # kill dead connections
                for key in list(self.connections.keys()):
                    if self.connections[key].timedout():
                        self.aware[key] = self.connections[key]
                        del self.connections[key]
                    elif self.connections[key].erroredout():
                        del self.connections[key]
                
                # kill dead awares
                for key in list(self.aware.keys()):
                    if self.aware[key].erroredout():
                        del self.aware[key]

            time.sleep(random.random())
            
    def resupply_from_aware(self):

        # Get awares, filter out those already connected
        with self.lock:
            awares = set(self.aware.keys())
            newawares = awares.difference(self.connections) 
            delawares = awares.intersection(self.connections)

        # delete ones that are connected
        for addr_port in delawares:
            with self.lock:
                del self.aware[addr_port]

        # try to join, return on first successful join
        for addr_port in newawares:
            proxy = Proxy(addr_port)
            try:
                # careful not to hold the lock while calling X_join
                response = proxy.do.X_join(self.id, self.port) 
                if response == "OK":
                    # remote peer accepted join, so add to connection
                    # and remove from aware list
                    with self.lock:
                        self.connections[addr_port] = self.aware[addr_port]
                        del self.aware[addr_port]
                    return
                elif response == "SELF":
                    with self.lock:
                        del self.aware[addr_port]
                else:
                    # if remote peer refuses, do nothing
                    # NB: this is not a peer error, nor a reason to remove
                    #     the peer from the aware list
                    pass
            except IOError:
                with self.lock:
                    self.aware[addr_port].error()                    
                
    def resupply_from_connections(self):
        with self.lock:
            try:
                addr_port, peer = self.connections.popitem()
            except KeyError:
                return
        proxy = Proxy(addr_port)
        try:
            peers = proxy.do.X_getpeers(self.port)
            peer.ok()
            for newpeer in peers:
                newpeer_tuple = tuple(newpeer)
                with self.lock:
                    self.aware[newpeer_tuple] = Peer(newpeer_tuple)
        except IOError:
            peer.error()
        finally:
            with self.lock:
                self.connections[addr_port] = peer
                
    def resupply_loop(self):
        "Resupply connections list from awarelist and by asking other peers"
        while not self.stop:
            if len(self.connections) < peers_to_maintain:
                self.resupply_from_aware()
            if len(self.connections) < peers_to_maintain:
                self.resupply_from_connections()
            time.sleep(random.random())
    
    #
    # XML-RPC functions (called remotely)
    #
    
    def X_message(self, msg, port, host):
        if self.acceptable((host, port)):
            self.inqueue.put(msg)
            # print("Getting msg from: " + host + ":" + str(port))
            return True
        else:
            return False
    
    def X_getpeers(self, port, host):
        # print("Sending peers to: " + host + ":" + str(port))
        return self._getpeers((host,port))
    
    def X_join(self, id, port, host):
        return self._join(id, (host, port))
