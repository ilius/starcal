#!/usr/bin/env python3
import unittest

# import sys; sys.path.append(".")

from scal3.utils import *

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

class TestFindWordByPos(unittest.TestCase):
	def test_findWordByPos(self):
		#     012345678901234567890123456789012345678901234567890123456789
		#    |      |   |       |           |  |   |      | |  |   |     |
		s1 = "Return the integer represented by the string s in the given"
		self.assertEqual(59, len(s1))
		self.assertEqual(findWordByPos(s1, -1), ("", -1))
		self.assertEqual(findWordByPos(s1, 0), ("Return", 0))
		self.assertEqual(findWordByPos(s1, 1), ("Return", 0))
		self.assertEqual(findWordByPos(s1, 2), ("Return", 0))
		self.assertEqual(findWordByPos(s1, 3), ("Return", 0))
		self.assertEqual(findWordByPos(s1, 4), ("Return", 0))
		self.assertEqual(findWordByPos(s1, 5), ("Return", 0))
		self.assertEqual(findWordByPos(s1, 6), ("Return", 0))
		self.assertEqual(findWordByPos(s1, 7), ("the", 7))
		self.assertEqual(findWordByPos(s1, 8), ("the", 7))
		self.assertEqual(findWordByPos(s1, 9), ("the", 7))
		self.assertEqual(findWordByPos(s1, 10), ("the", 7))
		self.assertEqual(findWordByPos(s1, 11), ("integer", 11))
		self.assertEqual(findWordByPos(s1, 12), ("integer", 11))
		self.assertEqual(findWordByPos(s1, 13), ("integer", 11))
		self.assertEqual(findWordByPos(s1, 14), ("integer", 11))
		self.assertEqual(findWordByPos(s1, 15), ("integer", 11))
		self.assertEqual(findWordByPos(s1, 16), ("integer", 11))
		self.assertEqual(findWordByPos(s1, 17), ("integer", 11))
		self.assertEqual(findWordByPos(s1, 18), ("integer", 11))
		self.assertEqual(findWordByPos(s1, 19), ("represented", 19))
		self.assertEqual(findWordByPos(s1, 20), ("represented", 19))
		self.assertEqual(findWordByPos(s1, 21), ("represented", 19))
		self.assertEqual(findWordByPos(s1, 22), ("represented", 19))
		self.assertEqual(findWordByPos(s1, 23), ("represented", 19))
		self.assertEqual(findWordByPos(s1, 24), ("represented", 19))
		self.assertEqual(findWordByPos(s1, 25), ("represented", 19))
		self.assertEqual(findWordByPos(s1, 26), ("represented", 19))
		self.assertEqual(findWordByPos(s1, 27), ("represented", 19))
		self.assertEqual(findWordByPos(s1, 28), ("represented", 19))
		self.assertEqual(findWordByPos(s1, 29), ("represented", 19))
		self.assertEqual(findWordByPos(s1, 30), ("represented", 19))
		self.assertEqual(findWordByPos(s1, 31), ("by", 31))
		self.assertEqual(findWordByPos(s1, 32), ("by", 31))
		self.assertEqual(findWordByPos(s1, 33), ("by", 31))
		self.assertEqual(findWordByPos(s1, 34), ("the", 34))
		self.assertEqual(findWordByPos(s1, 35), ("the", 34))
		self.assertEqual(findWordByPos(s1, 36), ("the", 34))
		self.assertEqual(findWordByPos(s1, 37), ("the", 34))
		self.assertEqual(findWordByPos(s1, 38), ("string", 38))
		self.assertEqual(findWordByPos(s1, 39), ("string", 38))
		self.assertEqual(findWordByPos(s1, 40), ("string", 38))
		self.assertEqual(findWordByPos(s1, 41), ("string", 38))
		self.assertEqual(findWordByPos(s1, 42), ("string", 38))
		self.assertEqual(findWordByPos(s1, 43), ("string", 38))
		self.assertEqual(findWordByPos(s1, 44), ("string", 38))
		self.assertEqual(findWordByPos(s1, 45), ("s", 45))
		self.assertEqual(findWordByPos(s1, 46), ("s", 45))
		self.assertEqual(findWordByPos(s1, 47), ("in", 47))
		self.assertEqual(findWordByPos(s1, 48), ("in", 47))
		self.assertEqual(findWordByPos(s1, 49), ("in", 47))
		self.assertEqual(findWordByPos(s1, 50), ("the", 50))
		self.assertEqual(findWordByPos(s1, 51), ("the", 50))
		self.assertEqual(findWordByPos(s1, 52), ("the", 50))
		self.assertEqual(findWordByPos(s1, 53), ("the", 50))
		self.assertEqual(findWordByPos(s1, 54), ("given", 54))
		self.assertEqual(findWordByPos(s1, 55), ("given", 54))
		self.assertEqual(findWordByPos(s1, 56), ("given", 54))
		self.assertEqual(findWordByPos(s1, 57), ("given", 54))
		self.assertEqual(findWordByPos(s1, 58), ("given", 54))
		self.assertEqual(findWordByPos(s1, 59), ("given", 54))
		self.assertEqual(findWordByPos(s1, 60), ("", -1))
		self.assertEqual(findWordByPos(s1, 61), ("", -1))



if __name__ == "__main__":
	unittest.main()
