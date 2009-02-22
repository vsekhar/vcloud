from __future__ import with_statement
import threading
import time
import random

class TimedList:
    def __init__(self, d=None):
        if d is None:
            self.dict = dict()
        else:
            self.dict = dict(d)
        self.lock = threading.RLock()
    
    def __len__(self):
        with self.lock:
            return len(self.dict)
    
    def getlist(self):
        with self.lock:
            return list(self.dict.items())
    
    def touch(self, item):
        with self.lock:
            self.dict[item] = time.time()
    
    def touchlist(self, l):
        with self.lock:
            for (h,p),v in l:
                if (h,p) in self.dict:
                    self.dict[(h,p)] = max(self.dict[(h,p)], v)
                else:
                    self.dict[(h,p)] = v
    
    def remove(self, item):
        try:
            with self.lock:
                del self.dict[item]
        except KeyError:
            pass
    
    def has(self, item):
        with self.lock:
            return item in self.dict
    
    def removeByAge(self, interval):
        curtime = time.time()
        removed = list()
        with self.lock:
            ks = list(self.dict.keys())
            for k in ks:
                if curtime - self.dict[k] > interval:
                    removed.append((k, self.dict[k]))
                    del self.dict[k]
        return removed

    def getrandom(self):
        with self.lock:
            ks = list(self.dict.keys())
        return random.choice(ks)
    
    def poprandom(self):
        with self.lock:
            ks = list(self.dict.keys())
            item = random.choice(ks)
            del self.dict[item]
        return item
