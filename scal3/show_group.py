#!/usr/bin/env python3

# no logging in this file

import os
import sys
import json

from scal3.s_object import loadBsonObject
from scal3.json_utils import dataToPrettyJson
from scal3 import event_lib
from scal3.path import confDir


if __name__ == "__main__":
	fs = event_lib.DefaultFileSystem(confDir)
	_id = int(sys.argv[1])
	with fs.open(event_lib.EventGroup.getFile(_id)) as fp:
		eventJsonData = json.load(fp)

	lastHash = eventJsonData["history"][0][1]
	data = loadBsonObject(lastHash, fs)
	print(dataToPrettyJson(data))
