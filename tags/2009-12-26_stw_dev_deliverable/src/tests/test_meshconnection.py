# Written by Stephen Weber
# stephen.t.weber@gmail.com

import unittest

from mocklockedsocket import MockLockedSocket
import meshconnection

class TestMeshConnection(unittest.TestCase):

    def setUp(self):
        self.client = MockLockedSocket()
        self.mc = meshconnection.MeshConnection(self.client,self.mock_callback())

    def mock_callback(self):
        def mc():
            while 1:
                msg = (yield)
        return mc

    def testStopSignal(self):
        self.assertEqual(self.mc.port, 0)
        self.assertFalse(self.client.socket.closed)
        self.mc.start()
        self.mc.stop.set()
        self.mc.join(5.0)
        self.assertFalse(self.mc.isAlive())
        self.assertEqual(self.mc.port, 22222)
