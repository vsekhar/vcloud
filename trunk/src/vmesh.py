# Library imports
import sys
import time
import threading
import queue
import sys

# My imports
import orgqueues
from kernel import KernelHandler
#from xmlserver import VGPServer
import peermanager2

# User-defined constants
HOST, PORT = "localhost", 0

if __name__ == "__main__":
    
    # Kernel handling
    kernel = KernelHandler(sys.argv[1], orgqueues.inqueue, orgqueues.outqueue)
    kernel_thread = threading.Thread(target=kernel.run)
    kernel_thread.setDaemon(True)
    kernel_thread.start()
    
    # get first peer if any
    if len(sys.argv) >= 4:
        firsthost = sys.argv[2]
        firstport = sys.argv[3]
        firstpeer = (firsthost, int(firstport))
    else:
        firsthost = None
        firstport = None
        firstpeer = None

    # PeerManager
    peermanager = peermanager2.PeerManager((HOST,PORT), orgqueues.inqueue, orgqueues.outqueue, firstpeer)
    print("Listening on " + peermanager.address + " : " + str(peermanager.port))
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    
    kernel.stop()
    kernel_thread.join()
    print("Done.")
    