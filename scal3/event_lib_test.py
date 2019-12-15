import unittest

import os
from os.path import join
import tempfile
import atexit

import sys;sys.path.append(".")

from scal3.event_lib import *

myTmpDir = tempfile.mkdtemp(prefix=f"starcal-event_lib_test-")
atexit.register(os.removedirs, myTmpDir)
fs = event_lib.DefaultFileSystem(myTmpDir)

event_lib.init(fs)
eventGroups = event_lib.EventGroupsHolder.load(fs)
eventTrash = event_lib.EventTrash.load(fs)


class TestEventLib(unittest.TestCase):
	pass





