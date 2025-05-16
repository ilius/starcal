from __future__ import annotations

import json
import sys
from typing import Any

from scal3.filesystem import DefaultFileSystem
from scal3.path import confDir
from scal3.s_object import SObjBinaryModel, getObjectPath


def dataToPrettyJson(data: dict[str, Any]) -> str:
	return json.dumps(
		data,
		sort_keys=True,
		indent=4,
		ensure_ascii=False,
	)


if __name__ == "__main__":
	fs = DefaultFileSystem(confDir)
	for hashStr in sys.argv[1:]:
		_dpath, fpath = getObjectPath(hashStr)
		data = SObjBinaryModel.loadData(hashStr, fs)
		# plog.info(data, indent=4, width=80)
		print(f"File: {fpath}")
		print(dataToPrettyJson(data))  # noqa: T201
		print("-------------------")  # noqa: T201
