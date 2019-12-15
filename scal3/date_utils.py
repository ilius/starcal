#!/usr/bin/env python3
import math

from typing import Tuple, List, Optional, Generator

from scal3 import cal_types
from scal3.cal_types import calTypes, to_jd, jd_to, GREGORIAN
from scal3.time_utils import getEpochFromJd


def monthPlus(y: int, m: int, p: int) -> Tuple[int, int]:
	y, m = divmod(y * 12 + m - 1 + p, 12)
	return y, m + 1


def dateEncode(date: Tuple[int, int, int]) -> str:
	return f"{date[0]:04d}/{date[1]:02d}/{date[2]:02d}"


def dateEncodeDash(date: Tuple[int, int, int]) -> str:
	return f"{date[0]:04d}-{date[1]:02d}-{date[2]:02d}"


def checkDate(date: Tuple[int, int, int]) -> None:
	if not 1 <= date[1] <= 12:
		raise ValueError(f"bad date '{date}': invalid month")
	if not 1 <= date[2] <= 31:
		raise ValueError(f"bad date '{date}': invalid day")


# FIXME: should return Tuple[int, int, int] ?
def dateDecode(st: str) -> List[int]:
	neg = False
	if st.startswith("-"):
		neg = True
		st = st[1:]
	if "-" in st:
		parts = st.split("-")
	elif "/" in st:
		parts = st.split("/")
	else:
		raise ValueError(f"bad date '{st}': invalid separator")
	if len(parts) != 3:
		raise ValueError(
			f"bad date '{st}': invalid numbers count {len(parts)}"
		)
	try:
		date = [int(p) for p in parts]
	except ValueError:
		raise ValueError(f"bad date '{st}': omitting non-numeric")
	if neg:
		date[0] *= -1
	checkDate(date)
	return date


# FIXME: move to cal_types/
def validDate(calType: int, y: int, m: int, d: int) -> bool:
	if y < 0:
		return False
	if m < 1 or m > 12:
		return False
	if d > cal_types.getMonthLen(y, m, calType):
		return False
	return True


def datesDiff(y1: int, m1: int, d1: int, y2: int, m2: int, d2: int) -> int:
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


def dayOfYear(y: int, m: int, d: int) -> int:
	return datesDiff(y, 1, 1, y, m, d) + 1


# FIXME: rename this function to weekDayByJd
# jwday: Calculate day of week from Julian day
# 0 = Sunday
# 1 = Monday
def jwday(jd: int) -> int:
	return (jd + 1) % 7


def getJdRangeForMonth(year: int, month: int, calType: int) -> Tuple[int, int]:
	day = cal_types.getMonthLen(year, month, calType)
	return (
		to_jd(year, month, 1, calType),
		to_jd(year, month, day, calType) + 1,
	)


def getFloatYearFromJd(jd: int, calType: int) -> float:
	if calType not in calTypes:
		raise RuntimeError(f"cal type '{calType}' not found")
	year, month, day = jd_to(jd, calType)
	yearStartJd = to_jd(year, 1, 1, calType)
	nextYearStartJd = to_jd(year + 1, 1, 1, calType)
	dayOfYear = jd - yearStartJd
	return year + float(dayOfYear) / (nextYearStartJd - yearStartJd)


def getJdFromFloatYear(fyear: float, calType: int) -> int:
	if calType not in calTypes:
		raise RuntimeError(f"cal type '{calType}' not found")
	year = int(math.floor(fyear))
	yearStartJd = to_jd(year, 1, 1, calType)
	nextYearStartJd = to_jd(year + 1, 1, 1, calType)
	dayOfYear = int((fyear - year) * (nextYearStartJd - yearStartJd))
	return yearStartJd + dayOfYear


def getEpochFromDate(y: int, m: int, d: int, calType: int) -> int:
	return getEpochFromJd(to_jd(
		y,
		m,
		d,
		calType,
	))


def ymdRange(
	date1: Tuple[int, int, int],
	date2: Tuple[int, int, int],
	calType: Optional[int] = None,
) -> Generator[Tuple[int, int, int], None, None]:
	y1, m1, d1 = date1
	y2, m2, d2 = date2
	if y1 == y2 and m1 == m2:
		for d in range(d1, d2):
			yield y1, m1, d
	if calType is None:
		calType = GREGORIAN
	if calType not in calTypes:
		raise RuntimeError(f"cal type '{calType}' not found")
	j1 = int(to_jd(y1, m1, d1, calType))
	j2 = int(to_jd(y2, m2, d2, calType))
	for j in range(j1, j2):
		yield jd_to(j, calType)
