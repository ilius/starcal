# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2012 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

from time import time, localtime
#from time import timezone, altzone, daylight
import datetime
import struct

from scal2.cal_types.gregorian import J1970
from scal2.utils import ifloor, iceil

## time() ~~ epoch
## jd == epoch/(24*3600.0) + J1970
## epoch == (jd-J1970)*24*3600
getJdFromEpoch = lambda epoch: ifloor(epoch//(24*3600) + J1970)
getFloatJdFromEpoch = lambda epoch: epoch/(24.0*3600) + J1970

getEpochFromJd = lambda jd: (jd-J1970)*(24*3600)

roundEpochToDay = lambda epoch: getEpochFromJd(round(getFloatJdFromEpoch(epoch)))

def getJdListFromEpochRange(startEpoch, endEpoch):
    startJd = getJdFromEpoch(startEpoch)
    endJd = getJdFromEpoch(endEpoch-0.01) + 1
    return range(startJd, endJd)

def getHmsFromSeconds(second):
    minute, second = divmod(int(second), 60)
    hour, minute = divmod(minute, 60)
    return hour, minute, second

def getJhmsFromEpoch(epoch, return_local=False):## return a tuple (julain_day, hour, minute, second) from epoch
    if return_local:
        epoch += getCurrentTimeZone()
    days, second = divmod(ifloor(epoch), 24*3600)
    return (days+J1970,) + getHmsFromSeconds(second)

def getSecondsFromHms(hour, minute, second=0):
    return hour*3600 + minute*60 + second

getEpochFromJhms = lambda jd, hour, minute, second: getEpochFromJd(jd) + getSecondsFromHms(hour, minute, second)

def getJdAndSecondsFromEpoch(epoch):## return a tuple (julain_day, extra_seconds) from epoch
    days, second = divmod(epoch, 24*3600)
    return (days + J1970, second)

def getTimeZoneByEpoch(epoch):
    try:
        return (datetime.datetime.fromtimestamp(epoch) - datetime.datetime.utcfromtimestamp(epoch)).seconds
    except ValueError:## year is out of range
        return 0

getTimeZoneByJd = lambda jd: getTimeZoneByEpoch(getEpochFromJd(jd))

getCurrentTimeZone = lambda: getTimeZoneByEpoch(time())
#getCurrentTimeZone = lambda: -altzone if daylight and localtime().tm_isdst else -timezone
getCurrentTime = lambda: time() + getCurrentTimeZone()
getGtkTimeFromEpoch = lambda epoch: (epoch-1.32171528839e+9)*1000 // 1

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
    #print floatHourToTime(3.6)
    for tm in (
        (8, 0, 0),
        (8, 0),
        (8,),
        (8, 30),
        (8, 30, 55),
        (8, 0, 10),
    ):
        print '%r, %r'%(tm, simpleTimeEncode(tm))






