import unittest

import kernel

class TestKernel(unittest.TestCase):

    def setUp(self):
        self.k = kernel.Kernel('test')

    def testGetMessage(self):
        self.assertEqual(len(self.k.getmsg()),8)
        self.assertTrue(self.k.getmsg().isalnum())

