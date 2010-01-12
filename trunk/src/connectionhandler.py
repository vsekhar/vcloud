'''
Created on 2009-12-29

Asyncore/asynchat wrapped sockets, no threading
'''
import datetime
import options
from asynchat import async_chat

MAX_MSG_LEN = 1024*1024 # 1 megabyte
COMMAND_TERMINATOR = b'\n'

class CommandError(Exception):
    pass

class ConnectionHandler(async_chat):
    def __init__(self, addr, peermanager, server, direction, sock=None, timestamp=None):
        async_chat.__init__(self, sock=sock)
        self.set_terminator(COMMAND_TERMINATOR)
        
        self.addr = addr
        self.remote_server_port = None
        self.server = server
        self.local_server_port = self.server.address[1]
        self.direction = direction
        if not sock:
            print("warning: ConnectionHandler received None socket, opening a new one")
            self.connect(self.addr)
        self.peermanager = peermanager
        self.ibuffer = []
        if timestamp:
            self.timestamp = timestamp
        else:
            self.update_timestamp()
        
        self.message_length = 0
        
        if self.direction == 'out':
            # we must have connected to the remote server port
            self.remote_server_port = self.addr[1]

            # send the local server port
            port_msg = 'z %s\n' % self.local_server_port
            if options.map.verbose > 1:
                print('sending server port to (%s:%s): %s' % (self.addr[0], self.addr[1], port_msg))
            self.push(port_msg.encode('ascii'))
            
            # remove from peer list (since it is now in the connection list)
            self.peermanager.del_peer(self.addr)
    
    def collect_incoming_data(self, data):
        self.ibuffer.append(data)
    
    def found_terminator(self):
        self.update_timestamp()
        
        try:

            ####################################
            # Try to process as a binary message
            ####################################
            bytes = b''.join(self.ibuffer).strip()
            self.ibuffer = []
            if self.message_length > 0:
                len_bytes = len(bytes)
                if len_bytes != self.message_length:
                    raise AssertionError("mismatched message lengths: %d expected, %d received" %
                                         (self.message_length, len_bytes))
                if options.map.verbose > 1:
                    print('kernel message complete, %d bytes' % self.message_length)
                self.set_terminator(COMMAND_TERMINATOR)
                self.message_length = 0
                
                # Maybe do some validation? if kernels implement this?
                # if not kernel.validate_msg(data):
                #    raise CommandError('Bad message from %s: %s' % (self.addr, data))

                self.server.inqueue.put(bytes)
                return

            ##################################################
            # Else, try to process as an ascii command/message
            ##################################################
            text = bytes.decode('ascii')
            command = text[:1]
            message = text[2:]
            if options.map.verbose and self.message_length == 0:
                print('msg from (%s:%s): %s' % (self.addr[0], self.addr[1], text))

            # Other peer requested peers list
            if command == 'p':
                excl_addr = (self.addr[0], self.remote_server_port)
                lst = self.peermanager.get_peers_and_connections(excl_addr)
                if lst is None:
                    lst_str = '[]'
                else:
                    lst_str = str(lst)
                response = 'l ' + lst_str + '\n'
                if options.map.verbose > 1:
                    print('sending list')
                self.push(response.encode('ascii'))
            
            # Other peer sent a new peer list (not implemented)
            ## e.g. {('127.0.0.1', 54216): datetime.timedelta(0, 2, 467959)}
            elif command == 'l':
                if options.map.verbose > 1:
                    print('list received')

                try:
                    self.peermanager.update_peers(eval(message))
                except TypeError:
                    raise CommandError('Bad peer list: %s' % message)
            
            # Other peer sent a kernel message, so setup to receive binary
            elif command == 'm':
                try:
                    self.message_length = int(message)
                except ValueError:
                    self.message_length = 0 # just in case
                    self.set_terminator(COMMAND_TERMINATOR) # just in case
                    raise CommandError('Bad msg length: %s' % message)
                else:
                    self.set_terminator(self.message_length)
                    if options.map.verbose > 1:
                        print('kernel message of length %d starting' % self.message_length)
                
            # Other peer or administrator requested statistics
            elif command == 's':
                stats = 'r ' + self.server.get_stats() + '\n'
                if options.map.verbose > 1:
                    print('request for stats')
                self.push(stats.encode('ascii'))
            
            # Other peerdebug sent statistics (not implemented)
            elif command == 'r':
                pass
            
            # Other peer sent its server port
            elif command == 'z':
                try:
                    new_port = int(message)
                    if new_port == 0:
                        raise ValueError
                except ValueError:
                    # Catches int() error, or new_port==0 error
                    raise CommandError("Bad remote port '%s'" % message)
                else:
                    self.remote_server_port = new_port
                    if options.map.verbose > 1:
                        print('received server port %s' % new_port)
                    self.peermanager.del_peer((self.addr[0], self.remote_server_port))
                        
            # Other peer notified of disconnection
            elif command == 'd':
                if options.map.verbose > 1:
                    print('disconnect requested')
                self.close_when_done()
            
            # Human operator sent a hello command
            elif command == 'h':
                if options.map.verbose > 1:
                    print('hello')
                self.push('hello\n'.encode('ascii'))
            
            # Human operator sent kill command (not yet implemented)
            elif command == 'x':
                if options.map.verbose > 1:
                    print('kill')
                pass
    
            # no-op (remove this after debugging to treat stray newlines as errors)
            elif command == '':
                pass
            
            # Unknown command
            else:
                raise CommandError("Unknown command '%s'" % command)

        # Command error, kill the connection (is this too extreme?)
        except CommandError as err:
            print('CommandError from %s: %s' % (self.addr, err))
            self.close_when_done()
    
    def update_timestamp(self):
        "Update timestamp (for use each time a successful socket communication takes place)"
        self.timestamp = datetime.datetime.utcnow()

    ''' Overrides to handle the peer_map and the time stamp '''
    def del_channel(self):
        "Delete channel from active sockets map, and it move to peers list"
        if self.direction == 'in' and self.remote_server_port:
            peer_server = (self.addr[0], self.remote_server_port)
            self.peermanager.add_peer(peer_server, self.timestamp)
        elif self.direction == 'out':
            self.peermanager.add_peer(self.addr, self.timestamp)
        return async_chat.del_channel(self)

    def handle_write(self):
        "Handle a write event and update the timestamp"
        async_chat.handle_write(self)
        self.update_timestamp()
    
    def handle_close(self):
        if options.map.verbose:
            print('closing connection to %s:%s' % (self.addr[0], self.remote_server_port))
        async_chat.handle_close(self)