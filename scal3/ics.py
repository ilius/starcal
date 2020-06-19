#!/usr/bin/env python3
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

from scal3 import logger
log = logger.get()

from time import strftime, gmtime, strptime, mktime

import sys

from typing import List

from os.path import join, split, splitext

from scal3.path import *
from scal3.cal_types import calTypes, jd_to, to_jd, GREGORIAN


icsTmFormat = "%Y%m%dT%H%M%S"
icsTmFormatPretty = "%Y-%m-%dT%H:%M:%SZ"
# timezone? (Z%Z or Z%z)

icsHeader = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Mozilla.org/NONSGML Mozilla Calendar V1.1//EN
"""

icsWeekDays = ("SU", "MO", "TU", "WE", "TH", "FR", "SA")


def encodeIcsWeekDayList(weekDayList: List[int]) -> str:
	return ",".join([
		icsWeekDays[wd]
		for wd in weekDayList
	])


def getIcsTimeByEpoch(epoch: int, pretty: bool = False) -> str:
	# from scal3.time_utils import getJhmsFromEpoch
	return strftime(
		icsTmFormatPretty if pretty else icsTmFormat,
		gmtime(epoch)
	)
	# format = icsTmFormatPretty if pretty else icsTmFormat
	# jd, hms = getJhmsFromEpoch(epoch)
	# year, month, day = jd_to(jd, GREGORIAN)
	# return strftime(format, (year, month, day, hms.h, hms.m, hms.s, 0, 0, 0))


def getIcsDate(y: int, m: int, d: int, pretty: bool = False) -> str:
	if pretty:
		return f"{y:04d}-{m:02d}-{d:02d}"
	else:
		return f"{y:04d}{m:02d}{d:02d}"


def getIcsDateByJd(jd: int, pretty: bool = False) -> str:
	y, m, d = jd_to(jd, GREGORIAN)
	return getIcsDate(y, m, d, pretty)


def getJdByIcsDate(dateStr: str) -> int:
	tm = strptime(dateStr, "%Y%m%d")
	return to_jd(tm.tm_year, tm.tm_mon, tm.tm_mday, GREGORIAN)


def getEpochByIcsTime(tmStr: str) -> int:
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
#		raise ValueError(f"getEpochByIcsTime: Bad ics time format {tmStr!r}")
#	return int(mktime(tm))


def splitIcsValue(value: str) -> List[str]:
	data = []
	for p in value.split(";"):
		pp = p.split("=")
		if len(pp) == 1:
			data.append([pp[0], ""])
		elif len(pp) == 2:
			data.append(pp)
		else:
			raise ValueError(f"unkown ics value {value!r}")
	return data


def convertHolidayPlugToIcs(
	plug: "BasePlugin",
	startJd: int,
	endJd: int,
	namePostfix: str = "",
) -> None:
	fname = split(plug.fpath)[-1]
	fname = splitext(fname)[0] + f"{namePostfix}.ics"
	plug.exportToIcs(fname, startJd, endJd)


def convertBuiltinTextPlugToIcs(
	plug: "BasePlugin",
	startJd: int,
	endJd: int,
	namePostfix: str = "",
) -> None:
	plug.load() # FIXME
	calType = plug.calType
	icsText = icsHeader
	currentTimeStamp = strftime(icsTmFormat)
	for jd in range(startJd, endJd):
		myear, mmonth, mday = jd_to(jd, calType)
		dayText = plug.getText(myear, mmonth, mday)
		if dayText:
			icsText += "\n".join([
				"BEGIN:VEVEN",
				"CREATED:" + currentTimeStamp,
				"LAST-MODIFIED:" + currentTimeStamp,
				"DTSTART;VALUE=DATE:" + getIcsDateByJd(jd),
				"DTEND;VALUE=DATE:" + getIcsDateByJd(jd + 1),
				"SUMMARY:" + dayText,
				"END:VEVENT",
			]) + "\n"
	icsText += "END:VCALENDAR\n"
	fname = split(plug.fpath)[-1]
	fname = splitext(fname)[0] + f"{namePostfix}.ics"
	open(fname, "w").write(icsText)


# FIXME: what is the purpose of this?
def convertAllPluginsToIcs(startYear: int, endYear: int) -> None:
	if GREGORIAN not in calTypes:
		raise RuntimeError(f"cal type GREGORIAN={GREGORIAN} not found")
	startJd = to_jd(startYear, 1, 1, GREGORIAN)
	endJd = to_jd(endYear + 1, 1, 1, GREGORIAN)
	namePostfix = f"-{startYear}-{endYear}"
	for plug in core.allPlugList:
		if isinstance(plug, HolidayPlugin):
			convertHolidayPlugToIcs(plug, startJd, endJd, namePostfix)
		elif isinstance(plug, BuiltinTextPlugin):
			convertBuiltinTextPlugToIcs(plug, startJd, endJd, namePostfix)
		else:
			log.info("Ignoring unsupported plugin {plug.file}")
