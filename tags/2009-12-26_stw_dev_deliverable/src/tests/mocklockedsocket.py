# Written by Stephen Weber
# stephen.t.weber@gmail.com

from mocksocket import MockSocket

class MockRLock:
    def __init__(self):
        self.acquire_count = 0
        self.release_count = 0

    def acquire(self):
        self.acquire_count += 1

    def release(self):
        self.release_count += 1

    def __enter__(self):
        self.acquire_count += 1

    def __exit__(self, type, value, traceback):
        self.release_count += 1

    def is_balanced(self):
        return (self.release_count == self.acquire_count)

class MockLockedSocket():

    def __init__(self, message=""):
        self.socket = MockSocket(message)
        self.lock = MockRLock() 

    def is_released(self):
        return self.lock.acquire_count.is_balanced()
