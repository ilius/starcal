#!/usr/bin/env python3

import json
import sys
from os.path import abspath, dirname, join, splitext

sourceDir = dirname(dirname(abspath(__file__)))

sys.path.append(join(sourceDir, "bson"))
import bson

for fname_json in sys.argv[1:]:
	fname, ext = splitext(fname_json)
	bson_s = open(fname_json, "rb").read()
	data = bson.loads(bson_s)
	open(fname + ".json", "w").write(json.dumps(data))
