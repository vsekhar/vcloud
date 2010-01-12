'''
Created on 2010-01-11
'''

def print_addresses(addresses):
    '''Accepts a list of tuples of the format ('addr', int(port)) and
    prints them'''
    if len(addresses):
        a,p = addresses[0]
        print('%s:%s' % (a,p)) 
        for (addr, port) in addresses[1:]:
            print(', %s:%s' % (addr, port))
