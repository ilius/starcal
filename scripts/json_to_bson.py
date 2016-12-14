#!/usr/bin/env python3

import sys
from os.path import splitext

import json
from bson import BSON

for fname_json in sys.argv[1:]:
	fname, ext = splitext(fname_json)
	json_s = open(fname_json).read()
	data = json.loads(json_s)
	open(fname + '.bson', 'wb').write(bytes(BSON.encode(data)))




