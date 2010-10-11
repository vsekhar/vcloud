import threading
import queue
import options
import basekernel

from random import choice
from util.repeattimer import RepeatTimer

LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = "0123456789"

SEND_INTERVAL = 1
MSGS_PER_INTERVAL = 10

class IncomingThread(threading.Thread):
    def __init__(self, kernel):
        threading.Thread.__init__(self, name="kernel_incoming_thread")
        self.kernel = kernel

    def run(self):
        """Processes pending messages in the inqueue."""
        while 1:
            try:
                msg = self.kernel._inqueue.get()
                if msg is None:
                    return
                if options.map.verbose > 1:
                    print("[%s] recv: %s" % (self.kernel.name,msg))
            except queue.Empty:
                pass

    def cancel(self):
        # processing messages is fast (just prints) so we can use a None message
        # as a cancel notifier. if a kernel takes time to process messages,
        # an event loop should check an Event() object for cancellation periodically
        self.kernel._inqueue.put(None)

class OutgoingTimer(RepeatTimer):
    def __init__(self, interval, kernel):
        RepeatTimer.__init__(self, interval=interval,
                             target=self.get_outgoing,
                             name="kernel_outgoing_timer")
        self.kernel = kernel

    def get_outgoing(self, n=MSGS_PER_INTERVAL):
        """Inserts a short string to outqueue, representing the results of a
        calculation."""
        for _ in range(n):
            random_text = ''.join([choice(LETTERS + DIGITS) for _ in range(8)])
            self.kernel._outqueue.put(random_text.encode('ascii'))

class Kernel(basekernel.BaseKernel):
    """Receives messages and returns messages. A placeholder for interaction
    with a data consumer/producer."""

    def __init__(self, name, send_interval=None):
        self.name = name
        self._inqueue = queue.Queue()
        self._outqueue = queue.Queue()
        if send_interval is not None:
            self.send_interval = send_interval
        else:
            self.send_interval = SEND_INTERVAL
        self.get_outgoing_timer = OutgoingTimer(self.send_interval, self)
        self.handle_incoming_thread = IncomingThread(self)
    
    def start(self):
        self.get_outgoing_timer.start()
        self.handle_incoming_thread.start()
    
    def cancel(self):
        self.get_outgoing_timer.cancel()
        self.handle_incoming_thread.cancel()
    
    def join(self):
        self.get_outgoing_timer.join()
        self.handle_incoming_thread.join()

    def get_messages(self, max_n=1):
        ret = []
        count = 0
        try:
            while 1:
                ret.append(self._outqueue.get_nowait())
                if max_n is not None and count >= max_n:
                    break
        except queue.Empty:
            pass
        return ret
    
    def put_messages(self, msgs):
        count = 0
        for msg in msgs:
            self._inqueue.put(msg)
            ++count
        return count        
