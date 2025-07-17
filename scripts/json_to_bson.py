#!/usr/bin/env python3
# mypy: ignore-errors

import json
import sys
from os.path import abspath, dirname, join, splitext

sourceDir = dirname(dirname(abspath(__file__)))

sys.path.append(join(sourceDir, "bson"))
import bson

for fname_json in sys.argv[1:]:
	fname, ext = splitext(fname_json)
	with open(fname_json, encoding="utf-8") as _file:
		json_s = _file.read()
	data = json.loads(json_s)
	with open(fname + ".bson", "wb") as _file:
		_file.write(bytes(bson.dumps(data)))
