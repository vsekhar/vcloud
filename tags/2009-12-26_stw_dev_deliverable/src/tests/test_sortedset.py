import unittest

from sortedset import SortedSet
from peerlistentry import PeerListEntry

class TestKernel(unittest.TestCase):

    def setUp(self):
        self.ple = [PeerListEntry(str(i)) for i in range(20)]
        self.ss = SortedSet(self.ple)

    def testInitialization(self):
        self.assertEqual(len(self.ss), 20)

    def testListAccess(self):
        ple = self.ss.get_entry('1')
        self.assertEqual(ple, self.ple[1])

        self.assertTrue('1' in self.ss)
        self.assertTrue(ple in self.ss)
        self.assertFalse('21' in self.ss)
        self.assertFalse(1 in self.ss)

    def testSetAccess(self):
        self.assertEqual(len(self.ss), 20)
        ple = PeerListEntry('5')
        self.ss.add_entry(ple)
        self.assertEqual(len(self.ss), 20)

    def testAddEntry(self):
        self.assertEqual(len(self.ss), 20)
        ple = PeerListEntry('20')
        self.ss.add_entry(ple)
        self.assertEqual(len(self.ss), 21)
        self.assertTrue('20' in self.ss)

    def testOldestEntries(self):
        oe = self.ss.oldest_entry()
        self.assertEqual(oe, '0')
        self.ss.add_entry(oe)
        self.assertEqual(oe, '0')
        oe.update()
        self.ss.add_entry(oe)
        oe = self.ss.oldest_entry()
        self.assertEqual(oe, '1')
        oe.update()
        self.ss.add_entry(oe)
        last_oe = oe
        oe = self.ss.oldest_entry()
        self.assertEqual(oe, '2')
        self.ss.add_entry(last_oe)
        self.assertEqual(oe, '2')

    def testRemove(self):
        self.ss.remove_entry('1')
        self.assertEqual(len(self.ss), 19)

    def testRemoveDuplicates(self):
        self.assertEqual(len(self.ss), 20)
        for n in range(4):
            self.ple.extend([PeerListEntry(str(i)) for i in range(5)])
        self.assertEqual(len(self.ple), 40)
        self.ss = SortedSet(self.ple)
        self.assertEqual(len(self.ss), 20)
