# Written by Stephen Weber
# stephen.t.weber@gmail.com

import unittest

from mocklockedsocket import MockLockedSocket
from mock_mc import MockMeshConnection
from connectionlistentry import ConnectionListEntry

import pymesh

class TestPyMesh(unittest.TestCase):

    def setUp(self):
        self.pm = pymesh.PyMesh("127.0.0.1:2000",limit=5)

    def testInitialization(self):
        self.assertEquals(self.pm.limit,5)
        self.assertEquals(pymesh.get_port(self.pm.addrport),2000)

    def testEmptyPeerList(self):
        ms = MockLockedSocket()
        self.assertEquals(ms.socket.buffer,'')
        self.pm.send_peerlist(ms)
        self.assertEquals(ms.socket.buffer,'')

    def testAddPeers(self):
        ms = MockLockedSocket()
        self.pm.add_peers([1,2,3,4,5])
        self.pm.send_peerlist(ms)
        self.assertEquals(ms.socket.buffer.count('p'),5)
        self.pm.add_peers([1,2,6])
        self.pm.send_peerlist(ms)
        self.assertEquals(ms.socket.buffer.count('p'),6)

    def testRemoveConnection(self):
        conn = ConnectionListEntry('',MockLockedSocket(),MockMeshConnection())
        self.pm.connections.add_entry(conn)
        self.assertEqual(len(self.pm.connections),1)
        self.pm.connections.remove_entry(conn)
        self.assertEqual(len(self.pm.connections),0)

    def testNotOverlimit(self):
        self.pm.set_limit(1)
        self.assertFalse(self.pm.is_overlimit())
        conn = ConnectionListEntry('',MockLockedSocket(),MockMeshConnection())
        self.pm.connections.add_entry(conn)
        self.assertFalse(self.pm.is_overlimit())

    def testOverlimit(self):
        self.pm.set_limit(1)
        conn1 = ConnectionListEntry('1',MockLockedSocket(),MockMeshConnection())
        conn2 = ConnectionListEntry('2',MockLockedSocket(),MockMeshConnection())
        self.pm.connections.add_entry(conn1)
        self.pm.connections.add_entry(conn2)
        self.assertTrue(self.pm.is_overlimit())

    def testLimitCulling(self):
        self.pm.set_limit(1)
        conn1 = ConnectionListEntry('1',MockLockedSocket(),MockMeshConnection())
        conn2 = ConnectionListEntry('2',MockLockedSocket(),MockMeshConnection())
        self.pm.connections.add_entry(conn1)
        self.pm.connections.add_entry(conn2)
        
        self.assertEqual(len(self.pm.connections),2)
        self.assertTrue(self.pm.is_overlimit())
        self.assertFalse(self.pm.is_underlimit())
        
        # culling removes a connection, this is back to not-overlimit
        self.pm.cull_excess_connections()
        self.assertEqual(len(self.pm.connections),1)
        self.assertFalse(self.pm.is_overlimit())
        self.assertFalse(self.pm.is_underlimit())
        
        # second cull does not remove more
        self.pm.cull_excess_connections()
        self.assertFalse(self.pm.is_underlimit())
        self.assertEqual(len(self.pm.connections),1)

    def testUnderlimit(self):
        self.pm.set_limit(1)
        self.assertTrue(self.pm.is_underlimit())
        conn1 = ConnectionListEntry('1',MockLockedSocket(),MockMeshConnection())
        self.pm.connections.add_entry(conn1)
        self.assertFalse(self.pm.is_underlimit())
        conn2 = ConnectionListEntry('2',MockLockedSocket(),MockMeshConnection())
        self.pm.connections.add_entry(conn2)
        self.assertFalse(self.pm.is_underlimit())
