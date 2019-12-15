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

import time
from time import localtime, mktime
from time import time as now
from datetime import datetime

from typing import Optional, Tuple, List, Dict, Union

import natz

from scal3.cal_types.gregorian import J0001, J1970, J0001_epoch
from scal3.cal_types.gregorian import jd_to as jd_to_g
from scal3.utils import ifloor, iceil

G10000_epoch = 253402300800 # getEpochFromJd(gregorian.to_jd(10000, 1, 1))

TZ = Optional[natz.TimeZone]

# jd is the integer value of Chreonological Julian Day,
# which is specific to time zone
# but epoch time is based on UTC, and not location-dependent

# Time Zone is different from UTC Offset
# Time Zone is a result of UTC Offset + DST

# Using datetime module is not preferred because of
# year limitation (1 to 9999) in TimeLine
# Just use for testing and comparing the result
# Or put in try...except block

# now() ~~ epoch
# function time.time() having the same name as its module is problematic
# don't use time.time() directly again (other than once)

utcOffsetByJdCache = {}
# utcOffsetByJdCache: {tzStr => {jd => utcOffset}}
# utcOffsetByJdCacheSize # FIXME


#def getUtcOffsetByEpoch(epoch: int) -> int:
#	try:
#		return (
#			datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)
#		).total_seconds()
#	except ValueError:## year is out of range
#		return 0


def getUtcOffsetByEpoch(epoch: int, tz: TZ = None) -> int:
	if epoch < J0001_epoch:
		return 0
	if epoch >= G10000_epoch:
		return 0
	if not tz:
		tz = natz.gettz()
	try:
		dt = datetime.fromtimestamp(epoch)
	except ValueError as e:
		log.error(f"epoch={epoch}, error: {e}")
		return 0
	return tz.utcoffset(dt).total_seconds()
	#delta = 0
	#while True:
	#	try:
	#		return tz.utcoffset(
	#			datetime.fromtimestamp(epoch + delta),
	#		).total_seconds()
	#	except AmbiguousTimeError:
	#		## FIXME: do we still get this error with dateutil.tz ?
	#		#d = datetime.fromtimestamp(epoch + 3600)
	#		# log.debug(
	#		#	"AmbiguousTimeError",
	#		#	d.year, d.month, d.day,
	#		#	d.hour, d.minute, d.second,
	#		#)
	#		delta += 3600
	#		log.info(f"delta = {delta}")
	#	except (
	#		ValueError,
	#		OverflowError,
	#	):
	#		return tz._utcoffset.total_seconds()
	#		# tz._utcoffset does not exist with dateutil


def getUtcOffsetByGDate(year: int, month: int, day: int, tz: TZ = None) -> int:
	if year <= 0:
		return 0
	if year >= 10000:
		return 0
	if not tz:
		tz = natz.gettz()
	try:
		dt = datetime(year, month, day)
	except ValueError as e:
		log.error(f"getUtcOffsetByGDate: year={year}, error: {e}")
		return 0
	return tz.utcoffset(dt).total_seconds()

#def getUtcOffsetByJd(jd, tz: TZ = None) -> int:
#	return getUtcOffsetByEpoch(getEpochFromJd(jd), tz)


def getUtcOffsetByJd(jd: int, tz: TZ = None) -> int:
	if not tz:
		tz = natz.gettz()
	tzStr = str(tz)
	# utcOffsetByJdCache: {tzStr => {jd => utcOffset}}
	if jd >= J1970:
		tzDict = utcOffsetByJdCache.get(tzStr)
		if tzDict is None:
			tzDict = utcOffsetByJdCache[tzStr] = {}
		offset = tzDict.get(jd)
		if offset is None:
			y, m, d = jd_to_g(jd)
			offset = tzDict[jd] = getUtcOffsetByGDate(y, m, d, tz)
	else:
		y, m, d = jd_to_g(jd)
		offset = getUtcOffsetByGDate(y, m, d, tz)

	return offset


def getUtcOffsetCurrent(tz: TZ = None) -> int:
	return getUtcOffsetByEpoch(now(), tz)

#def getUtcOffsetCurrent() -> int:
#	return (
#		-time.altzone if time.daylight and localtime().tm_isdst
#		else -time.timezone
#	)


def getGtkTimeFromEpoch(epoch: int) -> int:
	return int((epoch - 1321715288.39) * 1000 // 1)


def getFloatJdFromEpoch(epoch, tz: TZ = None) -> float:
	return (epoch + getUtcOffsetByEpoch(epoch, tz)) / (24.0 * 3600) + J1970
	#return datetime.fromtimestamp(epoch).toordinal() - 1 + J0001


def getJdFromEpoch(epoch, tz: TZ = None) -> int:
	return ifloor(getFloatJdFromEpoch(epoch, tz))


def getEpochFromJd(jd, tz: TZ = None) -> int:
	localEpoch = (jd - J1970) * 24 * 3600
	year, month, day = jd_to_g(jd)  # jd or jd-1? FIXME
	return localEpoch - getUtcOffsetByGDate(year, month, day, tz)

#def getEpochFromJd(jd: int) -> int:
#	return int(mktime(datetime.fromordinal(int(jd) - J0001 + 1).timetuple()))


def roundEpochToDay(epoch: int) -> int:
	return getEpochFromJd(round(getFloatJdFromEpoch(epoch)))


def getJdListFromEpochRange(startEpoch: int, endEpoch: int) -> List[int]:
	startJd = getJdFromEpoch(startEpoch)
	endJd = getJdFromEpoch(endEpoch - 0.01) + 1
	return list(range(startJd, endJd))


def getHmsFromSeconds(second: int) -> Tuple[int, int, int]:
	minute, second = divmod(int(second), 60)
	hour, minute = divmod(minute, 60)
	return hour, minute, second


def getJhmsFromEpoch(
	epoch: int,
	currentOffset: bool = False,
	tz: TZ = None,
) -> Tuple[int, int, int, int]:
	# return a tuple (julain_day, hour, minute, second) from epoch
	offset = (
		getUtcOffsetCurrent(tz) if currentOffset
		else getUtcOffsetByEpoch(epoch, tz)
	) # FIXME
	days, second = divmod(ifloor(epoch + offset), 24 * 3600)
	return (days + J1970,) + getHmsFromSeconds(second)


def getSecondsFromHms(hour: int, minute: int, second: int = 0) -> int:
	return hour * 3600 + minute * 60 + second


def getEpochFromJhms(
	jd: int,
	hour: int,
	minute: int,
	second: int,
	tz: TZ = None,
) -> int:
	return getEpochFromJd(jd, tz) + hour * 3600 + minute * 60 + second


def getJdAndSecondsFromEpoch(epoch: int) -> Tuple[int, int]:
	"""return a tuple (julain_day, extra_seconds) from epoch"""
	days, second = divmod(epoch, 24 * 3600)
	return (days + J1970, second)


durationUnitsRel = (
	(1, "second"),
	(60, "minute"),
	(60, "hour"),
	(24, "day"),
	(7, "week"),
) # type: List[Tuple[int, str]]

durationUnitsAbs = [] # type: List[Tuple[int, str]]
num = 1
for item in durationUnitsRel:
	num *= item[0]
	durationUnitsAbs.append((num, item[1]))

durationUnitValueToName = dict(durationUnitsAbs) # type: Dict[int, str]
durationUnitValues = [item[0] for item in durationUnitsAbs] # type: List[int]
durationUnitNames = [item[1] for item in durationUnitsAbs] # type: List[str]


def timeEncode(
	tm: Union[Tuple[int, int, int], Tuple[int, int]],
	checkSec: bool = False,
) -> str:
	if len(tm) == 2:
		tm = tm + (0,)
	if checkSec:
		if len(tm) == 3 and tm[2] > 0:
			return f"{tm[0]:02d}:{tm[1]:02d}:{tm[2]:02d}"
		else:
			return f"{tm[0]:02d}:{tm[1]:02d}"
	else:
		return f"{tm[0]:02d}:{tm[1]:02d}:{tm[2]:02d}"


def simpleTimeEncode(
	tm: Union[Tuple[int, int, int], Tuple[int, int], Tuple[int]],
) -> str:
	if len(tm) == 1:
		return str(int(tm))
	elif len(tm) == 2:
		if tm[1] == 0:
			return str(int(tm[0]))
		else:
			return f"{tm[0]}:{tm[1]:02d}"
	elif len(tm) == 3:
		if tm[1] == 0:
			if tm[2] == 0:
				return str(int(tm))
			else:
				return f"{tm[0]}:{tm[1]:02d}:{tm[2]:02d}"
		else:
			return f"{tm[0]}:{tm[1]:02d}:{tm[2]:02d}"


def timeDecode(st: str) -> Tuple[int, int, int]:
	parts = st.split(":")
	try:
		tm = tuple([int(p) for p in parts])
	except ValueError:
		raise ValueError(f"bad time '{st}'")
	if len(tm) == 1:
		tm += (0, 0)
	elif len(tm) == 2:
		tm += (0,)
	elif len(tm) != 3:
		raise ValueError(f"bad time '{st}'" )
	return tm


def hmEncode(hm: Tuple[int, int]) -> str:
	return f"{hm[0]:02d}:{hm[1]:02d}"


def hmDecode(st: str) -> Tuple[int, int]:
	parts = st.split(":")
	if len(parts) == 1:
		return (int(parts[0]), 0)
	elif len(parts) == 2:
		return (int(parts[0]), int(parts[1]))
	else:
		raise ValueError(f"bad hour:minute time '{st}'")


def hmsRangeToStr(h1: int, m1: int, s1: int, h2: int, m2: int, s2: int) -> str:
	return timeEncode(
		(h1, m1, s1),
		True,
	) + " - " + timeEncode(
		(h2, m2, s2),
		True,
	)


def epochGregDateTimeEncode(epoch: int, tz: TZ = None) -> str:
	jd, hour, minute, second = getJhmsFromEpoch(epoch, tz)
	year, month, day = jd_to_g(jd)
	return f"{year:04d}/{month:02d}/{day:02d} {hour:02d}:{minute:02d}:{second:02d}"


def encodeJd(jd: int) -> str:
	return epochGregDateTimeEncode(getEpochFromJd(jd))


def durationEncode(value: int, unit: int) -> str:
	iValue = int(value)
	if iValue == value:
		value = iValue
	return str(value) + " " + durationUnitValueToName[unit]


def durationDecode(durStr: str) -> Tuple[int, int]:
	durStr = durStr.strip()
	if " " in durStr:
		value, unit = durStr.split(" ")
		value = float(value)
		unit = unit.lower()
		if not unit:
			return (value, 1)
		for unitValue, unitName in durationUnitsAbs:
			if unit in (unitName, unitName + "s"):  # ,unitName[0]
				return (value, unitValue)
	raise ValueError(f"invalid duration '{durStr}'")


def timeToFloatHour(h: int, m: int, s: int = 0) -> float:
	return h + m / 60.0 + s / 3600.0


def floatHourToTime(fh: float) -> Tuple[int, int, int]:
	h, r = divmod(fh, 1)
	m, r = divmod(r * 60, 1)
	return (
		int(h),
		int(m),
		int(r * 60),
	)


def clockWaitMilliseconds() -> int:
	return int(1000 * (1.01 - now() % 1))


def jsonTimeFromEpoch(epoch: int) -> str:
	tm = datetime.fromtimestamp(epoch, tz=natz.UTC)
	# Python's `datetime` does not support "%:z" format ("+03:30")
	# so we have to set `tz` to None
	return tm.strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
	# log.debug(floatHourToTime(3.6))
	for tm in (
		(8, 0, 0),
		(8, 0),
		(8,),
		(8, 30),
		(8, 30, 55),
		(8, 0, 10),
	):
		log.info(f"{tm!r}, {simpleTimeEncode(tm)!r}")
