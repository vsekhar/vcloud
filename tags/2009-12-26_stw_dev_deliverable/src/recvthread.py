# Written by Stephen Weber
# stephen.t.weber@gmail.com

import threading
import socket


class RecvThread(threading.Thread):

    def __init__(self, client, timeout=1.0):
        threading.Thread.__init__(self)
        self.client = client
        self.success = False
        self.data = None
        self.error = False
        self.timeout = timeout

    def run(self):
        msg = None
        with self.client.lock:
            self.client.socket.settimeout(self.timeout)
            try:
                msg = self.client.socket.recv(1024)
            except socket.timeout:
                msg = None
            except socket.error:
                self.client.socket.close()
                self.error = True
            else:
                self.data = msg
                self.success = True
