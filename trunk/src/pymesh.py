'''
Created on 2009-12-28
'''

import meshserver

from mockkernel import Kernel
from queue import Queue

class PyMesh(object):
    '''
    Main PyMesh manager class
    '''

    def __init__(self):
        '''
        Constructs a PyMesh manager and starts listening
        '''
        self.inqueue = Queue()
        self.outqueue = Queue()
        self.queues = (self.inqueue, self.outqueue)
        self.server = meshserver.MeshServer(self.inqueue, self.outqueue)        
        self.kernel = Kernel("mockkernel", self.inqueue, self.outqueue)
    
    def start(self):
        self.kernel.start()
        self.server.start()
        
    def cancel(self):
        self.kernel.cancel()
        self.server.cancel()