'''
Augments asyncore's socket_map with functionality to handle a peer_map as well,
allowing us to track not just current connections, but peers we have 'seen'
and may need to contact again in the future. Also handles multi-threading
'''

import datetime
import asyncore
import socket
import random
import options
from connectionhandler import ConnectionHandler
from util.mergedict import merge_dict
from threading import RLock
    
class Empty(Exception):
    pass

class PeerManager():
    def __init__(self):
        self.peers = {}
        self.peers_lock = RLock()
        self.sockets = asyncore.socket_map
        self.sockets_lock = RLock()
    
    def make_deltas(self, dict):
        dict = dict.copy()
        now = datetime.datetime.utcnow()
        for k in dict:
            dict[k] = now-dict[k]
        return dict
    
    def socket_count(self):
        with self.sockets_lock:
            return len(self.sockets)
    
    def update_peers(self, peers_dict):
        """Refresh peers list with data from peers_dict by adding peers we don't
        already know about, and moving up timestamps where appropriate for peers
        we do already know about"""
        
        if len(peers_dict) == 0:
            return # prevent unnecessary lock acquisitions

        with self.sockets_lock:
            socket_addresses = [(i.addr[0], i.remote_server_port)
                                for i in self.sockets.values() if i.connected]
        with self.peers_lock:
            now = datetime.datetime.utcnow()
            for (k,delta) in peers_dict.items():
                
                # if we have better information (by being directly connected
                # to the peer in question) or if the information we got is stale
                # then ignore it
                if k in socket_addresses:
                    continue
                if delta > datetime.timedelta(seconds=options.map.peer_timeout):
                    continue
                
                # if we have this peer already, move up the time stamp
                # if we don't, add it using the time stamp sent to us
                try:
                    new_timestamp = max(self.peers[k], now - delta)
                except KeyError:
                    new_timestamp = now - delta
                self.peers[k] = new_timestamp

    def get_peers(self):
        "returns a list of peers as (remote_addr, remote_server_port)"
        with self.peers_lock:
            return self.make_deltas(self.peers)
    
    def get_connections(self, excl_addr):
        "returns a list of sockets as (remote_addr, remote_server_port)"
        with self.sockets_lock:
            l = [((socket.addr[0], socket.remote_server_port), socket.timestamp)
                    for socket in self.sockets.values()
                    if socket.connected
                    and socket.remote_server_port is not None
                    and (socket.addr[0], socket.remote_server_port) != excl_addr]
            return self.make_deltas(dict(l))
    
    def get_random_connection(self):
        return self.get_random_connection_list(1)[0]

    def get_random_connection_list(self, n=1):
        with self.sockets_lock:
            l = [i for i in self.sockets.values() if i.connected]
        try:
            return [random.choice(l) for _ in range(n)]
        except IndexError:
            # empty source list, so return empty random list
            return []
    
    def get_peers_and_connections(self, excl_addr):
        return merge_dict(self.get_peers(), self.get_connections(excl_addr))
    
    def poll_sockets(self, timeout=0):
        with self.sockets_lock:
            return asyncore.poll(timeout, self.sockets)

    def del_peer(self, addr):
        try:
            with self.peers_lock:
                del self.peers[addr]
        except KeyError:
            pass
    
    def add_peer(self, addr, timestamp=None):
        if timestamp == None:
            timestamp = datetime.datetime.utcnow()
        with self.peers_lock:
            try:
                self.peers[addr] = max(self.peers[addr], timestamp)
            except KeyError:
                self.peers[addr] = timestamp
    
    def accept_connection(self, sock, addr, server):
        with self.sockets_lock:
            if options.map.verbose:
                print('accepting connection from (%s:%s)' % addr)
            ConnectionHandler(sock=sock,
                              peermanager=self,
                              server=server,
                              direction='in')
    
    def fetch_peers(self, n):
        with self.peers_lock:
            if n > len(self.peers):
                try:
                    random_channel = self.get_random_connection()
                    msg = 'p\n'
                    random_channel.push(msg.encode('ascii'))
                except IndexError:
                    pass                    
    
    def add_connection_from_peers(self, connections_target, server):
        count = 0
        with self.sockets_lock:
            socketcount = len(self.sockets)
        if socketcount >= connections_target:
            return count
        try:
            for _ in range(connections_target - socketcount):
                try:
                    addr, timestamp = self.pop_oldest_peer()
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect(addr)
                    if options.map.verbose:
                        print('Making connection (%s:%s)' % addr)
                    with self.sockets_lock:
                        ConnectionHandler(sock=sock,
                                          peermanager=self,
                                          server=server,
                                          direction='out')
                    ++count
                except socket.error:
                    # put peer back with the same timestamp
                    self.add_peer(addr, timestamp)
        except Empty:
            # no more peers (raised by pop_oldest_peer())
            pass
        
        return count

    
    def pop_oldest_peer(self):
        with self.peers_lock:
            try:
                peer = min(self.peers.items(), key=lambda x:x[1])
            except ValueError:
                raise Empty
            else:
                del self.peers[peer[0]]
                return peer
    
    def cull_peers(self, n):
        """Remove peer entries, starting from the oldest, until we have at most
        'n' peers and no peer is more stale than the peer timeout value"""
         
        with self.peers_lock:
            l = list(self.peers.items())
            l.sort(key=lambda a:a[1])
            to_delete = {}
            if n < len(self.peers):
                for i in range(len(self.peers)-n):
                    to_delete[l[i][0]] = 0

            timeout = options.map.peer_timeout

            delta = datetime.timedelta(seconds=timeout)
            oldest_time = datetime.datetime.utcnow() - delta
            for (addr, time) in l:
                if time < oldest_time:
                    if options.map.verbose:
                        print('found peer to cull: %s:%s' % addr)
                    to_delete[addr] = 0
            
            # do the deletions
            for addr in to_delete.keys():
                del self.peers[addr]

    def close_all(self, listening_sockets_as_well=False):
        with self.sockets_lock:
            l = list(self.sockets.values())
            for i in l:
                try:
                    i.close_when_done()
                except AttributeError:
                    if listening_sockets_as_well:
                        i.close()
    
peers = PeerManager()