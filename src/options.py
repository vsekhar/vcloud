import version
from optparse import OptionParser

def get_option_parser():
    usage_str = 'usage: %prog [options] args'
    version_str = '%prog ' + version.string
    parser = OptionParser(usage=usage_str, version=version_str)

    parser.add_option('-c', '--config-file', dest='config_file',
                      action='store', default = './config',
                      help='path and file containing configuration')

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

