#!/usr/bin/env python3

import sys

try:
	import json
except ImportError:
	import simplejson as json

from collections import OrderedDict
from os.path import splitext


def dataToPrettyJson(data, ensure_ascii=False):
	return json.dumps(
		data,
		sort_keys=False,
		indent=2,
		ensure_ascii=ensure_ascii,
	)


for fpath_py in sys.argv[1:]:
	with open(fpath_py, encoding="utf-8") as _file:
		text_py = _file.read()
	data = OrderedDict()
	exec(text_py, {}, data)
	text_json = dataToPrettyJson(data)
	fpath_nox = splitext(fpath_py)[0]
	fpath_json = fpath_nox + ".json"
	with open(fpath_json, "w", encoding="utf-8") as _file:
		_file.write(text_json)
