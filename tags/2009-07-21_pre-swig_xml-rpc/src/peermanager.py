# Library imports
from __future__ import with_statement
import xmlrpc.server
import xmlrpc.client
import threading
import time
import random

# My imports
from addressedrequesthandler import AddressedXMLRPCRequestHandler
import peerproxy

# User constants
peer_timeout = 60
peer_max_errors = 3
peers_to_maintain = 3

class Peer:
    def __init__(self, addr_port, t=time.time(), errors=0):
        self.addr_port = addr_port
        self.time = t
        self.errors = errors
        
    def __repr__(self):
        return "P"+str(self.addr_port)+"t"+str(time.time()-self.time)+"e"+str(self.errors)
    
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
                    peer = self.manager.random_peer() #blocking
                    proxy = peerproxy.PeerProxy(peer)
                    if proxy.do.X_message(org, self.manager.port):
                        self.manager.peer_ok(peer)
                        break
                except (IOError, socket.error):
                    self.manager.peer_error(peer)
                    self.outqueue.put(org)

class PeerManager:
    def __init__(self, addr_port, inqueue, outqueue, heartbeat_func, first_peer=None):
        self.connections = dict()
        self.aware = dict()
        self.lock = threading.RLock()
        self.inqueue = inqueue
        self.outqueue = outqueue
        self.heartbeat_func = heartbeat_func
        self.id = random.random()
        
        # XML RPC Server
        self.XMLServer = xmlrpc.server.SimpleXMLRPCServer(
                                                          addr_port,
                                                          AddressedXMLRPCRequestHandler,
                                                          logRequests=False)
        self.XMLServer.register_function(self.X_message)
        self.XMLServer.register_function(self.X_getpeers)
        self.XMLServer.register_function(self.X_join)
        self.XMLServer.register_function(self.X_getinfo)
        self.address, self.port = self.XMLServer.server_address
        
        self.XMLServer_thread = threading.Thread(target=self.XMLServer.serve_forever, name="XMLThread")
        self.XMLServer_thread.setDaemon(True)
        self.XMLServer_thread.start()
        
        # Join first peer
        if first_peer is not None:
            proxy = peerproxy.PeerProxy(first_peer)
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
        
        if False:
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
            print("ERROR: Selfing out (should never happen, check IP vs. domain names)")
            return "SELF"
        host, port = addr_port
        with self.lock:
            if addr_port in self.connections:
                print("WARNING: Accepting *re-join* from: ", addr_port)
                return "OK"
            elif len(self.connections) < peers_to_maintain:
                self.connections[addr_port] = Peer(addr_port)
                print("Accepting new peer: ", addr_port)
                return "OK"
            else:
                self.aware[addr_port] = Peer(addr_port)
                return "NO"
    
    def peer_error(self, addr_port):
        """Report that an error was experienced connecting to a peer (ignore if
        peer isn't currently connected"""
        try:
            with self.lock:
                self.connections[addr_port].error()
        except KeyError:
            pass
    
    def peer_ok(self, addr_port):
        """Report that a peer was accessed successfully (ignore if peer isn't
        currently connected"""
        try:
            with self.lock:
                self.connections[addr_port].ok()
        except KeyError:
            pass
    
    def random_peer(self):
        "Gets a peer from the connections list, blocks until there is one"
        while True:
            with self.lock:
                keys = list(self.connections.keys())
            if len(keys):
                return random.choice(keys)
            time.sleep(random.random() / 2.0)
    
    def _getpeers(self):
        return self._getconnections().union(self._getawares())

    def _getconnections(self):
        with self.lock:
            return set(self.connections)
    
    def _getawares(self):
        with self.lock:
            return set(self.aware)
        
    def stop(self):
        "Stops the manage_loop and kill_loop threads"
        self.stop = True
    
    def kill_loop(self):
        "Kill connections that have timed-out or have too many errors"
        while not self.stop:
            time.sleep(random.random())
            with self.lock:
                # kill dead connections
                for key in list(self.connections.keys()):
                    if self.connections[key].timedout():
                        print("Timeout: ", self.connections[key])
                        self.aware[key] = self.connections[key]
                        del self.connections[key]
                    elif self.connections[key].erroredout():
                        print("Errored out: ", self.connections[key])
                        del self.connections[key]
                
                # kill dead awares
                for key in list(self.aware.keys()):
                    if self.aware[key].erroredout():
                        del self.aware[key]
            
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
            proxy = peerproxy.PeerProxy(addr_port)
            try:
                # careful not to hold the lock while calling X_join
                response = proxy.do.X_join(self.id, self.port) 
                if response == "OK":
                    # remote peer accepted join, so add to connection
                    # and remove from aware list
                    with self.lock:
                        self.connections[addr_port] = self.aware[addr_port]
                        self.connections[addr_port].ok()
                        del self.aware[addr_port]
                    return
                elif response == "SELF":
                    print("ERROR: self'd out when attempting to join: ", addr_port)
                    with self.lock:
                        del self.aware[addr_port]
                else:
                    # if remote peer refuses, do nothing
                    # NB: this is not a peer error, nor a reason to remove
                    #     the peer from the aware list
                    pass

            except (IOError, socket.error):
                with self.lock:
                    self.aware[addr_port].error()
                
    def resupply_from_connections(self):
        with self.lock:
            keys = list(self.connections.keys())
        if not len(keys):
            return
        addr_port = random.choice(keys)
        proxy = peerproxy.PeerProxy(addr_port)
        try:
            peers = proxy.do.X_getpeers(self.port)
            for newpeer in peers:
                newpeer_tuple = tuple(newpeer)
                with self.lock:
                    self.aware[newpeer_tuple] = Peer(newpeer_tuple)

            # Mark ok, and ignore if connection was killed
            try:
                with self.lock:
                    self.connections[addr_port].ok()
            except KeyError:
                pass
        except (IOError, socket.error):
            # Mark error, and ignore if connection was killed
            try:
                with self.lock:
                    self.connections[addr_port].error()
            except KeyError:
                pass
                
    def resupply_loop(self):
        "Resupply connections list from awarelist and by asking other peers"
        while not self.stop:
            if len(self.connections) < peers_to_maintain:
                self.resupply_from_aware()
            if len(self.connections) < peers_to_maintain:
                self.resupply_from_connections()
            time.sleep(random.random())
    
    #
    # XML-RPC functions (called remotely, 'host' param is added by AddressedXMLRPCRequestHandler)
    #
    
    def X_message(self, msg, port, host):
        if self.acceptable((host, port)):
            self.inqueue.put(msg)
            return True
        else:
            return False
    
    def X_getpeers(self, port, host):
        "Return peers but not the requester"
        peers = self._getpeers()
        requester = {(host, port)}
        return list(peers.difference(requester))
    
    def X_join(self, id, port, host):
        return self._join(id, (host, port))
    
    def X_getinfo(self, host):
        ret = dict()
        ret["outqueue_size"] = self.outqueue.qsize()
        ret["inqueue_size"] = self.inqueue.qsize()
        ret["connections"] = list(self._getconnections())
        ret["awares"] = list(self._getawares())
        ret["heartbeat_age"] = time.time() - self.heartbeat_func()
        return ret
    
