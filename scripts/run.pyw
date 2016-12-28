#!/usr/bin/python3
import sys
from os.path import dirname, join
rootDir = dirname(dirname(__file__))
sys.path.append(rootDir)
execfile(join(rootDir, sys.argv[1]))
