#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# Using kdelibs-4.4.0/kdecore/date/kcalendarsystemgregorianproleptic.cpp
# 		Copyright (C) 2009 John Layt <john@layt.net>
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

from typing import TYPE_CHECKING

from scal3.option import Option

if TYPE_CHECKING:
	from scal3.cal_types.pytypes import OptionTuple, TranslateFunc

__all__ = ["desc", "getMonthLen", "jd_to", "name", "to_jd"]

name = "gregorian_proleptic"
desc = "Gregorian Proleptic"
origLang = "en"

epoch = 1721426
minMonthLen = 29
maxMonthLen = 31
avgYearLen = 365.2425  # FIXME

options: list[OptionTuple] = []

monthName = (
	"January",
	"February",
	"March",
	"April",
	"May",
	"June",
	"July",
	"August",
	"September",
	"October",
	"November",
	"December",
)

monthNameAb = (
	"Jan",
	"Feb",
	"Mar",
	"Apr",
	"May",
	"Jun",
	"Jul",
	"Aug",
	"Sep",
	"Oct",
	"Nov",
	"Dec",
)
monthNameContext: Option[str] = Option("month-name")


def getMonthName(m: int, y: int | None = None) -> str:  # noqa: ARG001
	return monthName[m - 1]


def getMonthNameAb(
	tr: TranslateFunc,
	m: int,
	y: int | None = None,  # noqa: ARG001
) -> str:
	fullEn = monthName[m - 1]
	abbr = tr(fullEn, ctx="abbreviation")
	if abbr != fullEn:
		return abbr
	return monthNameAb[m - 1]


def save() -> None:
	pass


def isLeap(y: int) -> bool:
	if y < 1:
		y += 1
	return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def getMonthLen(year: int, month: int) -> int:
	if month == 2:
		if isLeap(year):
			return 29
		return 28
	if month in {4, 6, 9, 11}:
		return 30
	return 31


def to_jd(year: int, month: int, day: int) -> int:
	# Formula from The Calendar FAQ by Claus Tondering
	# http://www.tondering.dk/claus/cal/node3.html#SECTION003161000000000000000
	# NOTE: Coded from scratch from mathematical formulas, not copied from
	# the Boost licensed source code
	#
	# If year is -ve then is BC. In Gregorian there is no year 0,
	# but the maths is easier if we pretend there is,
	# so internally year of -1 = 1BC = 0 internally
	a = int(month < 3)

	y = year + 4800 - a
	if year < 1:
		y += 1

	m = month + 12 * a - 3

	return 365 * y + y // 4 - y // 100 + y // 400 - 32045 + (153 * m + 2) // 5 + day


def jd_to(jd: int) -> tuple[int, int, int]:
	# Formula from The Calendar FAQ by Claus Tondering
	# http://www.tondering.dk/claus/cal/node3.html#SECTION003161000000000000000
	# NOTE: Coded from scratch from mathematical formulas, not copied from
	# the Boost licensed source code
	a = jd + 32044
	b = (4 * a + 3) // 146097
	c = a - 146097 * b // 4
	d = (4 * c + 3) // 1461
	e = c - 1461 * d // 4
	m = (5 * e + 2) // 153
	day = e - (153 * m + 2) // 5 + 1
	month = m + 3 - 12 * (m // 10)
	year = 100 * b + d - 4800 + (m // 10)
	# If year is -ve then is BC. In Gregorian there is no year 0,
	# but the maths is easier if we pretend there is,
	# so internally year of 0 = 1BC = -1 outside
	if year < 1:
		year -= 1
	return (year, month, day)


"""
bool KCalendarSystemGregorianProleptic::isValid(
	int year,
	int month,
	int day,
) const
{
		if ( year < -4713 || year > 9999 || year == 0 ) {
				return false;
		}

		if ( month < 1 || month > 12 ) {
				return false;
		}

		if ( month == 2 ) {
				if ( isLeapYear( year ) ) {
						return ( day >= 1 && day <= 29 );
				} else {
						return ( day >= 1 && day <= 28 );
				}
		}

		if ( month == 4 || month == 6 || month == 9 || month == 11 ) {
				return ( day >= 1 && day <= 30 );
		}

		return ( day >= 1 && day <= 31 );
}
"""
