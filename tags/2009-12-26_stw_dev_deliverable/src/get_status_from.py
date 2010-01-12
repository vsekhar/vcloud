# Written by Stephen Weber
# stephen.t.weber@gmail.com

import socket
import sys

if len(sys.argv) == 2:
    addrport = sys.argv[1]

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    result = "no data received."

    addr = addrport.split(':')[0]
    port = int(addrport.split(':')[1])

    try:
        sock.connect((addr, port))
        sock.send('s')
        result = sock.recv(1024)
        sock.shutdown(socket.SHUT_RDWR)
    except socket.error as (errno, strerror):
        print "Socket error({0}): {1}".format(errno, strerror)

    print "recv: {0}".format(result)
