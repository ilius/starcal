import json

from scal3 import event_lib
from scal3.path import confDir
from scal3.s_object import saveBinaryObject

if __name__ == "__main__":
	fs = event_lib.DefaultFileSystem(confDir)
	jsonStr = ""
	while True:  # OK
		try:
			line = input()
		except EOFError:
			break
		jsonStr += line
	data = json.loads(jsonStr)
	print("-------------------------------")  # noqa: T201
	_hash = saveBinaryObject(data, fs)
	print("Created object with hash:", _hash)  # noqa: T201
