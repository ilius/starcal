#!/usr/bin/env python3

import sys
from os.path import splitext

import json
from bson import BSON

for fname_json in sys.argv[1:]:
	fname, ext = splitext(fname_json)
	bson_s = open(fname_json, "rb").read()
	data = BSON.decode(bson_s)
	open(fname + ".json", "w").write(json.dumps(data))
