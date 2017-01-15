# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
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
from time import strftime, gmtime, strptime, mktime

import sys

from os.path import join, split, splitext

from scal3.path import *
from scal3.time_utils import getJhmsFromEpoch
from scal3.cal_types import jd_to, to_jd, DATE_GREG


icsTmFormat = "%Y%m%dT%H%M%S"
icsTmFormatPretty = "%Y-%m-%dT%H:%M:%SZ"
## timezone? (Z%Z or Z%z)

icsHeader = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Mozilla.org/NONSGML Mozilla Calendar V1.1//EN
"""

icsWeekDays = ("SU", "MO", "TU", "WE", "TH", "FR", "SA")


def encodeIcsWeekDayList(weekDayList):
	return ",".join([
		icsWeekDays[wd]
		for wd in weekDayList
	])


def getIcsTimeByEpoch(epoch, pretty=False):
	return strftime(
		icsTmFormatPretty if pretty else icsTmFormat,
		gmtime(epoch)
	)
	#format = icsTmFormatPretty if pretty else icsTmFormat
	#jd, hour, minute, second = getJhmsFromEpoch(epoch)
	#year, month, day = jd_to(jd, DATE_GREG)
	#return strftime(format, (year, month, day, hour, minute, second, 0, 0, 0))


def getIcsDate(y, m, d, pretty=False):
	return ("%.4d-%.2d-%.2d" if pretty else "%.4d%.2d%.2d") % (y, m, d)


def getIcsDateByJd(jd, pretty=False):
	y, m, d = jd_to(jd, DATE_GREG)
	return getIcsDate(y, m, d, pretty)


def getJdByIcsDate(dateStr):
	tm = strptime(dateStr, "%Y%m%d")
	return to_jd(tm.tm_year, tm.tm_mon, tm.tm_mday, DATE_GREG)


def getEpochByIcsTime(tmStr):
	## python-dateutil
	from dateutil.parser import parse
	return int(
		mktime(
			parse(tmStr).timetuple()
		)
	)


#def getEpochByIcsTime(tmStr):
#	utcOffset = 0
#	if "T" in tmStr:
#		if "+" in tmStr or "-" in tmStr:
#			format = "%Y%m%dT%H%M%S%z" ## not working FIXME
#		else:
#			format = "%Y%m%dT%H%M%S"
#	else:
#		format = "%Y%m%d"
#	try:
#		tm = strptime(tmStr, format)
#	except ValueError as e:
#		raise ValueError("getEpochByIcsTime: Bad ics time format "%s""%tmStr)
#	return int(mktime(tm))


def splitIcsValue(value):
	data = []
	for p in value.split(";"):
		pp = p.split("=")
		if len(pp) == 1:
			data.append([pp[0], ""])
		elif len(pp) == 2:
			data.append(pp)
		else:
			raise ValueError("unkown ics value %r" % value)
	return data


def convertHolidayPlugToIcs(plug, startJd, endJd, namePostfix=""):
	fname = split(plug.fpath)[-1]
	fname = splitext(fname)[0] + "%s.ics" % namePostfix
	plug.exportToIcs(fname, startJd, endJd)


def convertBuiltinTextPlugToIcs(plug, startJd, endJd, namePostfix=""):
	plug.load() ## FIXME
	mode = plug.mode
	icsText = icsHeader
	currentTimeStamp = strftime(icsTmFormat)
	for jd in range(startJd, endJd):
		myear, mmonth, mday = jd_to(jd, mode)
		dayText = plug.getText(myear, mmonth, mday)
		if dayText:
			gyear, gmonth, gday = jd_to(jd, DATE_GREG)
			gyear_next, gmonth_next, gday_next = jd_to(jd + 1, DATE_GREG)
			#######
			icsText += "\n".join([
				"BEGIN:VEVEN",
				"CREATED:%s" % currentTimeStamp,
				"LAST-MODIFIED:%s" % currentTimeStamp,
				"DTSTART;VALUE=DATE:%.4d%.2d%.2d" % (
					gyear,
					gmonth,
					gday,
				),
				"DTEND;VALUE=DATE:%.4d%.2d%.2d" % (
					gyear_next,
					gmonth_next,
					gday_next,
				),
				"SUMMARY:%s" % dayText,
				"END:VEVENT",
			]) + "\n"
	icsText += "END:VCALENDAR\n"
	fname = split(plug.fpath)[-1]
	fname = splitext(fname)[0] + "%s.ics" % namePostfix
	open(fname, "w").write(icsText)
