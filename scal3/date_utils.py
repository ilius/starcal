from __future__ import annotations

import math
from typing import TYPE_CHECKING

from scal3 import cal_types
from scal3.cal_types import GREGORIAN, calTypes, jd_to, to_jd
from scal3.time_utils import getEpochFromJd

if TYPE_CHECKING:
	from collections.abc import Generator


def monthPlus(y: int, m: int, p: int) -> tuple[int, int]:
	y, m = divmod(y * 12 + m - 1 + p, 12)
	return y, m + 1


def dateEncode(date: tuple[int, int, int]) -> str:
	return f"{date[0]:04d}/{date[1]:02d}/{date[2]:02d}"


# def dateEncodeDash(date: tuple[int, int, int]) -> str:
# 	return f"{date[0]:04d}-{date[1]:02d}-{date[2]:02d}"


def checkDate(date: tuple[int, int, int]) -> None:
	if not 1 <= date[1] <= 12:
		raise ValueError(f"bad date '{date}': invalid month")
	if not 1 <= date[2] <= 31:
		raise ValueError(f"bad date '{date}': invalid day")


# FIXME: should return tuple[int, int, int] ?
def dateDecode(st: str) -> list[int]:
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
			f"bad date '{st}': invalid numbers count {len(parts)}",
		)
	try:
		date = [int(p) for p in parts]
	except ValueError:
		raise ValueError(f"bad date '{st}': omitting non-numeric") from None
	if neg:
		date[0] *= -1
	checkDate(date)
	return date


# TODO: move to cal_types/
def validDate(calType: int, year: int, month: int, day: int) -> bool:
	if year < 0:
		return False
	if month < 1 or month > 12:
		return False
	return 1 <= day <= cal_types.getMonthLen(year, month, calType)


def datesDiff(y1: int, m1: int, d1: int, y2: int, m2: int, d2: int) -> int:
	return to_jd(
		calTypes.primary,
		y2,
		m2,
		d2,
	) - to_jd(
		calTypes.primary,
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


def getJdRangeForMonth(year: int, month: int, calType: int) -> tuple[int, int]:
	day = cal_types.getMonthLen(year, month, calType)
	return (
		to_jd(year, month, 1, calType),
		to_jd(year, month, day, calType) + 1,
	)


def getFloatYearFromJd(jd: int, calType: int) -> float:
	if calType not in calTypes:
		raise RuntimeError(f"cal type '{calType}' not found")
	year, _month, _day = jd_to(jd, calType)
	yearStartJd = to_jd(year, 1, 1, calType)
	nextYearStartJd = to_jd(year + 1, 1, 1, calType)
	dayOfYear = jd - yearStartJd
	return year + dayOfYear / (nextYearStartJd - yearStartJd)


def getJdFromFloatYear(fyear: float, calType: int) -> int:
	if calType not in calTypes:
		raise RuntimeError(f"cal type '{calType}' not found")
	year = math.floor(fyear)
	yearStartJd = to_jd(year, 1, 1, calType)
	nextYearStartJd = to_jd(year + 1, 1, 1, calType)
	dayOfYear = int((fyear - year) * (nextYearStartJd - yearStartJd))
	return yearStartJd + dayOfYear


def getEpochFromDate(y: int, m: int, d: int, calType: int) -> int:
	return getEpochFromJd(
		to_jd(
			y,
			m,
			d,
			calType,
		),
	)


def ymdRange(
	date1: tuple[int, int, int],
	date2: tuple[int, int, int],
	calType: int | None = None,
) -> Generator[tuple[int, int, int], None, None]:
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


# def inputDate(msg: str) -> "tuple[int, int, int] | None":
# 	while True:  # OK
# 		try:
# 			date = input(msg)
# 		except KeyboardInterrupt:
# 			return
# 		if date.lower() == "q":
# 			return
# 		try:
# 			return dateDecode(date)
# 		except Exception as e:
# 			log.info(str(e))
