#!/usr/bin/env python
# pipetest.py
import itertools
import time
import sys 

try:
    for i in itertools.count(0):
        print("line %d"%i )
        sys.stdout.flush()
        time.sleep(2)
except (IOError):
    pass