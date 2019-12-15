#!/usr/bin/env python3
import sys
from os.path import dirname, join
sourceDir = dirname(dirname(__file__))
sys.path.append(sourceDir)
execfile(join(sourceDir, sys.argv[1]))
