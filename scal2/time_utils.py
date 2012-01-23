import time
from time import localtime
import datetime
import struct

from scal2.cal_modules.gregorian import J1970

## time() ~~ epoch
## jd == epoch/(24*3600.0) + J1970
## epoch == (jd-J1970)*24*3600
getJdFromEpoch = lambda epoch: int(epoch//(24*3600) + J1970)
getFloatJdFromEpoch = lambda epoch: epoch/(24.0*3600) + J1970

getEpochFromJd = lambda jd: (jd-J1970)*(24*3600)

def getJhmsFromEpoch(epoch, local=False):## return a tuple (julain_day, hour, minute, second) from epoch
    #if local:
    #    epoch -= getCurrentTimeZone()
    (days, second) = divmod(int(epoch), 24*3600)
    (minute, second) = divmod(second, 60)
    (hour, minute) = divmod(minute, 60)
    return (days + J1970, hour, minute, second)

def getSecondsFromHms(hour, minute, second):
    return hour*3600 + minute*60 + second

getEpochFromJhms = lambda jd, hour, minute, second: getEpochFromJd(jd) + getSecondsFromHms(hour, minute, second)

def getJdAndSecondsFromEpoch(epoch):## return a tuple (julain_day, extra_seconds) from epoch
    (days, second) = divmod(epoch, 24*3600)
    return (days + J1970, second)

getTimeZoneByEpoch = lambda epoch: (datetime.datetime.fromtimestamp(epoch) - datetime.datetime.utcfromtimestamp(epoch)).seconds

getTimeZoneByJd = lambda jd: getTimeZoneByEpoch(getEpochFromJd(jd))

getCurrentTimeZone = lambda: getTimeZoneByEpoch(time.time())
#getCurrentTimeZone = lambda: -time.altzone if time.daylight and localtime().tm_isdst else -time.timezone
getCurrentTime = lambda: time.time() + getCurrentTimeZone()
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

def dateEncode(date):
    return '%.4d/%.2d/%.2d'%tuple(date)

def checkDate(date):
    if not 1 <= date[1] <= 12:
        raise ValueError('bad date %s (invalid month)'%st)
    if not 1 <= date[2] <= 31:
        raise ValueError('bad date %s (invalid day)'%st)

def dateDecode(st):
    if '-' in st:
        parts = st.split('-')
    elif '/' in st:
        parts = st.split('/')
    else:
        raise ValueError('bad date %s (invalid seperator)'%st)
    if len(parts)!=3:
        raise ValueError('bad date %s (invalid numbers count)'%st)
    try:
        date = tuple([int(p) for p in parts])
    except ValueError:
        raise ValueError('bad date %s (omitting non-numeric)'%st)
    checkDate(date)
    return date

def timeEncode(tm, checkSec=False):
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
        (value, unit) = durStr.split(' ')
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






