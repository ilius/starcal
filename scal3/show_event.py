
# no logging in this file

import json
import sys

from scal3 import event_lib
from scal3.json_utils import dataToPrettyJson
from scal3.path import confDir
from scal3.s_object import loadBsonObject

if __name__ == "__main__":
	fs = event_lib.DefaultFileSystem(confDir)
	eventId = int(sys.argv[1])
	with fs.open(event_lib.Event.getFile(eventId)) as eventFile:
		eventJsonData = json.load(eventFile)

	lastHash = eventJsonData["history"][0][1]
	data = loadBsonObject(lastHash, fs)
	print(dataToPrettyJson(data))
