#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
# Copyright (C) 2007 Mehdi Bayazee <Bayazee@Gmail.com>
# Copyright (C) 2001 Roozbeh Pournader <roozbeh@sharif.edu>
# Copyright (C) 2001 Mohammad Toossi <mohammad@bamdad.org>
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

# Iranian (Jalali) calendar:
# http://en.wikipedia.org/wiki/Iranian_calendar

from __future__ import annotations

from typing import TYPE_CHECKING

from scal3 import logger
from scal3.property import Property

if TYPE_CHECKING:
	from scal3.cal_types.pytypes import TranslateFunc

__all__ = ["desc", "getMonthLen", "isLeap", "jd_to", "name", "to_jd"]


log = logger.get()

name = "jalali"
desc = "Persian"
origLang = "fa"

monthNameMode = Property(0)
options = [
	(
		"monthNameMode",
		list,
		"Month Names",
		("Iranian", "Kurdish/Maadi", "Afghan/Dari", "Pashto"),
	),
]
confParams = {
	"monthNameMode": monthNameMode,
}


monthNameVars = (
	(
		(
			# Iranian
			"Farvardin",
			"Ordibehesht",
			"Khordad",
			"Teer",
			"Mordad",
			"Shahrivar",
			"Mehr",
			"Aban",
			"Azar",
			"Dey",
			"Bahman",
			"Esfand",
		),
		(
			# Iranian - abbreviated
			"Far",
			"Ord",
			"Khr",
			"Tir",
			"Mor",
			"Shr",
			"Meh",
			"Abn",
			"Azr",
			"Dey",
			"Bah",
			"Esf",
		),
	),
	(
		(
			# Kurdish/Maadi
			"Xakelêwe",
			"Gullan",
			"Cozerdan",
			"Pûşper",
			"Gelawêj",
			"Xermanan",
			"Rezber",
			"Gelarêzan",
			"Sermawez",
			"Befranbar",
			"Rêbendan",
			"Reşeme",
		),
	),
	(
		(
			# Afghan/Dari
			"Hamal",
			"Sawr",
			"Jawzā",
			"Saratān",
			"Asad",
			"Sonbola",
			"Mizān",
			"Aqrab",
			"Qaws",
			"Jadi",
			"Dalvæ",
			"Hūt",
		),
	),
	(
		(
			# Pashto
			"Wray",
			"Ǧwayay",
			"Ǧbargolay",
			"Čungāx̌",
			"Zmaray",
			"Waǵay",
			"Təla",
			"Laṛam",
			"Līndəi",
			"Marǧūmay",
			"Salwāǧa",
			"Kab",
		),
	),
)


def getMonthName(
	m: int,
	y: int | None = None,  # noqa: ARG001
) -> str:
	return monthNameVars[monthNameMode.v][0][m - 1]


def getMonthNameAb(
	tr: TranslateFunc,
	m: int,
	y: int | None = None,  # noqa: ARG001
) -> str:
	names = monthNameVars[monthNameMode.v]
	fullEn = names[0][m - 1]
	abbr = tr(fullEn, ctx="abbreviation")
	if abbr != fullEn:
		return abbr
	if len(names) == 2:
		return tr(names[1][m - 1])
	return tr(fullEn)


epoch = 1948321
minMonthLen = 29
maxMonthLen = 31
avgYearLen = 365.2425  # FIXME

GREGORIAN_EPOCH = 1721426
monthLen = (31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 30)

monthLenSum = [0]
for i in range(12):
	monthLenSum.append(monthLenSum[-1] + monthLen[i])

# log.debug(monthLenSum)
# monthLenSum[i] == sum(monthLen[:i])

from bisect import bisect_left

from scal3.config_utils import (
	loadSingleConfig,
	saveSingleConfig,
)
from scal3.path import confDir, sysConfDir

# Here load user options from file
sysConfPath = f"{sysConfDir}/{name}.json"
loadSingleConfig(sysConfPath, confParams)


confPath = f"{confDir}/{name}.json"
loadSingleConfig(confPath, confParams)


def save() -> None:
	"""Save user options to file."""
	saveSingleConfig(
		confPath,
		confParams,
	)


def isLeap(year: int) -> bool:
	"""isLeap: Is a given year a leap year in the Jalali calendar ?."""
	jy = year - 979
	jyd, jym = divmod(jy, 33)
	jyd2, jym2 = divmod(jy + 1, 33)
	return ((jyd2 - jyd) * 8 + (jym2 + 3) // 4 - (jym + 3) // 4) == 1


def getMonthDayFromYdays(yday: int) -> tuple[int, int]:
	month = bisect_left(monthLenSum, yday)
	day = yday - monthLenSum[month - 1]
	return month, day


def to_jd(year: int, month: int, day: int) -> int:
	"""Calculate Julian day from Jalali date."""
	jy = year - 979
	jyd, jym = divmod(jy, 33)
	return (
		365 * jy
		+ jyd * 8
		+ (jym + 3) // 4
		+ monthLenSum[month - 1]
		+ day
		- 1
		+ 584101
		+ GREGORIAN_EPOCH
	)


def jd_to(jd: int) -> tuple[int, int, int]:
	"""Calculate Jalali date from Julian day."""
	assert isinstance(jd, int)
	jdays = jd - GREGORIAN_EPOCH - 584101
	# -(1600*365 + 1600//4 - 1600//100 + 1600//400) + 365-79+1 == -584101
	# log.debug("jdays =", jdays)
	j_np, jdays = divmod(jdays, 12053)

	yearFact, jdays = divmod(jdays, 1461)
	year = 979 + 33 * j_np + 4 * yearFact

	if jdays >= 366:
		yearPlus, jdays = divmod(jdays - 1, 365)
		year += yearPlus
	yday = jdays + 1
	month, day = getMonthDayFromYdays(yday)
	return year, month, day


# Normal: esfand = 29 days
# Leap: esfand = 30 days


def getMonthLen(year: int, month: int) -> int:
	if month == 12:
		return 29 + isLeap(year)

	return monthLen[month - 1]
