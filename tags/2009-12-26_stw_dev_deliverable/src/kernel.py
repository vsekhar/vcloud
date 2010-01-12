# Written by Stephen Weber
# stephen.t.weber@gmail.com

from random import choice

LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = "0123456789"

class Kernel():
    """Receives messages and returns messages. A placeholder for interaction
    with a data consumer/producer."""

    def __init__(self,name):
        self.name = name

    def getmsg(self):
        """Returns a short string, representing the results of a
        calculation."""
        return ''.join([choice(LETTERS + DIGITS) for i in range(8)])

    def putmsg(self, message):
        """Accepts a short string message, and returns True if it was
        accepted."""
        print "[%s] recv: %s" % (self.name,message)
        return True
