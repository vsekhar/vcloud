# Libraries
import xmlrpc.client
import sys

# Me
import peerproxy

error_threshold = 3

def trace(host, port):
    """Returns a tuple, the first element being a dictionary with
       data on each peer found in the mesh, the second being a set
       of (address,port) of peers that could not be reached"""
    done = dict() # {(host,port):result, ...}
    queue = dict() # {(host,port):error_count, ...}
    queue[(host,port)] = 0 # add starting node (with no errors)
    error = set() # {(host,port),...} for hosts that repeatedly error out 
    while len(queue):
        current, cur_errors = queue.popitem()
        if current in done:
            continue
        proxy = peerproxy.PeerProxy(current)
        try:
            response = proxy.do.X_getinfo()
            done[current] = response
            for newpeer in response["connections"]+response["awares"]:
                # XML-RPC converts tuples to lists, so need to convert back
                newpeer_tuple = tuple(newpeer)
                queue.append(newpeer_tuple)
        except IOError:
            cur_errors = cur_errors + 1
            if cur_errors >= error_threshold:
                # too many errors, so stash this host in the error set
                error.add(current)
            else:
                # return host to queue to try again later
                queue[current] = cur_errors
    return done,error

if __name__ == "__main__":
    done,error = trace(sys.argv[1], int(sys.argv[2]))
    for k,v in done.items():
        print(k, ": ")
        for a,b in v.items():
            print("\t", a, "=", b)
    for k in error:
        print("Error accessing: ", k)
