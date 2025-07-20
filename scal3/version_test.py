# mypy: ignore-errors
import unittest


def versionLessThan(v0: str, v1: str) -> bool:
	from packaging import version

	return version.parse(v0) < version.parse(v1)


class TestVersionCompare(unittest.TestCase):
	def test_versionLessThan(self) -> None:
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

	def assertVLessThan(self, v1: str, v2: str) -> None:
		self.assertTrue(versionLessThan(v1, v2))
