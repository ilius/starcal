#!/usr/bin/env python3

import sys
import json
from pprint import pprint
from scal3.s_object import loadBsonObject


def dataToPrettyJson(data):
	return json.dumps(
		data,
		sort_keys=True,
		indent=4,
		ensure_ascii=False,
	)

if __name__ == "__main__":
	for arg in sys.argv[1:]:
		data = loadBsonObject(arg)
		#pprint(data, indent=4, width=80)
		print(dataToPrettyJson(data))
		print("-------------------")
