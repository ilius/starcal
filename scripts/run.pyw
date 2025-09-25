#!/usr/bin/env python3
import sys
from os.path import dirname, join

sourceDir = dirname(dirname(__file__))
sys.path.append(sourceDir)
fpath = join(sourceDir, sys.argv[1])
with open(fpath, encoding="utf-8") as file:
    code = compile(file.read(), fpath, "exec")
    exec(code)
