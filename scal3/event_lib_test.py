import atexit
import shutil
import sys
import tempfile
import unittest

sys.path.append(".")

from scal3 import event_lib
from scal3.s_object import DefaultFileSystem

myTmpDir = tempfile.mkdtemp(prefix="starcal-event_lib_test-")


def removeTempDir():
	print(f"Removing {myTmpDir}")
	shutil.rmtree(myTmpDir)


atexit.register(removeTempDir)
fs = DefaultFileSystem(myTmpDir)

event_lib.init(fs)
print("Loading groups")
eventGroups = event_lib.EventGroupsHolder.load(fs)
print("Loading trash")
eventTrash = event_lib.EventTrash.load(fs)


class TestEventLib(unittest.TestCase):
	pass
