import asyncore
import socket
from connectionhandler import ConnectionHandler

class ServerSocket(asyncore.dispatcher):
    def __init__(self, bind_address='', port=0):
        asyncore.dispatcher.__init__(self)
        self.create_socket(asyncore.socket.AF_INET,
                           asyncore.socket.SOCK_STREAM)
        self.bind((bind_address, port))
        self.address_port = self.socket.getsockname()
        self.address = self.address_port[0]
        self.port = self.address_port[1]
        self.listen(1)

    def handle_accept(self):
        sock,_ = self.accept()
        ConnectionHandler(socket=sock, server=self)

    def handle_close(self):
        self.close()

poll = asyncore.poll
connections = asyncore.socket_map
serversocket = ServerSocket()

def new_connection(host_port):
	sock = socket.create_connection(host_port)
	ConnectionHandler(socket=sock, server=serversocket)

