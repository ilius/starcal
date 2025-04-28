# no logging in this file

import os

os.environ["LOG_LEVEL"] = "10"  # 10=DEBUG

from scal3 import event_lib
from scal3.filesystem import DefaultFileSystem
from scal3.path import confDir

if __name__ == "__main__":
	fs = DefaultFileSystem(confDir)
	event_lib.init(fs)
	event_lib.removeUnusedObjects(fs)
