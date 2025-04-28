# no logging in this file

import json
import sys

from scal3 import event_lib
from scal3.filesystem import DefaultFileSystem
from scal3.json_utils import dataToPrettyJson
from scal3.path import confDir
from scal3.s_object import loadBinaryObject

if __name__ == "__main__":
	fs = DefaultFileSystem(confDir)
	ident = int(sys.argv[1])
	with fs.open(event_lib.EventGroup.getFile(ident)) as fp:
		eventJsonData = json.load(fp)

	lastHash = eventJsonData["history"][0][1]
	data = loadBinaryObject(lastHash, fs)
	print(dataToPrettyJson(data))  # noqa: T201
