import json
import sys

from scal3 import event_lib
from scal3.path import confDir
from scal3.s_object import getObjectPath, loadBinaryObject


def dataToPrettyJson(data):
	return json.dumps(
		data,
		sort_keys=True,
		indent=4,
		ensure_ascii=False,
	)


if __name__ == "__main__":
	fs = event_lib.DefaultFileSystem(confDir)
	for hashStr in sys.argv[1:]:
		_dpath, fpath = getObjectPath(hashStr)
		data = loadBinaryObject(hashStr, fs)
		# plog.info(data, indent=4, width=80)
		print(f"File: {fpath}")
		print(dataToPrettyJson(data))  # noqa: T201
		print("-------------------")  # noqa: T201
