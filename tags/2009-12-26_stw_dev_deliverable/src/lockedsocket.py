from threading import RLock
import socket

class LockedSocket():

    def __init__(self,sock=None):
        if sock:
            self.socket = sock
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lock = RLock()
