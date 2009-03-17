# Libraries
import xmlrpc.client
import sys

# Me
import peerproxy

def trace(host, port):
    done = dict()
    queue = [(host, port)]
    while len(queue):
        current = queue.pop()
        if current in done:
            continue
        proxy = peerproxy.PeerProxy(current)
        try:
            response = proxy.do.X_getinfo()
            done[current] = response
            for newpeer in response["peers"]:
                # XML-RPC converts tuples to lists, so need to convert back
                newpeer_tuple = tuple(newpeer)
                queue.append(newpeer_tuple)
        except IOError:
            print("Error accessing: ", current)
    return done

if __name__ == "__main__":
    data = trace(sys.argv[1], int(sys.argv[2]))
    for k,v in data.items():
        print(k, ": ")
        for a,b in v.items():
            print("\t", a, "=", b)