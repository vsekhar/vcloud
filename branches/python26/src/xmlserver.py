from __future__ import with_statement
import xmlrpc.server
import xmlrpc.client
import random
import queue
import threading
import time
import sys

import orgqueues
import connections
from addressedrequesthandler import MyXMLRPCRequestHandler 

connections_manager = connections.ConnectionsManager(30)

class VGPServer:
    def __init__(self, address_port, firstpeer, peers_to_maintain):
        if firstpeer:
            connections_manager.aware(firstpeer)
        self.peers_to_maintain = peers_to_maintain

        self.XML_server = xmlrpc.server.SimpleXMLRPCServer(
                                address_port,
                                MyXMLRPCRequestHandler,
                                logRequests=False)
        self.XML_server.register_function(self.X_remote_transfer)
        self.XML_server.register_function(self.X_get_peers)
        self.XML_server.register_function(self.X_mgr_get_peers)
        self.XML_server.register_function(self.X_mgr_add_peer)
        self.XML_server.register_function(self.X_mgr_get_queue_sizes)
        self.XML_server_thread = threading.Thread(target=self.XML_server.serve_forever)
        self.XML_server_thread.setDaemon(True)
        self.XML_server_thread.start()
        self.address, self.port = self.get_server_address()
        
        self.sender_thread = threading.Thread(target=self.run)
        self.sender_thread.setDaemon(True)
        self.sender_thread.start()
        
    def get_server_address(self):
        return self.XML_server.server_address
    
    def X_remote_transfer(self, organism, port, host):
        connections_manager.aware((host, port))
        try:
            orgqueues.inqueue.put(organism)
            return True
        except:
            return False
    
    def X_get_peers(self, port, host):
        connections_manager.aware((host, port))
        peers = connections_manager.get_all_connections()
        #print("Unfiltered: ", peers)
        filtered_peers = [(x,y) for x,y in peers
                               if not y.learned_from == (host, port)
                               and not x == (host, port)]
        #print("Filtered: ", filtered_peers)
        return filtered_peers
    
    def X_mgr_get_peers(self, host):
        return connections_manager.get_all_connections()
    
    def X_mgr_add_peer(self, new_peer, host):
        connections_manager.connect(new_peer)
    
    def X_mgr_get_queue_sizes(self, host):
        return (orgqueues.inqueue.size(), orgqueues.outqueue.size())
    
    def run(self):
        while True:
            # Transfer organisms (exception if none to transfer)
            try:
                org = orgqueues.outqueue.get_nowait()                
                try:
                    host, port = connections_manager.get_random_connection()
                    uri = "http://" + host + ":" + str(port)
                    peer = xmlrpc.client.ServerProxy(uri)

                    # Send orgs (if any pending) to random peers
                    try:
                        if peer.X_remote_transfer(org, self.port):
                                connections_manager.connection_ok((host, port))
                    except IOError as err:
                        connections_manager.connection_error((host, port))
                    
                except connections.Empty:
                    pass
            except queue.Empty:
                pass

            # Get more peers if needed
            if connections_manager.count() < self.peers_to_maintain:
                if not connections_manager.add():
                    try:
                        host, port = connections_manager.get_random_connection()
                        uri = "http://" + host + ":" + str(port)
                        peer = xmlrpc.client.ServerProxy(uri)
                        try:
                            new_peers = peer.X_get_peers(self.port)
                            #print("Received: ", new_peers)
                            connections_manager.aware_dict(new_peers, (host, port))
                            connections_manager.add()
                        except IOError as err:
                            connections_manager.connection_error((host, port))
                    except connections.Empty:
                        #print("No connections; listening...")
                        pass
            
            # Drop peers if needed
            elif connections_manager.count() > self.peers_to_maintain:
                connections_manager.disconnect()
    
            time.sleep(random.random()*2)
