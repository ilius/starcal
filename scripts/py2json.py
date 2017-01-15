#!/usr/bin/env python3

import sys
try:
	import json
except ImportError:
	import simplejson as json

from os.path import splitext
from collections import OrderedDict


def dataToPrettyJson(data, ensure_ascii=False):
	return json.dumps(
		data,
		sort_keys=False,
		indent=2,
		ensure_ascii=ensure_ascii,
	)


for fpath_py in sys.argv[1:]:
	text_py = open(fpath_py).read()
	data = OrderedDict()
	exec(text_py, {}, data)
	text_json = dataToPrettyJson(data)
	fpath_nox = splitext(fpath_py)[0]
	fpath_json = fpath_nox + ".json"
	open(fpath_json, "w").write(text_json)
