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
    def __init__(self, peermanager, server, direction, sock, timestamp=None):
        async_chat.__init__(self, sock=sock)
        
        self.address_port = self.socket.getpeername()
        self.address = self.address_port[0]
        self.port = self.address_port[1]

        self.server = server
        self.local_server_port = self.server.port

        self.peermanager = peermanager

        if timestamp is not None:
            self.timestamp = timestamp
        else:
            self.update_timestamp()
        
        self.set_terminator(COMMAND_TERMINATOR)
        self.message_length = 0
        self.message_command = None
        self.ibuffer = []
        
        self.direction = direction
        if self.direction == 'out':
            # we must have connected to the remote server port
            self.remote_server_port = self.port

            # send the local server port
            port_msg = 'z %s\n' % self.local_server_port
            if options.map.verbose > 2:
                print('sending server port to (%s:%s): %s' % (self.address, self.port, port_msg))
            self.push(port_msg.encode('ascii'))
            
        elif self.direction == 'in':
            self.remote_server_port = None
            
        else:
            raise RuntimeError("bad socket direction: %s" % self.direction)
        # remove from peer list (since it is now in the connection list)
        self.peermanager.del_peer(self.address_port)
    
    def collect_incoming_data(self, data):
        self.ibuffer.append(data)
    
    def found_terminator(self):
        self.update_timestamp()
        
        try:

            ####################################
            # Process variable-length messages
            ####################################
            bytes = b''.join(self.ibuffer).strip()
            self.ibuffer = []
            if self.message_length > 0 and self.message_command is not None:
                try:
                    len_bytes = len(bytes)
                    if len_bytes != self.message_length:
                        raise AssertionError("mismatched data lengths: %d expected, %d received" %
                                             (self.message_length, len_bytes))
                    if options.map.verbose > 2:
                        print('variable-length message complete, %d bytes' % self.message_length)
                    
                    # handle based on what command the message is tied to
                    if self.message_command == 'm':
                        # enqueue raw bytes
                        self.server.handle_incoming_message(bytes)
                        return
                    elif self.message_command == 's':
                        # decode and print
                        print("Stats from (%s:%s):" % self.address_port)
                        print(bytes.decode('ascii'))
                        return
                    else:
                        raise CommandError(
                            "variable-length message had bad command: %s"
                            % self.message_command)
                
                finally:
                    # get ready to receive a command
                    self.set_terminator(COMMAND_TERMINATOR)
                    self.message_length = 0
                    self.message_command = None

            ########################################
            # Else, try to process one-line messages
            ########################################
            text = bytes.decode('ascii')
            command = text[:1]
            message = text[2:]
            if options.map.verbose > 1 and self.message_length == 0:
                print('msg from (%s:%s): %s' % (self.address, self.port, text))

            # Other peer sent a variable-length message, so setup to receive
            # in next iteration of this loop
            if (command == 'm'  # kernel message
                or command == 'r' # stats response
                ):
                try:
                    length = int(message)
                except ValueError:
                    self.message_length = 0 # just in case
                    self.message_command = None
                    self.set_terminator(COMMAND_TERMINATOR) 
                    raise CommandError("Bad msg length: %s" % message)
                else:
                    if length > MAX_MSG_LEN:
                        raise CommandError("msg too long: size=%d (max=%d)" % (length, MAX_MSG_LEN))
                    self.set_terminator(length)
                    self.message_length = length
                    self.message_command = command
                    if options.map.verbose > 2:
                        print("variable-length message (%d bytes) starting" % self.message_length)
                
            # Other peer requested peers list
            elif command == 'p':
                excl_addr = (self.address, self.remote_server_port)
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
                    print('list received: %s' % message)

                try:
                    self.peermanager.update_peers(eval(message))
                except TypeError:
                    raise CommandError('Bad peer list: %s' % message)
            
            # Other peer or administrator requested statistics
            elif command == 's':
                stats = 'r ' + self.server.get_stats() + '\n'
                if options.map.verbose > 1:
                    print('request for stats')
                self.push(stats.encode('ascii'))
                        
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
                    self.peermanager.del_peer((self.address, self.remote_server_port))
                        
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
            print('CommandError from %s: %s' % (self.address_port, err))
            self.close_when_done()
    
    def update_timestamp(self):
        "Update timestamp (for use each time a successful socket communication takes place)"
        self.timestamp = datetime.datetime.utcnow()

    ''' Overrides to handle the peer_map and the time stamp '''
    def del_channel(self):
        "Delete channel from active sockets map, and move it to peers list"
        if self.direction == 'in' and self.remote_server_port is not None:
            peer_server = (self.address, self.remote_server_port)
            self.peermanager.add_peer(peer_server, self.timestamp)
        elif self.direction == 'out':
            self.peermanager.add_peer(self.address_port, self.timestamp)
        else:
            print("warning: no remote server port, peer dropped (%s:%s)" % self.address_port)
        return async_chat.del_channel(self)

    def handle_write(self):
        "Handle a write event and update the timestamp"
        async_chat.handle_write(self)
        self.update_timestamp()
    
    def handle_read(self):
        "Handle a read event and update the timestamp"
        async_chat.handle_read(self)
        self.update_timestamp()
    
    def handle_close(self):
        if options.map.verbose:
            print('closing connection to %s:%s' % (self.address, self.remote_server_port))
        async_chat.handle_close(self)
