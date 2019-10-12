import unittest

import sys;sys.path.append(".")

from scal3.cal_types import jalali


def lastMonthLenByConvert(year: int) -> int:
	return jalali.to_jd(year + 1, 1, 1) - jalali.to_jd(year, 12, 1)

class TestJalali(unittest.TestCase):
	def notest_isLeap_negativeYear(self):
		print()
		# mismatch between 2 algs in leap years for
		# year <= 780
		# 978 <= year <= 987
		isLeapFunc = jalali.isLeap
		for year in range(10, -101, -1):
			jalali.jalaliAlg = 0
			isLeap1 = isLeapFunc(year)
			jalali.jalaliAlg = 1
			isLeap2 = isLeapFunc(year)
			# print(f"{str(year).center(10)}   {'L' if isLeap1 else ' '}   {'L' if isLeap2 else ' '}")
			print(f"{year}: \"{'L' if isLeap1 else ' '}{'L' if isLeap2 else ' '}\",")


	# year -> f"{'L' if isLeap33 else ' '}{'L' if isLeap2820 else ' '}"
	isLeapDict = {
		10: "  ",
		9:  "L ",
		8:  " L",
		7:  "  ",
		6:  "  ",
		5:  "L ",
		4:  " L",
		3:  "  ",
		2:  "  ",
		1:  "L ",
		0:  " L",
		-1: "  ",
		-2: "  ",
		-3: "L ",
		-4: " L",
		-5: "  ",
		-6: "  ",
		-7: "L ",
		-8: " L",
		-9: "  ",
		-10: "  ",
		-11: "L ",
		-12: "  ",
		-13: " L",
		-14: "  ",
		-15: "  ",
		-16: "L ",
		-17: " L",
		-18: "  ",
		-19: "  ",
		-20: "L ",
		-21: " L",
		-22: "  ",
		-23: "  ",
		-24: "L ",
		-25: " L",
		-26: "  ",
		-27: "  ",
		-28: "L ",
		-29: " L",
		-30: "  ",
		-31: "  ",
		-32: "L ",
		-33: " L",
		-34: "  ",
		-35: "  ",
		-36: "L ",
		-37: " L",
		-38: "  ",
		-39: "  ",
		-40: "L ",
		-41: "  ",
		-42: " L",
		-43: "  ",
		-44: "L ",
		-45: "  ",
		-46: " L",
		-47: "  ",
		-48: "  ",
		-49: "L ",
		-50: " L",
		-51: "  ",
		-52: "  ",
		-53: "L ",
		-54: " L",
		-55: "  ",
		-56: "  ",
		-57: "L ",
		-58: " L",
		-59: "  ",
		-60: "  ",
		-61: "L ",
		-62: " L",
		-63: "  ",
		-64: "  ",
		-65: "L ",
		-66: " L",
		-67: "  ",
		-68: "  ",
		-69: "L ",
		-70: " L",
		-71: "  ",
		-72: "  ",
		-73: "L ",
		-74: "  ",
		-75: " L",
		-76: "  ",
		-77: "L ",
		-78: "  ",
		-79: " L",
		-80: "  ",
		-81: "  ",
		-82: "L ",
		-83: " L",
		-84: "  ",
		-85: "  ",
		-86: "L ",
		-87: " L",
		-88: "  ",
		-89: "  ",
		-90: "L ",
		-91: " L",
		-92: "  ",
		-93: "  ",
		-94: "L ",
		-95: " L",
		-96: "  ",
		-97: "  ",
		-98: "L ",
		-99: " L",
		-100: "  ",


		1360: "  ",
		1361: "  ",
		1362: "LL",
		1363: "  ",
		1364: "  ",
		1365: "  ",
		1366: "LL",
		1367: "  ",
		1368: "  ",
		1369: "  ",
		1370: "LL",
		1371: "  ",
		1372: "  ",
		1373: "  ",
		1374: "  ",
		1375: "LL",
		1376: "  ",
		1377: "  ",
		1378: "  ",
		1379: "LL",
		1380: "  ",
		1381: "  ",
		1382: "  ",
		1383: "LL",
		1384: "  ",
		1385: "  ",
		1386: "  ",
		1387: "LL",
		1388: "  ",
		1389: "  ",
		1390: "  ",
		1391: "LL",
		1392: "  ",
		1393: "  ",
		1394: "  ",
		1395: "LL",
		1396: "  ",
		1397: "  ",
		1398: "  ",
		1399: "LL",
		1400: "  ",
		1401: "  ",
		1402: "  ",
		1404: " L", # FIXME: why mismatch
		1405: "  ",
		1406: "  ",
		1407: "  ",
		1408: "LL",
	}
	dateToJdDict = {
		(0, 1, 1): (1947955, 1947955),
		(100, 1, 1): (1984479, 1984480),  # mismatch
		(200, 1, 1): (2021004, 2021004),
		(300, 1, 1): (2057528, 2057528),
		(400, 1, 1): (2094052, 2094052),
		(400, 2, 1): (2094083, 2094083),
		(1394, 1, 1): (2457103, 2457103),
		(1394, 2, 1): (2457134, 2457134),
		(1394, 3, 1): (2457165, 2457165),
		(1394, 4, 1): (2457196, 2457196),
		(1394, 5, 1): (2457227, 2457227),
		(1394, 6, 1): (2457258, 2457258),
		(1394, 7, 1): (2457289, 2457289),
		(1394, 8, 1): (2457319, 2457319),
		(1394, 9, 1): (2457349, 2457349),
		(1394, 10, 1): (2457379, 2457379),
		(1394, 11, 1): (2457409, 2457409),
		(1394, 12, 1): (2457439, 2457439),
		(1395, 1, 1): (2457468, 2457468),
		(1395, 2, 1): (2457499, 2457499),
		(1395, 3, 1): (2457530, 2457530),
		(1395, 4, 1): (2457561, 2457561),
		(1395, 5, 1): (2457592, 2457592),
		(1395, 6, 1): (2457623, 2457623),
		(1395, 7, 1): (2457654, 2457654),
		(1395, 8, 1): (2457684, 2457684),
		(1395, 9, 1): (2457714, 2457714),
		(1395, 10, 1): (2457744, 2457744),
		(1395, 11, 1): (2457774, 2457774),
		(1395, 12, 1): (2457804, 2457804),
		(1396, 1, 1): (2457834, 2457834),
		(1396, 2, 1): (2457865, 2457865),
		(1396, 3, 1): (2457896, 2457896),
		(1396, 4, 1): (2457927, 2457927),
		(1396, 5, 1): (2457958, 2457958),
		(1396, 6, 1): (2457989, 2457989),
		(1396, 7, 1): (2458020, 2458020),
		(1396, 8, 1): (2458050, 2458050),
		(1396, 9, 1): (2458080, 2458080),
		(1396, 10, 1): (2458110, 2458110),
		(1396, 11, 1): (2458140, 2458140),
		(1396, 12, 1): (2458170, 2458170),
	}

	def test_isLeap(self):
		for alg in range(2):
			jalali.jalaliAlg = alg
			for year, isLeapByAlg in self.isLeapDict.items():
				isLeap = isLeapByAlg[alg] == "L"
				lastMonthLen = lastMonthLenByConvert(year)
				isLeapActual = jalali.isLeap(year)
				lastMonthLenExpected = 29
				if isLeap:
					lastMonthLenExpected = 30
				self.assertEqual(
					isLeapActual,
					isLeap,
					f"year={year}, isLeap={isLeap}, isLeapActual={isLeapActual}, alg={alg}",
				)
				self.assertEqual(
					lastMonthLen,
					lastMonthLenExpected,
					f"year={year}, isLeap={isLeap}, alg={alg}",
				)

	def test_to_jd(self):
		for alg in range(2):
			jalali.jalaliAlg = alg
			for date, jdByAlg in self.dateToJdDict.items():
				jd = jdByAlg[alg]
				jdActual = jalali.to_jd(*date)
				self.assertEqual(
					jdActual,
					jd,
					f"date={date}, jd={jd}, jdActual={jdActual}, alg={alg}",
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
