'''
Created on 2009-12-29

@author: vsekhar
'''

from threading import RLock

def LockedObj(object):
    def __init__(self, data):
        self.data = data
        self.lock = RLock()
    
    def __enter__(self):
        self.lock.acquire()
    
    def __exit__(self):
        self.lock.release()
