# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# Using libkal code
#		The 'libkal' library for date conversion:
#		Copyright (C) 1996-1998 Petr Tomasek <tomasek@etf.cuni.cz>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

name = 'julian'
desc = 'Julian'
origLang = 'en'

from math import floor


def ifloor(x):
	return int(floor(x))

monthName = (
	'January', 'February', 'March',
	'April', 'May', 'June',
	'July', 'August', 'September',
	'October', 'November', 'December',
)

monthNameAb = (
	'Jan', 'Feb', 'Mar',
	'Apr', 'May', 'Jun',
	'Jul', 'Aug', 'Sep',
	'Oct', 'Nov', 'Dec',
)


def getMonthName(m, y=None):
	return monthName[m - 1]


def getMonthNameAb(m, y=None):
	return monthNameAb.__getitem__(m - 1)


def getMonthsInYear(y):
	return 12

epoch = 1721058
minMonthLen = 28
maxMonthLen = 32
avgYearLen = 365.25

options = ()

monthLenSum = (
	0, 31, 59,
	90, 120, 151,
	181, 212, 243,
	273, 304, 334,
	365,
)


def save():
	pass


def isLeap(year):
	return year % 4 == 0


def getYearDays(month, leap):
	"""
	month: int, 1..13
	leap: bool
	"""
	ydays = monthLenSum[month - 1]
	if leap and month < 3:
		ydays -= 1
	return ydays


def getMonthDayFromYdays(yDays, leap):
	"""
	yDays: int, number of days in year
	leap: bool
	"""
	month = 1
	while month < 12 and yDays > getYearDays(month + 1, leap):
		month += 1
	day = yDays - getYearDays(month, leap)
	return month, day


def to_jd(year, month, day):
	quadCount, yMode = divmod(year, 4)
	return (
		epoch +
		1461 * quadCount +
		365 * yMode +
		getYearDays(month, yMode == 0) +
		day
	)


def jd_to(jd):
	"""
	quad: 4 years
	quadCount (p1): quad count
	quadDays (q1): quad remaining days count
	yMode (p2): year % 4
	yDays (q2+1): year remaining days count
	"""

	# wjd = ifloor(jd - 0.5) + 1
	quadCount, quadDays = divmod(jd - epoch, 1461)

	if quadDays == 0:  # first day of quad (and year)
		return (4 * quadCount, 1, 1)

	yMode, yDays = divmod(quadDays - 1, 365)
	yDays += 1
	year = 4 * quadCount + yMode
	month, day = getMonthDayFromYdays(yDays, yMode == 0)

	return (year, month, day)


def getMonthLen(year, month):
	if month == 12:
		return to_jd(year + 1, 1, 1) - to_jd(year, 12, 1)
	else:
		return to_jd(year, month + 1, 1) - to_jd(year, month, 1)
