#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
# Used code from http://code.google.com/p/ethiocalendar/
# 				Copyright (C) 2008-2009 Yuji DOI <yuji5296@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/lgpl.txt>.
# Also avalable in /usr/share/common-licenses/LGPL on Debian systems
# or /usr/share/licenses/common/LGPL/license.txt on ArchLinux

from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.option import Option

if TYPE_CHECKING:
	from typing import Final

	from scal3.cal_types.pytypes import OptionTuple, TranslateFunc

__all__ = ["desc", "getMonthLen", "jd_to", "name", "to_jd"]

name = "ethiopian"
desc = "Ethiopian"
origLang = "en"

monthName = (
	"Meskerem",
	"Tekimt",
	"Hidar",
	"Tahsas",
	"Ter",
	"Yekoutit",
	"Meyabit",
	"Meyaziya",
	"Genbot",
	"Sene",
	"Hamle",
	"Nahse",
)

monthNameAb = monthName  # FIXME

monthLen = [30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 35]
monthNameContext: Final[Option[str]] = Option("month-name")


def getMonthName(m: int, y: int | None = None) -> str:  # noqa: ARG001
	return monthName[m - 1]


def getMonthNameAb(tr: TranslateFunc, m: int, y: int | None = None) -> str:  # noqa: ARG001
	fullEn = monthName[m - 1]
	abbr = tr(fullEn, ctx="month-name-abbr")
	if abbr != fullEn:
		return abbr
	return monthNameAb[m - 1]


epoch = 1724235
minMonthLen = 30
maxMonthLen = 36
avgYearLen = 365.25

options: list[OptionTuple] = []
optionButtons: list[tuple[str, str, str]] = []


def save() -> None:
	pass


def isLeap(y: int) -> bool:
	return (y + 1) % 4 == 0


def to_jd(year: int, month: int, day: int) -> int:
	return epoch + 365 * (year - 1) + year // 4 + (month - 1) * 30 + day - 15


def jd_to(jd: int) -> tuple[int, int, int]:
	quad, dquad = divmod(jd - epoch, 1461)
	yindex = min(3, dquad // 365)
	year = quad * 4 + yindex + 1

	yearday = jd - to_jd(year, 1, 1)
	month, day = divmod(yearday, 30)
	day += 1
	month += 1
	if month == 13:
		month -= 1
		day += 30
	if month == 12:
		mLen = 35 + isLeap(year)
		if day > mLen:
			year += 1
			month = 1
			day -= mLen

	return year, month, day


def getMonthLen(year: int, month: int) -> int:
	if month == 12:
		return 35 + isLeap(year)
	return monthLen[month - 1]
