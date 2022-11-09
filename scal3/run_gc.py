#!/usr/bin/env python3

# no logging in this file

import os
import sys
import json

os.environ["LOG_LEVEL"] = "10"  # 10=DEBUG

from scal3.s_object import loadBsonObject
from scal3.json_utils import dataToPrettyJson
from scal3 import event_lib
from scal3 import core
from scal3.path import confDir


if __name__ == "__main__":
	fs = event_lib.DefaultFileSystem(confDir)
	event_lib.init(fs)
	event_lib.removeUnusedObjects(fs)
