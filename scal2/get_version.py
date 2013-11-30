#!/usr/bin/env python2
import os

VERSION = ''

fp = open('%s/core.py'%os.path.dirname(__file__))
while True:
    line = fp.readline()
    if line.startswith('VERSION'):
        exec(line)
        break
print(VERSION)

