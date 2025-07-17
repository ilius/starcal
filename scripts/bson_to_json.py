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
	with open(fname_json, "rb") as _file:
		bson_s = _file.read()
	data = bson.loads(bson_s)
	with open(fname + ".json", "w", encoding="utf-8") as _file:
		_file.write(json.dumps(data))
