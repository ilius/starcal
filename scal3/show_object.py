#!/usr/bin/env python3

import sys
import json
from pprint import pprint
from scal3.s_object import loadBsonObject
from scal3.path import confDir
from scal3 import event_lib


def dataToPrettyJson(data):
	return json.dumps(
		data,
		sort_keys=True,
		indent=4,
		ensure_ascii=False,
	)


if __name__ == "__main__":
	fs = event_lib.DefaultFileSystem(confDir)
	for arg in sys.argv[1:]:
		data = loadBsonObject(arg, fs)
		#plog.info(data, indent=4, width=80)
		print(dataToPrettyJson(data))
		print("-------------------")
