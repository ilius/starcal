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

import time
from time import localtime, mktime
from time import time as now
from datetime import datetime

import natz
import natz.local

from scal3.cal_types.gregorian import J0001, J1970
from scal3.cal_types.gregorian import jd_to as jd_to_g
from scal3.utils import ifloor, iceil

## jd is the integer value of Chronological Julian Day, which is specific to time zone
## but epoch time is based on UTC, and not location-dependent

## Time Zone is different from UTC Offset
## Time Zone is a result of UTC Offset + DST

## Using datetime module is not preferred because of year limitation (1 to 9999) in TimeLine
## Just use for testing and comparing the result
## Or put in try...except block

## now() ~~ epoch
## function time.time() having the same name as its module is problematic
## don't use time.time() directly again (other than once)

#def getUtcOffsetByEpoch(epoch):
#	try:
#		return (datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)).total_seconds()
#	except ValueError:## year is out of range
#		return 0

def getUtcOffsetByEpoch(epoch, tz=None):
	if not tz:
		tz = natz.local.get_localzone()
	delta = 0
	while True:
		try:
			return tz.utcoffset(datetime.fromtimestamp(epoch + delta)).total_seconds()
		except natz.AmbiguousTimeError:## FIXME
			#d = datetime.fromtimestamp(epoch+3600)
			#print('AmbiguousTimeError', d.year, d.month, d.day, d.hour, d.minute, d.second)
			delta += 3600
			print('delta = %s'%delta)
		except (
			ValueError,
			OverflowError,
		):
			return tz._utcoffset.total_seconds()


def getUtcOffsetByGDate(year, month, day, tz=None):
	if not tz:
		tz = natz.local.get_localzone()
	try:
		return tz.utcoffset(datetime(year, month, day)).total_seconds()
	except (ValueError, OverflowError):
		return tz._utcoffset.total_seconds()
	except natz.NonExistentTimeError:
		return tz.utcoffset(datetime(year, month, day, 1, 0, 0)).total_seconds()


#getUtcOffsetByJd = lambda jd, tz=None: getUtcOffsetByEpoch(getEpochFromJd(jd), tz)

def getUtcOffsetByJd(jd, tz=None):
	y, m, d = jd_to_g(jd)
	return getUtcOffsetByGDate(y, m, d, tz)


getUtcOffsetCurrent = lambda tz=None: getUtcOffsetByEpoch(now(), tz)
#getUtcOffsetCurrent = lambda: -time.altzone if time.daylight and localtime().tm_isdst else -time.timezone

getGtkTimeFromEpoch = lambda epoch: int((epoch-1.32171528839e+9)*1000 // 1)


getFloatJdFromEpoch = lambda epoch, tz=None: \
	(epoch + getUtcOffsetByEpoch(epoch, tz)) / (24.0*3600) + J1970
#getFloatJdFromEpoch = lambda epoch: datetime.fromtimestamp(epoch).toordinal() - 1 + J0001


getJdFromEpoch = lambda epoch, tz=None: ifloor(getFloatJdFromEpoch(epoch, tz))


def getEpochFromJd(jd, tz=None):
	localEpoch = (jd-J1970) * 24*3600
	year, month, day = jd_to_g(jd) ## jd or jd-1? FIXME
	return localEpoch - getUtcOffsetByGDate(year, month, day, tz)

#getEpochFromJd = lambda jd: int(mktime(datetime.fromordinal(int(jd)-J0001+1).timetuple()))

roundEpochToDay = lambda epoch: getEpochFromJd(round(getFloatJdFromEpoch(epoch)))

def getJdListFromEpochRange(startEpoch, endEpoch):
	startJd = getJdFromEpoch(startEpoch)
	endJd = getJdFromEpoch(endEpoch-0.01) + 1
	return list(range(startJd, endJd))

def getHmsFromSeconds(second):
	minute, second = divmod(int(second), 60)
	hour, minute = divmod(minute, 60)
	return hour, minute, second

def getJhmsFromEpoch(epoch, currentOffset=False, tz=None):
	## return a tuple (julain_day, hour, minute, second) from epoch
	offset = getUtcOffsetCurrent(tz) if currentOffset else getUtcOffsetByEpoch(epoch, tz) ## FIXME
	days, second = divmod(ifloor(epoch + offset), 24*3600)
	return (days+J1970,) + getHmsFromSeconds(second)

getSecondsFromHms = lambda hour, minute, second=0: hour*3600 + minute*60 + second

getEpochFromJhms = lambda jd, hour, minute, second, tz=None: \
	getEpochFromJd(jd, tz) + hour*3600 + minute*60 + second

def getJdAndSecondsFromEpoch(epoch):## return a tuple (julain_day, extra_seconds) from epoch
	days, second = divmod(epoch, 24*3600)
	return (days + J1970, second)



durationUnitsRel = (
	(1, 'second'),
	(60, 'minute'),
	(60, 'hour'),
	(24, 'day'),
	(7, 'week'),
)

durationUnitsAbs = []
num = 1
for item in durationUnitsRel:
	num *= item[0]
	durationUnitsAbs.append((num, item[1]))

durationUnitValueToName = dict(durationUnitsAbs)
durationUnitValues = [item[0] for item in durationUnitsAbs]
durationUnitNames = [item[1] for item in durationUnitsAbs]


def timeEncode(tm, checkSec=False):
	if len(tm)==2:
		tm = tm + (0,)
	if checkSec:
		if len(tm)==3 and tm[2]>0:
			return '%.2d:%.2d:%.2d'%tuple(tm)
		else:
			return '%.2d:%.2d'%tuple(tm[:2])
	else:
		return '%.2d:%.2d:%.2d'%tuple(tm)

def simpleTimeEncode(tm):
	if len(tm)==1:
		return '%d'%tm
	elif len(tm)==2:
		if tm[1]==0:
			return '%d'%tm[0]
		else:
			return '%d:%.2d'%tm
	elif len(tm)==3:
		if tm[1]==0:
			if tm[2]==0:
				return '%d'%tm[0]
			else:
				return '%d:%.2d:%.2d'%tm
		else:
			return '%d:%.2d:%.2d'%tm

def timeDecode(st):
	parts = st.split(':')
	try:
		tm = tuple([int(p) for p in parts])
	except ValueError:
		raise ValueError('bad time %s'%st)
	if len(tm)==1:
		tm += (0, 0)
	elif len(tm)==2:
		tm += (0,)
	elif len(tm)!=3:
		raise ValueError('bad time %s'%st)
	return tm

hmEncode = lambda hm: '%.2d:%.2d'%tuple(hm)

def hmDecode(st):
	parts = st.split(':')
	if len(parts)==1:
		return (int(parts[0]), 0)
	elif len(parts)==2:
		return (int(parts[0]), int(parts[1]))
	else:
		raise ValueError('bad hour:minute time %s'%st)


hmsRangeToStr = lambda h1, m1, s1, h2, m2, s2: timeEncode((h1, m1, s1), True) + ' - ' + timeEncode((h2, m2, s2), True)

def epochGregDateTimeEncode(epoch, tz=None):
	jd, hour, minute, second = getJhmsFromEpoch(epoch, tz)
	year, month, day = jd_to_g(jd)
	return '%.4d/%.2d/%.2d %.2d:%.2d:%.2d'%(year, month, day, hour, minute, second)

encodeJd = lambda jd: epochGregDateTimeEncode(getEpochFromJd(jd))

def durationEncode(value, unit):
	iValue = int(value)
	if iValue==value:
		value = iValue
	return '%s %s'%(value, durationUnitValueToName[unit])

def durationDecode(durStr):
	durStr = durStr.strip()
	if ' ' in durStr:
		value, unit = durStr.split(' ')
		value = float(value)
		unit = unit.lower()
		if not unit:
			return (value, 1)
		for unitValue, unitName in durationUnitsAbs:
			if unit in (unitName, unitName+'s'):## ,unitName[0]
				return (value, unitValue)
	raise ValueError('invalid duration %r'%durStr)


timeToFloatHour = lambda h, m, s=0: h + m/60.0 + s/3600.0

def floatHourToTime(fh):
	h, r = divmod(fh, 1)
	m, r = divmod(r*60, 1)
	return (
		int(h),
		int(m),
		int(r*60),
	)

if __name__=='__main__':
	#print(floatHourToTime(3.6))
	for tm in (
		(8, 0, 0),
		(8, 0),
		(8,),
		(8, 30),
		(8, 30, 55),
		(8, 0, 10),
	):
		print('%r, %r'%(tm, simpleTimeEncode(tm)))






