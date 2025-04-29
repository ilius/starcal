#
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

from scal3 import logger

log = logger.get()

from time import gmtime, mktime, strftime, strptime

from scal3.cal_types import GREGORIAN, jd_to, to_jd

# from scal3.path import

__all__ = [
	"encodeIcsWeekDayList",
	"getEpochByIcsTime",
	"getIcsDateByJd",
	"getIcsTimeByEpoch",
	"icsHeader",
	"icsTmFormat",
]

icsTmFormat = "%Y%m%dT%H%M%S"
icsTmFormatPretty = "%Y-%m-%dT%H:%M:%SZ"
# timezone? (Z%Z or Z%z)

icsHeader = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Mozilla.org/NONSGML Mozilla Calendar V1.1//EN
"""

icsWeekDays = ("SU", "MO", "TU", "WE", "TH", "FR", "SA")


def encodeIcsWeekDayList(weekDayList: list[int]) -> str:
	return ",".join([icsWeekDays[wd] for wd in weekDayList])


def getIcsTimeByEpoch(epoch: int, pretty: bool = False) -> str:
	# from scal3.time_utils import getJhmsFromEpoch
	return strftime(
		icsTmFormatPretty if pretty else icsTmFormat,
		gmtime(epoch),
	)
	# format = icsTmFormatPretty if pretty else icsTmFormat
	# jd, hms = getJhmsFromEpoch(epoch)
	# year, month, day = jd_to(jd, GREGORIAN)
	# return strftime(format, (year, month, day, hms.h, hms.m, hms.s, 0, 0, 0))


def getIcsDate(y: int, m: int, d: int, pretty: bool = False) -> str:
	if pretty:
		return f"{y:04d}-{m:02d}-{d:02d}"
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
			parse(tmStr).timetuple(),
		),
	)


# def getEpochByIcsTime(tmStr):
# 	utcOffset = 0
# 	if "T" in tmStr:
# 		if "+" in tmStr or "-" in tmStr:
# 			format = "%Y%m%dT%H%M%S%z" # not working FIXME
# 		else:
# 			format = "%Y%m%dT%H%M%S"
# 	else:
# 		format = "%Y%m%d"
# 	try:
# 		tm = strptime(tmStr, format)
# 	except ValueError as e:
# 		raise ValueError(f"getEpochByIcsTime: Bad ics time format {tmStr!r}")
# 	return int(mktime(tm))


def splitIcsValue(value: str) -> list[str]:
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
