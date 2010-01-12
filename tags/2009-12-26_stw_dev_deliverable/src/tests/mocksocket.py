# Written by Stephen Weber
# stephen.t.weber@gmail.com

class MockSocket:

    def __init__(self,message=""):
        self.message = message
        self.timeout = 0.0
        self.closed = False
        self.buffer = ''

    def getpeername(self):
        return ('127.0.0.1',22222)

    def settimeout(self,seconds):
        self.timeout = seconds

    def recv(self,buffersize):
        return self.message

    def send(self,msg):
        self.buffer = msg

    def close(self):
        self.closed = True

