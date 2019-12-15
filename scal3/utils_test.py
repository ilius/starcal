#!/usr/bin/env python3
import unittest
from scal3.utils import versionLessThan

class TestVersionCompare(unittest.TestCase):
	def test_versionLessThan(self):
		self.assertVLessThan("3.1.0", "3.1.1")
		self.assertVLessThan("3.1.9", "3.2.0")
		self.assertVLessThan("3.2.0", "3.11.0")
		self.assertVLessThan("3.2rc0", "3.2")
		self.assertVLessThan("3.2rc0", "3.2.0")
		self.assertVLessThan("3.2rc1", "3.2.0")
		self.assertVLessThan("3.2rc2", "3.2.0")
		self.assertVLessThan("3.1.5", "3.2rc0")
		self.assertVLessThan("3.1.0", "3.2rc1")
		self.assertVLessThan("3.1.9", "3.2rc1")

	def assertVLessThan(self, v1, v2):
		self.assertTrue(versionLessThan(v1, v2))

if __name__ == "__main__":
	unittest.main()
