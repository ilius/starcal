# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# Using kdelibs-4.4.0/kdecore/date/kcalendarsystemindiannational.cpp
#		Copyright (C) 2009 John Layt <john@layt.net>
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

name = "indian_national"
desc = "Indian National"
origLang = "hi"  # or "en" FIXME

monthName = (
	"Chaitra",
	"Vaishākh",
	"Jyaishtha",
	"Āshādha",
	"Shrāvana",
	"Bhādrapad",
	"Āshwin",
	"Kārtik",
	"Agrahayana",
	"Paush",
	"Māgh",
	"Phālgun",
)

monthNameAb = (
	"Cha",
	"Vai",
	"Jya",
	"Āsh",
	"Shr",
	"Bhā",
	"Āsw",
	"Kār",
	"Agr",
	"Pau",
	"Māg",
	"Phā",
)


def getMonthName(m, y=None):
	return monthName[m - 1]


def getMonthNameAb(m, y=None):
	return monthNameAb[m - 1]


def getMonthsInYear(y):
	return 12


# Monday	Somavãra
# Tuesday	Mañgalvã
# Wednesday Budhavãra
# Thursday	Guruvãra
# Friday	Sukravãra
# Saturday	Sanivãra
# Sunday	Raviãra

# Mon	Som
# Tue	Mañ
# Wed	Bud
# Thu	Gur
# Fri	Suk
# Sat	San
# Sun	Rav

epoch = 1749994
minMonthLen = 30
maxMonthLen = 31
avgYearLen = 365.2425  # FIXME


options = ()


def save():
	pass


try:
	from scal3.cal_types import gregorian
except ImportError:
	from . import gregorian


def isLeap(y):
	return gregorian.isLeap(y + 78)


"""bool KCalendarSystemIndianNational::isValid(
	int year,
	int month,
	int day,
) const
{
	if ( year < 0 || year > 9999 ) {
		return false
	}

	if ( month < 1 || month > 12 ) {
		return false
	}

	if ( month == 1 ) {
		if ( isLeapYear( year ) ) {
			return ( day >= 1 && day <= 31 )
		} else {
			return ( day >= 1 && day <= 30 )
		}
	}

	if ( month >= 2 || month <= 6    ) {
		return ( day >= 1 && day <= 31 )
	}

	return ( day >= 1 && day <= 30 )
}
"""


def getMonthLen(y, m):
	if m == 1:
		if isLeap(y):
			return 31
		else:
			return 30
	if 2 <= m <= 6:
		return 31
	return 30


def jd_to(jd):
	# The calendar is closely synchronized to the Gregorian Calendar, always
	# starting on the same day. We can use this and the regular sequence of
	# days in months to do a simple conversion by finding what day in the
	# Gregorian year the Julian Day number is, converting this to the day in
	# the Indian year and subtracting off the required number of months and
	# days to get the final date

	gregorianYear, gregorianMonth, gregorianDay = gregorian.jd_to(jd)
	jdGregorianFirstDayOfYear = gregorian.to_jd(gregorianYear, 1, 1)
	gregorianDayOfYear = jd - jdGregorianFirstDayOfYear + 1

	# There is a fixed 78 year difference between year numbers, but the years
	# do not exactly match up, there is a fixed 80 day difference between the
	# first day of the year, if the Gregorian day of the year is 80 or less
	# then the equivalent Indian day actually falls in the preceding year
	if gregorianDayOfYear > 80:
		year = gregorianYear - 78
	else:
		year = gregorianYear - 79

	# If it is a leap year then the first month has 31 days, otherwise 30.
	if isLeap(year):
		daysInMonth1 = 31
	else:
		daysInMonth1 = 30

	# The Indian year always starts 80 days after the Gregorian year,
	# calculate the Indian day of the year, taking into account if it falls
	# into the previous Gregorian year
	if gregorianDayOfYear > 80:
		indianDayOfYear = gregorianDayOfYear - 80
	else:
		indianDayOfYear = (
			gregorianDayOfYear
			+ daysInMonth1
			+ 5 * 31
			+ 6 * 30
			- 80
		)

	# Then simply remove the whole months from the day of the year and you
	# are left with the day of month
	if indianDayOfYear <= daysInMonth1:
		month = 1
		day = indianDayOfYear
	elif indianDayOfYear <= daysInMonth1 + 5 * 31:
		month = (indianDayOfYear - daysInMonth1 - 1) // 31 + 2
		day = indianDayOfYear - daysInMonth1 - (month - 2) * 31
	else:
		month = (indianDayOfYear - daysInMonth1 - 5 * 31 - 1) // 30 + 7
		day = indianDayOfYear - daysInMonth1 - 5 * 31 - (month - 7) * 30
	return (year, month, day)


def to_jd(year, month, day):
	# The calendar is closely synchronized to the Gregorian Calendar, always
	# starting on the same day We can use this and the regular sequence of days
	# in months to do a simple conversion by finding the Julian Day number of
	# the first day of the year and adding on the required number of months
	# and days to get the final Julian Day number
	# Calculate the jd of 1 Chaitra for this year and how many days are in
	# Chaitra this year If a Leap Year, then 1 Chaitra == 21 March of the
	# Gregorian year and Chaitra has 31 days If not a Leap Year, then
	# 1 Chaitra == 22 March of the Gregorian year and Chaitra has 30 days
	# Need to use dateToJulianDay() to calculate instead of setDate()
	# to avoid the year 9999 validation
	if isLeap(year):
		jdFirstDayOfYear = gregorian.to_jd(year + 78, 3, 21)
		daysInMonth1 = 31
	else:
		jdFirstDayOfYear = gregorian.to_jd(year + 78, 3, 22)
		daysInMonth1 = 30

	# Add onto the jd of the first day of the year the number of days required
	# Calculate the number of days in the months before the required month
	# Then add on the required days
	# The first month has 30 or 31 days depending on if it is a
	# Leap Year (determined above)
	# The second to sixth months have 31 days each
	# The seventh to twelth months have 30 days each
	# Note: could be expressed more efficiently, but I think this is clearer
	if month == 1:
		jd = jdFirstDayOfYear + day - 1
	elif month <= 6:
		jd = (
			jdFirstDayOfYear
			+ daysInMonth1
			+ (month - 2) * 31
			+ day - 1
		)
	else:  # month > 6
		jd = (
			jdFirstDayOfYear
			+ daysInMonth1
			+ 5 * 31
			+ (month - 7) * 30
			+ day - 1
		)
	return jd
