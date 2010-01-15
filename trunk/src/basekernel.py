'''
Created on 2010-01-14
'''

class BaseKernel(object):
    '''
    Interface definition of a user-defined kernel class.
    
    User kernels need not inherit from this class but should implement the
    specified methods in the specified way
    '''

    def start(self):
        '''starts the kernel (must not block)'''
        raise NotImplementedError("must be implemented in subclass")
    
    def cancel(self):
        '''signals that the kernel should finish up (must not block)'''
        raise NotImplementedError("must be implemented in subclass")
    
    def join(self):
        '''blocks until the kernel is actually stopped
        you usually need to run cancel() before join() in order to signal that
        the kernel should finish up, if you don't, then join() basically just
        waits for the kernel to finish naturally, which may or may not ever happen'''
        raise NotImplementedError("must be implemented in subclass")
    
    def get_message: return get_messages(self)[0]
    def get_messages(self, max_n=1):
        '''returns at most max_n=1 kernel messages as a list
        Must not block. Must be thread-safe. Kernel messages are sent by vmesh
        as-is over a socket as binary data, with no encoding applied'''
        raise NotImplementedError("must be implemented in subclass")
    
    def put_message(self, msg): return put_messages([msg])
    def put_messages(self, msgs):
        '''applies received kernel messages to the kernel, returns number processed
        Must not block. Must be thread-safe. msgs must be a list of messages.
        If all msgs cannot be consumed, function should return how many were.
            E.g.:
                msgs = [1,2,3,4,5]
                while msgs:
                    count = self.put_messages(msgs)
                    msgs = msgs[count:]
        '''
        raise NotImplementedError("must be implemented in subclass")