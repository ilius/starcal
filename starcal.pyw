#!/usr/bin/env python3
from os.path import dirname, join

fpath = join(dirname(__file__), "scal3", "ui_gtk", "starcal.py")
with open(fpath, encoding="utf-8") as codeFile:
	exec(codeFile.read())
