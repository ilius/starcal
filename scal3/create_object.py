#!/usr/bin/env python3

import sys
import json
from pprint import pprint
from scal3.s_object import saveBsonObject
from scal3.path import confDir
from scal3 import event_lib

if __name__ == "__main__":
	fs = event_lib.DefaultFileSystem(confDir)
	jsonStr = ""
	while True:
		try:
			line = input()
		except EOFError:
			break
		jsonStr += line
	data = json.loads(jsonStr)
	print("-------------------------------")
	_hash = saveBsonObject(data, fs)
	print("Created object with hash:", _hash)
