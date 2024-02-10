#!/usr/bin/env python3
import json
import sys

for fname in sys.argv[1:]:
	with open(fname) as _file:
		data = json.loads(_file.read())
	jstr = json.dumps(data, sort_keys=True, separators=(",", ":"))
	with open(fname, "w") as _file:
		_file.write(jstr)
