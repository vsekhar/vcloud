'''
Created on 2010-01-16
'''

import asyncore

class ServerSocket(asyncore.dispatcher):
    '''
    An implementation of a asyncore.dispatcher for receiving new peer connections
    '''


    def __init__(self, bind_address, port, mesh):
        '''
        Create a socket and start listening
        '''
        asyncore.dispatcher.__init__(self)
        self.mesh = mesh
        self.peermgr = mesh.peermgr
        self.create_socket(asyncore.socket.AF_INET,
                           asyncore.socket.SOCK_STREAM)
        self.bind((bind_address, port))
        self.address_port = self.socket.getsockname()
        self.address = self.address_port[0]
        self.port = self.address_port[1]
        self.listen(1)

    def handle_accept(self):
        (sock, addr) = self.accept()
        print('Received connection (%s:%s)' % (addr[0], addr[1]))
        self.peermgr.accept_connection(sock=sock,
                                addr=addr,
                                server=self.mesh)

    def handle_close(self):
        self.close()
        
