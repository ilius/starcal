#!/usr/bin/env python3

import sys
from os.path import join, dirname, abspath, splitext

import json

rootDir = dirname(dirname(abspath(__file__)))

sys.path.append(join(rootDir, "bson"))
import bson

for fname_json in sys.argv[1:]:
	fname, ext = splitext(fname_json)
	bson_s = open(fname_json, "rb").read()
	data = bson.loads(bson_s)
	open(fname + ".json", "w").write(json.dumps(data))
