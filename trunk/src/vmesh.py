# Library imports
import sys
import time
import threading
import queue
import sys

# My imports
import kernel
import peermanager

# User-defined constants
HOST, PORT = "localhost", 0

inqueue = queue.Queue()
outqueue = queue.Queue()

if __name__ == "__main__":
    
    if len(sys.argv) >= 4:
        firsthost = sys.argv[2]
        firstport = sys.argv[3]
        firstpeer = (firsthost, int(firstport))
    else:
        firsthost = None
        firstport = None
        firstpeer = None

    kernel = kernel.KernelHandler(sys.argv[1], inqueue, outqueue)
    mypeermanager = peermanager.PeerManager((HOST,PORT), inqueue, outqueue, firstpeer)
    print("Listening on " + mypeermanager.address + " : " + str(mypeermanager.port))
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Done.")
    