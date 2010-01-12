from pymesh import PyMesh
from kernel import Kernel
import sys
import optparse

def main():
    """Actions to perform when run as the main script."""
    parser = get_parser()
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("incorrect number of arguments")
    local = get_local_address(args)
    if (None == local):
        print "Could not determine local address! Exiting now."
        return
    mgr = PyMesh(local,limit=options.softlimit,
                 kernel=Kernel(local),seeds=options.seeds)
    mgr.start()
    mgr.join()

def get_parser():
    """Returns an option parser for this program."""
    parser = optparse.OptionParser(
        usage="%prog address:port [-p address:port] [-n num] [-f freq]",
        version='%prog 2009-12-16')

    parser.set_defaults(softlimit=3, frequency=120, seeds=[])

    parser.add_option("-n",
                      type="int", dest="softlimit")
    parser.add_option("-f","--frequency",
                      type="int", dest="frequency")
    parser.add_option("-p",
                      action="append", dest="seeds")

    return parser

def get_local_address(arglist):
    """Parse the program's arguments to find the address and port number to
    bind to."""
    for each in arglist:
        if (each.count(':') == 1):      # simple checks for now
            if (each.count('.') == 3):
                return each
    return None

if __name__ == "__main__":
    main()
