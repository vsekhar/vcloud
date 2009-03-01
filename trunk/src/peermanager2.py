from __future__ import with_statement
import xmlrpc.server
import xmlrpc.client
import queue
import threading
import time
import random

#import orgqueues
import timedlist
from addressedrequesthandler import AddressedXMLRPCRequestHandler

peer_timeout = 60

class PeerManager:
    def __init__(self, address_port, firstpeer, peers_to_maintain, inqueue, outqueue):
        self.id = random.random()
        self.inqueue = inqueue
        self.outqueue = outqueue
        self.connections = timedlist.TimedList()
        self.aware = timedlist.TimedList()
        if firstpeer is not None:
            self.aware.touch(firstpeer)
        self.peers_to_maintain = peers_to_maintain
        
        self.XMLServer = xmlrpc.server.SimpleXMLRPCServer(
                                address_port,
                                AddressedXMLRPCRequestHandler,
                                logRequests=False)
        self.XMLServer.register_function(self.X_join)
        self.XMLServer.register_function(self.X_message)
        self.XMLServer.register_function(self.X_break)
        self.XMLServer.register_function(self.X_getpeers)
        self.XMLServerThread = threading.Thread(target=self.XMLServer.serve_forever)
        self.XMLServerThread.setDaemon(True)
        self.XMLServerThread.start()
        self.address, self.port = self.XMLServer.server_address
        
        self.peerupdater_thread = threading.Thread(target=self.PeerUpdater)
        self.peerupdater_thread.setDaemon(True)
        self.peerupdater_thread.start()
        
    def PeerUpdater(self):
        while True:
            # Delete peers if needed
            removed = self.connections.removeByAge(peer_timeout)
            for (h,p),v in removed:
                print("Removing: " + h + ":" + str(p))
                uri = "http://" + host + ":" + str(port)
                peer = xmlrpc.client.ServerProxy(uri)
                try:
                    peer.X_break(port)
                    self.aware.touch((h,p))
                except IOError:
                    pass
            
            # Join with peers if needed
            if len(self.connections) < self.peers_to_maintain:
                if len(self.aware) > 0:
                    host,port = self.aware.poprandom()
                    uri = "http://" + host + ":" + str(port)
                    peer = xmlrpc.client.ServerProxy(uri)
                    try:
                        if peer.X_join(self.id, self.port):
                            self.connections.touch((host, port))
                    except IOError:
                        pass
                elif len(self.connections) > 0:
                    host,port = self.connections.getrandom()
                    uri = "http://" + host + ":" + str(port)
                    peer = xmlrpc.client.ServerProxy(uri)
                    try:
                        peers = peer.X_getpeers(self.port)
                        self.aware.touchlist(peers)
                    except IOError:
                        self.connections.remove((host, port))
                        self.aware.touch((host, port))
                else:
                    pass
            
            # send messages
            try:
                while True:
                    try:
                        host,port = self.connections.getrandom()
                        msg = self.outqueue.get_nowait()
                        uri = "http://" + host + ":" + str(port)
                        peer = xmlrpc.client.ServerProxy(uri)
                        try:
                            if peer.X_message(msg, self.port):
                                pass
                            else:
                                self.outqueue.put(msg)
                        except IOError:
                            self.connections.remove((host, port))
                            self.aware.touch((host, port))
                            self.outqueue.put(msg)
        
                    except IndexError:
                        pass
            except queue.Empty:
                pass 

            time.sleep(1+random.random())
        
    # Protocol functions (called via XML-RPC)
    
    def X_join(self, id, port, host):
        if id == self.id:
            return False
        elif self.connections.has((host, port)):
            print("Rejoining: " + host + ":" + str(port))
            return True
        elif len(self.connections) < self.peers_to_maintain:
            self.connections.touch((host, port))
            print("Joining: " + host + ":" + str(port))
            return True
        else:
            return False
    
    def X_message(self, msg, port, host):
        if self.connections.has((host, port)):
            self.inqueue.put(msg)
            self.connections.touch((host, port))
            return True
        else:
            return False
    
    def X_break(self, port, host):
        if self.connections.has((host, port)):
            self.connections.remove((host,port))
            print("Breaking: " + host + ":" + str(port))
            return True
        else:
            return False
    
    def X_getpeers(self, port, host):
        print("Sending peers to: " + host + ":" + str(port))
        return self.connections.getlist()
    
    