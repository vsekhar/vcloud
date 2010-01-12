# Written by Stephen Weber
# stephen.t.weber@gmail.com

from peerlistentry import PeerListEntry
from meshconnection import MeshConnection

class ConnectionListEntry(PeerListEntry):

    def __init__(self, addrport, sock, callback):
        PeerListEntry.__init__(self,addrport)
        self.sock = sock
        self.callback = callback(self)
        self.callback.next()
        self.thread = MeshConnection(self.sock,self.message_conduit)
        self.thread.start()

    def close(self):
        if self.thread.is_alive():
            self.thread.stop.set()

    def message_conduit(self, message):
        self.update()
        self.callback.send(message)

    def __str__(self):
        return "Connection %s last seen at %s" % (self.addrport,str(self.timestamp))

    def __repr__(self):
        return "c(%s, %s)" % (self.addrport,str(self.timestamp))
