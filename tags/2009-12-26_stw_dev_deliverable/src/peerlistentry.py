# Written by Stephen Weber
# stephen.t.weber@gmail.com

from datetime import datetime, timedelta
from threading import RLock

OLDEST_DELTA = timedelta(seconds=60)

def ple_from_strings(addrport, strtime):
    strdt = strtime.split('.')[0]
    micros = int(strtime.split('.')[1])
    timestamp = datetime.strptime(strdt, "%Y-%m-%d %H:%M:%S")
    micro_td = timedelta(microseconds=micros)
    return PeerListEntry(addrport, timestamp + micro_td)

class PeerListEntry():
    """Represents a known peer that is a potential connection."""

    def __init__(self, addrport, timestamp=None):
        self.addrport = addrport
        if timestamp:
            self.timestamp = timestamp
        else:
            self.timestamp = datetime.utcnow()
        self.timestamp_lock = RLock()

    def update(self, newtime=None):
        """Update the timestamp with a new time. If a time is not specified,
        the current UTC time is used."""
        with self.timestamp_lock:
            if newtime:
                self.timestamp = newtime
            else:
                self.timestamp = datetime.utcnow()

    def is_stale(self):
        retval = False
        with self.timestamp_lock:
            if (self.timestamp + OLDEST_DELTA) < datetime.utcnow():
                retval = True
        return retval

    def __eq__(self, other):
        try:
            value = other.addrport
        except AttributeError:
            value = other
        return (self.addrport == value)

    def __ne__(self, other):
        try:
            value = other.addrport
        except AttributeError:
            value = other
        return (self.addrport != value)

    def __cmp__(self, other):
        if (self.timestamp < other.timestamp):
            return -1
        elif (self.timestamp > other.timestamp):
            return 1
        return 0

    def __str__(self):
        return "Peer %s last seen at %s" % (self.addrport,str(self.timestamp))
    
    def __repr__(self):
        return "p(%s, %s)" % (self.addrport,str(self.timestamp))
