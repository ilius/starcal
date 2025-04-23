import json
import sys

from scal3 import event_lib
from scal3.path import confDir
from scal3.s_object import loadBinaryObject


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
		data = loadBinaryObject(arg, fs)
		# plog.info(data, indent=4, width=80)
		print(dataToPrettyJson(data))  # noqa: T201
		print("-------------------")  # noqa: T201
