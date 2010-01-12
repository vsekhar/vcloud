# Written by Stephen Weber
# stephen.t.weber@gmail.com

"""A load-balancing TCP/IP mesh interface"""

import threading
import socket
import sys

from repeattimer import RepeatTimer
from lockedsocket import LockedSocket
from sortedset import SortedSet
from peerlistentry import PeerListEntry, ple_from_strings
from connectionlistentry import ConnectionListEntry

def get_address(addrport):
    return addrport.split(':')[0]

def get_port(addrport):
    return int(addrport.split(':')[1])

class PyMesh(threading.Thread):

    id = 0

    def __init__(self, addrport, limit=3, kernel=None, seeds=[]):
        threading.Thread.__init__(self)
        self.addrport = addrport
        self.kernel = kernel
        self.myid = PyMesh.id
        PyMesh.id += 1
        self.connections = SortedSet()
        self.connections_lock = threading.RLock()
        self.limit_lock = threading.RLock()
        self.limit = limit
        self.peers = SortedSet()
        self.peers_lock = threading.RLock()
        self.add_peers(seeds)

    def run(self):
        """Primary thread section. Configures other threads, then listens for
        incoming connections."""
        lstn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            lstn.bind((get_address(self.addrport), get_port(self.addrport)))
            lstn.listen(1)
        except socket.error:
            print "Could not bind to requested address."
            return

        kernelthread = RepeatTimer(5.0, self.readkernel)
        kernelthread.start()

        janitor = RepeatTimer(0.1, self.cleanup_connections)
        janitor.start()

        pt_thread = RepeatTimer(30.0, self.periodic_tasks)
        pt_thread.start()

        while 1:
            try:
                (clnt, ap) = lstn.accept()
                print "received connection on %d" % ap[1]
                cmd = clnt.recv(2).strip()
                if cmd == 's':
                    clnt.send(repr(self))
                elif cmd == 'c':
                    self.connect_client(LockedSocket(clnt))
                elif cmd == 'l':
                    self.send_peerlist(LockedSocket(clnt))
                else:
                    print "main recv'd something else: %s " % cmd
            except socket.error as (errid, strerr):
                print "Error in main thread: %s" % strerr
        # after while exits
        print "Closing, cleaning up resources..."
        kernelthread.cancel()
        kernelthread.join()
        janitor.cancel()
        janitor.join()
        pt_thread.cancel()
        pt_thread.join()
        with self.connections_lock:
            for each in self.connections.list:
                each.close()

    def set_limit(self, newlimit):
        with self.limit_lock:
            self.limit = newlimit

    def is_underlimit(self):
        """Returns whether the number of connections is less than the
        specified soft limit."""
        result = False
        with self.connections_lock:
            num_connects = len(self.connections)
        with self.limit_lock:
            result = num_connects < self.limit
        return result

    def is_overlimit(self):
        """Returns whether the number of connections is greater than the
        specified soft limit."""
        result = False
        with self.connections_lock:
            num_connects = len(self.connections)
        with self.limit_lock:
            result = num_connects > self.limit
        return result

    def send_peerlist(self, client):
        message = ""
        success = False
        with self.peers_lock:
            message = str(self.peers)
        with self.connections_lock:
            if len(self.connections) > 0:
                if message != "":
                    message += '_'
                message += str(self.connections)
        with client.lock:
            try:
                client.socket.send(message)
            except socket.error:
                success = False
            else:
                print "[%s] Sent peers: %s" % (self.addrport, message)
                success = True
        return success

    def recv_peerlist(self, client):
        """Sends the "peerlist" command to the socket of a connected peer."""
        success = False
        with client.lock:
            try:
                client.socket.send('l')
            except socket.error:
                success = False
            else:
                success = True
        return success

    def request_peerlist(self, addrport):
        """Requests a peerlist from an unconnected peer that might not
        exist anymore."""
        success = False
        tempclient = LockedSocket()
        with tempclient.lock:
            try:
                tempclient.socket.connect((get_address(addrport),
                                       get_port(addrport)))
                tempclient.socket.send('l')
            except socket.error:
                success = False
            else:
                success = True
        return success

    def connect_client(self, client):
        """Connects incoming client socket and stores its information
        locally."""
        clientaddress = ""
        with client.lock:
            try:
                client.socket.send('c')
                clientaddress = client.socket.recv(22)
            except socket.error:
                success = False
            else:
                success = True
        if success:
            with self.peers_lock:
                if clientaddress in self.peers:
                    ple = self.peers.get_entry(clientaddress)
                    self.peers.remove_entry(ple)

            cle = ConnectionListEntry(clientaddress, client,
                                  self.kmf_factory())
            print "Connecting to client on %s" % clientaddress
            with self.connections_lock:
                self.connections.add_entry(cle)

    def seekpeer(self):
        """Attempts to connect to peers, using a list of peers that have been
        seen."""
        with self.connections_lock:
            connection_addresses = [each.addrport for each in
                                    self.connections.list]

        unconnected_peers = []
        with self.peers_lock:
            for each in self.peers.list:
                if each.addrport not in connection_addresses:
                    unconnected_peers.append(each)

        peersock = None
        connected = False
        addrport = None
        for peer in unconnected_peers:
            peersock = LockedSocket()
            with peersock.lock:
                try:
                    peersock.socket.connect((get_address(peer.addrport),
                                  get_port(peer.addrport)))
                    peersock.socket.send('c ')
                    resp = peersock.socket.recv(2).strip()
                    if resp == 'c':
                        peersock.socket.send(self.addrport)
                        addrport = peer.addrport
                        connected = True
                        break
                    else:
                        print "seekpeer recv'd something else: %s" % resp
                        peersock.socket.close()
                except socket.error:
                    pass    # should be logging errors
        if connected:
            with self.peers_lock:
                self.peers.remove_entry(self.peers.get_entry(addrport))

            cle = ConnectionListEntry(addrport, peersock,
                                          self.kmf_factory())
            with self.connections_lock:
                self.connections.add_entry(cle)

    def get_peers(self):
        success = False
        with self.peers_lock:
            if len(self.peers) > 0:
                oe = self.peers.oldest_entry()
                print "\t\t\t\t\t[%s] getting from peer [%s]" % (self.addrport,
                                                            repr(oe))
                success = self.request_peerlist(oe.addrport)
                if success:
                    oe.update()
        if not success:
            with self.connections_lock:
                if len(self.connections) > 0:
                    oe = self.connections.oldest_entry()
                    print "\t\t\t\t\t[%s] getting from conn [%s]" % (self.addrport,
                                                            repr(oe))
                    success = self.recv_peerlist(oe.sock)
                    if success:
                        oe.update()
                    else:
                        self.remove_connection(oe)

    def process_peerlist(self, strpeers):
        print "\t\t\t[%s] processing peers: %s" % (self.addrport, strpeers)
        strlist = strpeers.split('_')
        peerlist = []
        for each in strlist:
            address = each.split(',')[0][2:]
            strtime = each.split(',')[1][:-1].strip()
            if address != self.addrport:
                ple = ple_from_strings(address, strtime)
                self.add_peer_entry(ple)

    def add_peer_entry(self, peerentry):
        consumed = False
        with self.connections_lock:
            if peerentry.addrport in self.connections: 
                self.connections.add_entry(peerentry)
                consumed = True
        if not consumed:
            with self.peers_lock:
                self.peers.add_entry(peerentry)

    def add_peers(self, peerlist):
        print "adding peers: %s" % str(peerlist)
        with self.peers_lock:
            for each in peerlist:
                self.peers.add_entry(PeerListEntry(each))

    def __repr__(self):
        """Returns a short string representing the current status of this
        client."""
        return "[%s] (%d) %s %s" % (self.addrport, \
                                len(self.connections), \
                                str(self.connections), \
                                str(self.peers))

    def kmf_factory(self):
        """Returns a new coroutine function to respond to received socket
        messages and passes them on to the kernel."""
        def kmf(cle):
            while True:
                msg = (yield)
                if len(msg) > 0:
                    if msg.startswith('k '):
                        self.kernel.putmsg(msg[2:])
                    elif msg.startswith('p(') or msg.startswith('c('):
                        print "[%s] got peers from %s: %s" % (self.addrport,
                                                              cle.addrport,
                                                              msg)
                        self.process_peerlist(msg)
                    elif (len(msg) == 1) and msg.startswith('l'):
                        print "[%s] got list message from %s" % (self.addrport,
                                                                cle.addrport)
                        success = self.send_peerlist(cle.sock)
                        if success:
                            cle.update()
                    else:
                        print "kmf: %s" % msg
        return kmf

    def readkernel(self):
        """Requests information from the local kernel and sends it to a
        connected peer."""
        msg = self.kernel.getmsg()
        self.sendmsg('k ' + msg)

    def sendmsg(self, message):
        """Sends a kernel message to the connected peer with oldest
        timestamp."""
        if (message != ""):
            numbytes = len(message)
            with self.connections_lock:
                if len(self.connections) > 0:
                    connection = self.connections.oldest_entry()
                    client = connection.sock
                    success = False
                    for i in range(3):
                        with client.lock:
                            try:
                                client.socket.settimeout(30.0)
                                client.socket.send(message)
                            except socket.error as msg:
                                self.remove_connection(connection)
                            else:
                                success = True
                            break
                    if success:
                        connection.update()
                    else:
                        self.remove_connection(connection)

    def periodic_tasks(self):
        self.get_peers()
        self.seek_limit()

    def cleanup_connections(self):
        """Check all current connections and remove the ones that
        have finished."""
        with self.connections_lock:
            for connection in self.connections.list:
                if not connection.thread.is_alive():
                    print "{%s} removing dead connection to %s" % \
                               (self.addrport, connection.addrport)
                    self.remove_connection(connection)
        # remove stale peer entries
        with self.peers_lock:
            stale_list = []
            for peer in self.peers.list:
                if peer.is_stale():
                    stale_list.append(peer.addrport)
            for each in stale_list:
                self.peers.remove_entry(each)


    def seek_limit(self):
        if self.is_overlimit():
            self.cull_excess_connections()
        elif self.is_underlimit():
            self.seekpeer()
        #else pass

    def cull_excess_connections(self):
        """Drops an active connection if the number of connections are above
        the soft limit."""
        with self.connections_lock:
            if self.is_overlimit():
                oe = self.connections.oldest_entry()
                print "Culling excess connection: %s" % \
                        (str(oe.addrport))
                self.connections.remove_entry(oe)

    def remove_connection(self, connection):
        """Disconnect and remove a given connection."""
        connection.close()
        with self.connections_lock:
            if connection in self.connections:
                self.connections.remove_entry(connection)
        ple = PeerListEntry(connection.addrport)
        ple.update(connection.timestamp)
        with self.peers_lock:
            self.peers.add_entry(ple)
