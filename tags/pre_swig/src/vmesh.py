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
    executable = argv[0]
    if len(argv) >= 3:
        firstpeer = (argv[1], int(argv[2]))
    else:
        firsthost = None
        firstport = None
        firstpeer = None

    mykernel = kernel.KernelHandler(executable, inqueue, outqueue)
    mypeermanager = peermanager.PeerManager((HOST,PORT), inqueue, outqueue, mykernel.get_heartbeat_time, firstpeer)
    print("Listening on " + mypeermanager.address + " : " + str(mypeermanager.port))
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Done.")

if __name__ == "__main__":
    main(sys.argv[1:])

