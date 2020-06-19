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

# getEpochFromJd(gregorian.to_jd(10000, 1, 1))
G10000_epoch = 253402300800

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


class HMS:
	formats = {
		"HMS": "{h:02d}:{m:02d}:{s:02d}",
		"hMS": "{h}:{m:02d}:{s:02d}",
		"hms": "{h}:{m}:{s}",

		"HM": "{h:02d}:{m:02d}",
		"hm": "{h}:{m}",
		"hM": "{h}:{m:02d}",
	}

	def __init__(self, h=0, m=0, s=0):
		self.h = h
		self.m = m
		self.s = s

	def tuple(self) -> "Tuple[int, int, int]":
		return (self.h, self.m, self.s)

	def __format__(self, fmt=""):
		if fmt in ("", "HM$"):
			# optimization for default format
			return (
				"{h:02d}:{m:02d}" if self.s == 0
				else "{h:02d}:{m:02d}:{s:02d}"
			).format(h=self.h, m=self.m, s=self.s)
		if fmt.endswith("$"):
			if len(fmt) < 2:
				raise ValueError(f"invalid HMS format {fmt!r}")
			if self.s == 0:
				fmt = fmt[:-1]
			elif fmt[-2] < "a":
				fmt = fmt[:-1] + "S"
			else:
				fmt = fmt[:-1] + "s"
		pyfmt = self.formats.get(fmt)
		if pyfmt is None:
			raise ValueError(f"invalid HMS format {fmt!r}")
		return pyfmt.format(h=self.h, m=self.m, s=self.s)


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


def getGtkTimeFromEpoch(epoch: int) -> int:
	return int((epoch - 1321715288.39) * 1000 // 1)


def getFloatJdFromEpoch(epoch, tz: TZ = None) -> float:
	return (epoch + getUtcOffsetByEpoch(epoch, tz)) / (24.0 * 3600) + J1970


def getJdFromEpoch(epoch, tz: TZ = None) -> int:
	return ifloor(getFloatJdFromEpoch(epoch, tz))


def getEpochFromJd(jd, tz: TZ = None) -> int:
	localEpoch = (jd - J1970) * 24 * 3600
	year, month, day = jd_to_g(jd)  # jd or jd-1? FIXME
	return localEpoch - getUtcOffsetByGDate(year, month, day, tz)


def roundEpochToDay(epoch: int) -> int:
	return getEpochFromJd(round(getFloatJdFromEpoch(epoch)))


def getJdListFromEpochRange(startEpoch: int, endEpoch: int) -> List[int]:
	startJd = getJdFromEpoch(startEpoch)
	endJd = getJdFromEpoch(endEpoch - 0.01) + 1
	return list(range(startJd, endJd))


def getHmsFromSeconds(second: int) -> HMS:
	minute, second = divmod(int(second), 60)
	hour, minute = divmod(minute, 60)
	return HMS(hour, minute, second)


def getJhmsFromEpoch(
	epoch: int,
	currentOffset: bool = False,
	tz: TZ = None,
) -> Tuple[int, HMS]:
	# return a tuple (julain_day, hour, minute, second) from epoch
	offset = (
		getUtcOffsetCurrent(tz) if currentOffset
		else getUtcOffsetByEpoch(epoch, tz)
	)
	# ^ FIXME
	days, second = divmod(ifloor(epoch + offset), 24 * 3600)
	return days + J1970, getHmsFromSeconds(second)


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


# type: List[Tuple[int, str]]
durationUnitsRel = (
	(1, "second"),
	(60, "minute"),
	(60, "hour"),
	(24, "day"),
	(7, "week"),
)

durationUnitsAbs = []  # type: List[Tuple[int, str]]
num = 1
for item in durationUnitsRel:
	num *= item[0]
	durationUnitsAbs.append((num, item[1]))

durationUnitValueToName = dict(durationUnitsAbs)  # type: Dict[int, str]
durationUnitValues = [item[0] for item in durationUnitsAbs]  # type: List[int]
durationUnitNames = [item[1] for item in durationUnitsAbs]  # type: List[str]


def timeEncode(
	tm: Union[Tuple[int, int, int], Tuple[int, int]],
) -> str:
	return f"{HMS(*tm)}"


def simpleTimeEncode(
	tm: Union[Tuple[int, int, int], Tuple[int, int], Tuple[int]],
) -> str:
	# FIXME: how to extend HMS formatting to include this conditioning?
	# need a new symbol for "minute, omit if zero", like "$" for second
	if len(tm) == 1:
		return str(int(tm[0]))
	elif len(tm) == 2:
		if tm[1] == 0:
			return str(int(tm[0]))
		else:
			return f"{HMS(*tm)}"
	elif len(tm) == 3:
		return f"{HMS(*tm)}"


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
		raise ValueError(f"bad time '{st}'")
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


def epochGregDateTimeEncode(epoch: int, tz: TZ = None) -> str:
	jd, hms = getJhmsFromEpoch(epoch, tz)
	year, month, day = jd_to_g(jd)
	return f"{year:04d}/{month:02d}/{day:02d} {hms:HMS}"


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

	print(f"default: {HMS(5, 9, 7)}")
	print(f"HMS: {HMS(5, 9, 7):HMS}")
	print(f"HM:  {HMS(5, 9, 7):HM}")
	print(f"hms: {HMS(5, 9, 7):hms}")
	print(f"hm:  {HMS(5, 9, 7):hm}")
	print(f"hMS: {HMS(5, 9, 7):hMS}")
	print(f"hM:  {HMS(5, 9, 7):hM}")
	print(f"HM$: {HMS(5, 9, 7):HM$}")
	print(f"HM$: {HMS(5, 9, 0):HM$}")
	print(f"hm$: {HMS(5, 9, 0):hm$}")
