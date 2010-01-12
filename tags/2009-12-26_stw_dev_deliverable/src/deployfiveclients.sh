#!/bin/bash

python srvr.py 127.0.0.1:2000 &
sleep 0.5s
python srvr.py 127.0.0.1:2001 -p 127.0.0.1:2000 &
sleep 0.5s
python srvr.py 127.0.0.1:2002 -p 127.0.0.1:2000 &
sleep 0.5s
python srvr.py 127.0.0.1:2003 -p 127.0.0.1:2000 &
sleep 0.5s
python srvr.py 127.0.0.1:2004 -p 127.0.0.1:2000 &
