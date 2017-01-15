#!/usr/bin/env python3

import os
import sys
import json

from scal3.s_object import loadBsonObject
from scal3.json_utils import dataToPrettyJson
from scal3 import event_lib


if __name__ == "__main__":
	eventId = int(sys.argv[1])
	with open(event_lib.Event.getFile(eventId)) as eventFile:
		eventJsonData = json.load(eventFile)

	lastHash = eventJsonData["history"][0][1]
	data = loadBsonObject(lastHash)
	print(dataToPrettyJson(data))
