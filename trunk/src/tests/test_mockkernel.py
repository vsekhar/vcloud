'''
Created on 2009-12-31

SHELVED: Until rest of implementation is more nailed down
'''

import unittest
import queue
import time

from .mockkernel import Kernel

class MockKernelTestCase(unittest.TestCase):
    def setUp(self):
        self.inqueue = queue.Queue()
        self.outqueue = queue.Queue()
    
    def make_kernel(self):
        return Kernel(name="test_mock_kernel",
                                    inqueue=self.inqueue,
                                    outqueue=self.outqueue,
                                    send_interval=0.1,
                                    recv_timeout=0.1)

    
    def clearqueues(self):
        try:
            while 1:
                self.inqueue.get_nowait()
        except queue.Empty:
            pass
        
        try:
            while 1:
                self.outqueue.get_nowait()
        except queue.Empty:
            pass
    
    def test_message_passing(self):
        kernel = self.make_kernel()
        self.clearqueues()
        for i in range(10):
            self.inqueue.put(str(i))
        kernel.start()
        try:
            time.sleep(1)
            with self.assertRaises(queue.Empty):
                self.inqueue.get_nowait()
            self.outqueue.get_nowait() # check if this raises exception
            self.assertTrue(True)      # won't get to here if it does
        finally:
            kernel.cancel()
            kernel.join()
    
if __name__ == '__main__':
    unittest.main()
