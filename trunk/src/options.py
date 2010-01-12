'''
Created on 2009-12-30
'''

import version
from optparse import OptionParser

def get_option_parser():
    usage_str = 'usage: %prog [options] args'
    version_str = '%prog ' + version.string
    parser = OptionParser(usage=usage_str, version=version_str)
    
    parser.add_option('-b', '--bind_address', dest='bind_address',
                      help='bind local server to given address (default=OS-determined',
                      default='')
    
    parser.add_option('-p', '--bind_port', dest='bind_port',
                      help='bind local server to given port (default=OS-determined)',
                      type='int', default='0')
    
    parser.add_option('-s', '--seed', dest='seeds',
                      action='append', default = [],
                      help='add a seed peer (addr:port format)')
    
    parser.add_option('-c', '--connections', dest='connections',
                      help='number of connections to try to maintain (default=3)',
                      type='int', default='3')
    
    parser.add_option('-n', '--peers', dest='peers',
                      help='max number of peers to track (default=30)',
                      type='int', default='30')
    
    parser.add_option('-v', '--verbose', dest='verbose',
                      help='set verbose mode (more output, -vv for even more)',
                      action='count', default=0)
    
    parser.add_option('-t', '--peer_timeout', dest='peer_timeout',
                      help='max time in seconds peers will remain tracked before timeout (default=30)',
                      type='int', default='30')
    
    return parser

map = None
args = None

def parse_cmd_line():
    global map, args
    parser = get_option_parser()
    map, args = parser.parse_args()
    if map.verbose > 1:
        print(map, args)


# for testing, invoke from command line with '-d' to have it print the parse
if __name__ == '__main__':
    parse_cmd_line()
    