'''
Created on 2009-12-30
'''

import version
from optparse import OptionParser

def get_option_parser():
    usage_str = 'usage: %prog [options] args'
    version_str = '%prog ' + version.string
    parser = OptionParser(usage=usage_str, version=version_str)
    
    parser.add_option('-f', '--config-file', dest='config_file',
    				  help='configuration file')

    parser.add_option('-s', '--seed', dest='seeds',
                      action='append', default = [],
                      help='add a seed peer (addr:port format)')

    return parser

map = None
args = None

def parse_cmd_line():
    global map, args
    parser = get_option_parser()
    map, args = parser.parse_args()

# for testing, invoke from command line with '-v' to have it print the parse
if __name__ == '__main__':
    parse_cmd_line()
    
