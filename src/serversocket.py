import asyncore
from connectionhandler import ConnectionHandler

class ServerSocket(asyncore.dispatcher):
    def __init__(self, bind_address, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(asyncore.socket.AF_INET,
                           asyncore.socket.SOCK_STREAM)
        self.bind((bind_address, port))
        self.address_port = self.socket.getsockname()
        self.address = self.address_port[0]
        self.port = self.address_port[1]
        self.listen(1)

    def handle_accept(self):
        (sock, _) = self.accept()
        ConnectionHandler(sock, 'in')

    def handle_close(self):
        self.close()
        
