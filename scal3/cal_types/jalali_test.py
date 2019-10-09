import unittest

import sys;sys.path.append(".")

from scal3.cal_types import jalali


class TestJalali(unittest.TestCase):
	# year -> isLeap33, isLeap2820
	isLeapDict = {
		1360: (False, False),
		1361: (False, False),
		1362: (True, True),
		1363: (False, False),
		1364: (False, False),
		1365: (False, False),
		1366: (True, True),
		1367: (False, False),
		1368: (False, False),
		1369: (False, False),
		1370: (True, True),
		1371: (False, False),
		1372: (False, False),
		1373: (False, False),
		1374: (False, False),
		1375: (True, True),
		1376: (False, False),
		1377: (False, False),
		1378: (False, False),
		1379: (True, True),
		1380: (False, False),
		1381: (False, False),
		1382: (False, False),
		1383: (True, True),
		1384: (False, False),
		1385: (False, False),
		1386: (False, False),
		1387: (True, True),
		1388: (False, False),
		1389: (False, False),
		1390: (False, False),
		1391: (True, True),
		1392: (False, False),
		1393: (False, False),
		1394: (False, False),
		1395: (True, True),
		1396: (False, False),
		1397: (False, False),
		1398: (False, False),
		1399: (True, True),
		1400: (False, False),
		1401: (False, False),
		1402: (False, False),
		1404: (False, True), # FIXME: why mismatch
		1405: (False, False),
		1406: (False, False),
		1407: (False, False),
		1408: (True, True),
	}
	dateToJdDict = {
		#(0, 1, 1): 1947955,
		#(100, 1, 1): 1984479,
		(200, 1, 1): 2021004,
		(300, 1, 1): 2057528,
		(400, 1, 1): 2094052,
		(400, 2, 1): 2094083,
		(1394, 1, 1):  2457103,
		(1394, 2, 1):  2457134,
		(1394, 3, 1):  2457165,
		(1394, 4, 1):  2457196,
		(1394, 5, 1):  2457227,
		(1394, 6, 1):  2457258,
		(1394, 7, 1):  2457289,
		(1394, 8, 1):  2457319,
		(1394, 9, 1):  2457349,
		(1394, 10, 1): 2457379,
		(1394, 11, 1): 2457409,
		(1394, 12, 1): 2457439,
		(1395, 1, 1):  2457468,
		(1395, 2, 1):  2457499,
		(1395, 3, 1):  2457530,
		(1395, 4, 1):  2457561,
		(1395, 5, 1):  2457592,
		(1395, 6, 1):  2457623,
		(1395, 7, 1):  2457654,
		(1395, 8, 1):  2457684,
		(1395, 9, 1):  2457714,
		(1395, 10, 1): 2457744,
		(1395, 11, 1): 2457774,
		(1395, 12, 1): 2457804,
		(1396, 1, 1):  2457834,
		(1396, 2, 1):  2457865,
		(1396, 3, 1):  2457896,
		(1396, 4, 1):  2457927,
		(1396, 5, 1):  2457958,
		(1396, 6, 1):  2457989,
		(1396, 7, 1):  2458020,
		(1396, 8, 1):  2458050,
		(1396, 9, 1):  2458080,
		(1396, 10, 1): 2458110,
		(1396, 11, 1): 2458140,
		(1396, 12, 1): 2458170,
	}

	def test_isLeap(self):
		for alg in range(2):
			for year, isLeapByAlg in self.isLeapDict.items():
				jalali.jalaliAlg = alg
				isLeap = isLeapByAlg[alg]
				isLeapActual = jalali.isLeap(year)
				#if isLeapActual:
				#	print(f"{year} is leap?")
				self.assertEqual(
					isLeapActual,
					isLeap,
					f"year={year}, isLeap={isLeap}, isLeapActual={isLeapActual}",
				)

	def test_to_jd(self):
		for alg in range(2):
			jalali.jalaliAlg = alg
			for date, jd in self.dateToJdDict.items():
				jdActual = jalali.to_jd(*date)
				self.assertEqual(
					jdActual,
					jd,
					f"date={date}, jd={jd}, jdActual={jdActual}",
				)

	def test_convert(self):
		for alg in range(2):
			jalali.jalaliAlg = alg
			startYear = 1360
			endYear = 1450
			for year in range(startYear, endYear):
				for month in range(1, 13):
					monthLen = jalali.getMonthLen(year, month)
					for day in range(1, monthLen + 1):
						date = (year, month, day)
						jd = jalali.to_jd(*date)
						ndate = jalali.jd_to(jd)
						self.assertEqual(
							ndate,
							date,
							f"jd={jd}, date={date}, ndate={ndate}",
						)


if __name__ == "__main__":
	unittest.main()
