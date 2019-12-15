#!/usr/bin/env python3

import sys
from os.path import join, dirname, abspath, splitext

import json

sourceDir = dirname(dirname(abspath(__file__)))

sys.path.append(join(sourceDir, "bson"))
import bson

for fname_json in sys.argv[1:]:
	fname, ext = splitext(fname_json)
	json_s = open(fname_json).read()
	data = json.loads(json_s)
	open(fname + ".bson", "wb").write(bytes(bson.dumps(data)))
