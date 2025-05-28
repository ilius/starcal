# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.

from __future__ import annotations

from scal3 import cal_types, logger
from scal3.cal_types import to_jd
from scal3.locale_man import numDecode
from scal3.time_utils import getEpochFromJd

__all__ = [
	"checkDate",
	"dateDecode",
	"dateEncode",
	"getEpochFromDate",
	"getJdRangeForMonth",
	"jwday",
	"monthPlus",
	"parseDroppedDate",
]


log = logger.get()


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


def dateDecode(st: str) -> tuple[int, int, int]:
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
	ys, ms, ds = parts
	try:
		y, m, d = (int(ys), int(ms), int(ds))
	except ValueError:
		raise ValueError(f"bad date '{st}': omitting non-numeric") from None
	if neg:
		y *= -1
	checkDate((y, m, d))
	return y, m, d


# TODO: move to cal_types/
def validDate(calType: int, year: int, month: int, day: int) -> bool:
	if year < 0:
		return False
	if month < 1 or month > 12:
		return False
	return 1 <= day <= cal_types.getMonthLen(year, month, calType)


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


def getEpochFromDate(y: int, m: int, d: int, calType: int) -> int:
	return getEpochFromJd(
		to_jd(
			y,
			m,
			d,
			calType,
		),
	)


def parseDroppedDate(text: str) -> tuple[int, int, int] | None:
	part = text.split("/")
	if len(part) != 3:
		return None
	try:
		num0 = numDecode(part[0])
		num1 = numDecode(part[1])
		num2 = numDecode(part[2])
	except ValueError:
		log.exception("")
		return None
	del part
	maxPart = max(num0, num1, num2)
	if maxPart <= 999:
		valid = 0 <= num0 <= 99 and 1 <= num1 <= 12 and 1 <= num2 <= 31
		if not valid:
			return None
		return (
			2000 + num0,
			num1,
			num2,
		)

	minMax = (
		(1000, 2100),
		(1, 12),
		(1, 31),
	)
	formats = (
		[0, 1, 2],
		[1, 2, 0],
		[2, 1, 0],
	)
	# "format" must be list because we use method "index"

	nums = [num0, num1, num2]

	def formatIsValid(fmt: list[int]) -> bool:
		for i, num in enumerate(nums):
			f = fmt[i]
			if not (minMax[f][0] <= num <= minMax[f][1]):
				return False
		return True

	for fmt in formats:
		if formatIsValid(fmt):
			return (
				nums[fmt.index(0)],
				nums[fmt.index(1)],
				nums[fmt.index(2)],
			)
	return None

	# FIXME: when drag from a persian GtkCalendar with format %y/%m/%d
	# if year < 100:
	# 	year += 2000
