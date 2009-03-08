# Library imports
import sys
import time
import queue

# My imports
import kernel
import peermanager

# User-defined constants
HOST, PORT = "localhost", 0

inqueue = queue.Queue()
outqueue = queue.Queue()

def main(argv):
    if len(sys.argv) >= 3:
        firsthost = sys.argv[1]
        firstport = sys.argv[2]
        firstpeer = (firsthost, int(firstport))
    else:
        firsthost = None
        firstport = None
        firstpeer = None

    kernel = kernel.KernelHandler(sys.argv[0], inqueue, outqueue)
    mypeermanager = peermanager.PeerManager((HOST,PORT), inqueue, outqueue, firstpeer)
    print("Listening on " + mypeermanager.address + " : " + str(mypeermanager.port))
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Done.")

if __name__ == "__main__":
    main(sys.argv[1:])