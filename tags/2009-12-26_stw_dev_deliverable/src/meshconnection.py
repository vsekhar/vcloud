# Written by Stephen Weber
# stephen.t.weber@gmail.com

import threading
from recvthread import RecvThread
from repeattimer import RepeatTimer

class MeshConnection(threading.Thread):
    """A sub-thread that handles a successful connection request"""

    THRESHOLD = 20

    def __init__(self, clntsock, callback):
        """Set up thread. Expects to received a LockedSocket as clntsock."""
        threading.Thread.__init__(self)
        self.client = clntsock
        self.port = 0
        self.callback = callback
        self.stop = threading.Event()
        self.msg_recv = threading.Event()
        self.rt = None
        self.timeout_count = 0

    def run(self):
        """Method representing the thread's activity, listens for socket
        activity and shares it locally."""
        with self.client.lock:
            self.port = self.client.socket.getpeername()[1]
        grt = RepeatTimer(0.1, self.generate_receiver)
        grt.start()

        while not self.stop.is_set():
            if self.msg_recv.is_set():
                self.msg_recv.clear()
                if self.rt.success:
                    self.timeout_count = 0
                    self.callback(self.rt.data)
                else:
                    if self.rt.error:
                        break
                    self.timeout_count += 1

                if self.timeout_count > MeshConnection.THRESHOLD:
                    print "Client timed out too many times, ending recv."
                    break
        grt.cancel()

    def generate_receiver(self):
        if self.rt and self.rt.is_alive():
            pass
        else:
            self.rt = RecvThread(self.client)
            self.rt.start()
            self.rt.join()
            self.msg_recv.set()

    def __repr__(self):
        return "MeshConnection(%d,%d)" % (self.myid,self.port)
