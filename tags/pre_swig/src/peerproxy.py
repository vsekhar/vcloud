import xmlrpc.client

class PeerProxy:
    def __init__(self, addr_port):
        self.host, self.port = addr_port
        self.uri = "http://" + self.host + ":" + str(self.port)
        self.do = xmlrpc.client.ServerProxy(self.uri)
