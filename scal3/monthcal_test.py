import unittest

import os

from scal3 import locale_man
from scal3.cal_types import calTypes, GREGORIAN


class Test_getMonthDesc(unittest.TestCase):
	def __init__(self, *args):
		unittest.TestCase.__init__(self, *args)
		locale_man.lang = "en_US.UTF-8"
		locale_man.prepareLanguage()
		locale_man.loadTranslator()

	def assertCase(self, year: int, month: int, desc: str):
		from scal3.monthcal import getMonthDesc, getMonthStatus
		self.assertEqual(desc, getMonthDesc(getMonthStatus(year, month)))

	def test_gregorian(self):
		calTypes.activeNames = ["gregorian"]
		calTypes.update()
		self.assertCase(2019, 7, "July 2019")
		self.assertCase(2019, 1, "January 2019")

	def test_gregorian_jalali(self):
		calTypes.activeNames = ["gregorian", "jalali"]
		calTypes.update()
		self.assertCase(2019, 1, "January 2019\nDey and Bahman 1397")
		self.assertCase(2019, 2, "February 2019\nBahman and Esfand 1397")
		self.assertCase(2019, 3, "March 2019\nEsfand 1397 and Farvardin 1398")
		self.assertCase(2019, 4, "April 2019\nFarvardin and Ordibehesht 1398")
		self.assertCase(2019, 5, "May 2019\nOrdibehesht and Khordad 1398")
		self.assertCase(2019, 6, "June 2019\nKhordad and Teer 1398")
		self.assertCase(2019, 7, "July 2019\nTeer and Mordad 1398")
		self.assertCase(2019, 8, "August 2019\nMordad and Shahrivar 1398")
		self.assertCase(2019, 9, "September 2019\nShahrivar and Mehr 1398")
		self.assertCase(2019, 10, "October 2019\nMehr and Aban 1398")
		self.assertCase(2019, 11, "November 2019\nAban and Azar 1398")
		self.assertCase(2019, 12, "December 2019\nAzar and Dey 1398")


if __name__ == "__main__":
	unittest.main()
