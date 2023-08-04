import atexit
import os
import sys
import tempfile
import unittest

sys.path.append(".")

from scal3 import event_lib

myTmpDir = tempfile.mkdtemp(prefix="starcal-event_lib_test-")
atexit.register(os.removedirs, myTmpDir)
fs = event_lib.DefaultFileSystem(myTmpDir)

event_lib.init(fs)
eventGroups = event_lib.EventGroupsHolder.load(fs)
eventTrash = event_lib.EventTrash.load(fs)


class TestEventLib(unittest.TestCase):
	pass
