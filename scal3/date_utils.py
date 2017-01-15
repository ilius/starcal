import math
from scal3.cal_types import calTypes, to_jd, DATE_GREG
from scal3.time_utils import getEpochFromJd


def getMonthLen(year, month, mode):
	return calTypes[mode].getMonthLen(year, month)


def monthPlus(y, m, p):
	y, m = divmod(y * 12 + m - 1 + p, 12)
	return y, m + 1


def dateEncode(date):
	return "%.4d/%.2d/%.2d" % tuple(date)


def dateEncodeDash(date):
	return "%.4d-%.2d-%.2d" % tuple(date)


def checkDate(date):
	if not 1 <= date[1] <= 12:
		raise ValueError("bad date %s (invalid month)" % date)
	if not 1 <= date[2] <= 31:
		raise ValueError("bad date %s (invalid day)" % date)


def dateDecode(st):
	neg = False
	if st.startswith("-"):
		neg = True
		st = st[1:]
	if "-" in st:
		parts = st.split("-")
	elif "/" in st:
		parts = st.split("/")
	else:
		raise ValueError("bad date %s (invalid seperator)" % st)
	if len(parts) != 3:
		raise ValueError(
			"bad date %s (invalid numbers count %s)" % (st, len(parts))
		)
	try:
		date = [int(p) for p in parts]
	except ValueError:
		raise ValueError("bad date %s (omitting non-numeric)" % st)
	if neg:
		date[0] *= -1
	checkDate(date)
	return date


def validDate(mode, y, m, d):  # move to cal-modules FIXME
	if y < 0:
		return False
	if m < 1 or m > 12:
		return False
	if d > getMonthLen(y, m, mode):
		return False
	return True


def datesDiff(y1, m1, d1, y2, m2, d2):
	return to_jd(
		calType.primary,
		y2,
		m2,
		d2,
	) - to_jd(
		calType.primary,
		y1,
		m1,
		d1,
	)


def dayOfYear(y, m, d):
	return datesDiff(y, 1, 1, y, m, d) + 1


# jwday: Calculate day of week from Julian day
# 0 = Sunday
# 1 = Monday
def jwday(jd):
	return (jd + 1) % 7


def getJdRangeForMonth(year, month, mode):
	day = getMonthLen(year, month, mode)
	return (
		to_jd(year, month, 1, mode),
		to_jd(year, month, day, mode) + 1,
	)


def getFloatYearFromJd(jd, mode):
	module = calTypes[mode]
	year, month, day = module.jd_to(jd)
	yearStartJd = module.to_jd(year, 1, 1)
	nextYearStartJd = module.to_jd(year + 1, 1, 1)
	dayOfYear = jd - yearStartJd
	return year + float(dayOfYear) / (nextYearStartJd - yearStartJd)


def getJdFromFloatYear(fyear, mode):
	module = calTypes[mode]
	year = int(math.floor(fyear))
	yearStartJd = module.to_jd(year, 1, 1)
	nextYearStartJd = module.to_jd(year + 1, 1, 1)
	dayOfYear = int((fyear - year) * (nextYearStartJd - yearStartJd))
	return yearStartJd + dayOfYear


def getEpochFromDate(y, m, d, mode):
	return getEpochFromJd(to_jd(
		y,
		m,
		d,
		mode,
	))


def ymdRange(date1, date2, mode=None):
	y1, m1, d1 = date1
	y2, m2, d2 = date2
	if y1 == y2 and m1 == m2:
		for d in range(d1, d2):
			yield y1, m1, d
	if mode is None:
		mode = DATE_GREG
	calType = calTypes[mode]
	j1 = int(calType.to_jd(y1, m1, d1))
	j2 = int(calType.to_jd(y2, m2, d2))
	for j in range(j1, j2):
		yield calType.jd_to(j)
