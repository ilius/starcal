# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
# Used code from http://code.google.com/p/ethiocalendar/
#				Copyright (C) 2008-2009 Yuji DOI <yuji5296@gmail.com>
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


name = "ethiopian"
desc = "Ethiopian"
origLang = "en" # FIXME

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


def getMonthName(m, y=None):
	return monthName.__getitem__(m - 1)


def getMonthNameAb(m, y=None):
	return monthNameAb.__getitem__(m - 1)


def getMonthsInYear(y):
	return 12


epoch = 1724235
minMonthLen = 30
maxMonthLen = 36
avgYearLen = 365.25

options = ()


def save():
	pass


def isLeap(y):
	return (y + 1) % 4 == 0


def to_jd(year, month, day):
	return (
		epoch
		+ 365 * (year - 1)
		+ year // 4
		+ (month - 1) * 30
		+ day
		- 15
	)


def jd_to(jd):
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


def getMonthLen(year, month):
	if month == 12:
		return 35 + isLeap(year)
	else:
		return monthLen[month - 1]


if __name__ == "__main__":
	import sys
	from . import gregorian
	for gy in range(2012, 1990, -1):
		jd = gregorian.to_jd(gy, 1, 1)
		ey, em, ed = jd_to(jd)
		#if ed==22:
		#	print(gy)
		print("%.4d/%.2d/%.2d\t%.4d/%.2d/%.2d" % (gy, 1, 1, ey, em, ed))
