# Libraries
import xmlrpc.client
import sys

# Me
import peerproxy

def trace(host, port):
    done = dict()
    queue = [(host, port)]
    while len(queue):
        current = tuple(queue.pop())
        if current in done:
            continue
        proxy = peerproxy.PeerProxy(current)
        try:
            response = proxy.do.X_getinfo()
            done[current] = response
            for newpeer in response["peers"]:
                queue.append(tuple(newpeer))
        except IOError:
            print("Error accessing: ", current)
    return done

if __name__ == "__main__":
    print(trace(sys.argv[1], int(sys.argv[2])))