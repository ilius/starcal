#!/usr/bin/env python3
import sys
from os.path import dirname, join

sourceDir = dirname(dirname(__file__))
sys.path.append(sourceDir)
with open(join(sourceDir, sys.argv[1]), encoding="utf-8") as file:
    exec(file.read())
