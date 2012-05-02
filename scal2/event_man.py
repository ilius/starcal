# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2012 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
#print time(), __file__ ## FIXME

import json, random, os, shutil
from os.path import join, split, isdir, isfile, dirname, splitext
from os import listdir

try:
    from collections import OrderedDict
except:## python < 2.7
    from scal2.lib.ordereddict import OrderedDict

from paths import *

from scal2.utils import arange, ifloor, iceil, IteratorFromGen, findNearestIndex
from scal2.os_utils import makeDir
from scal2.time_utils import *
from scal2.json_utils import *
from scal2.color_utils import hslToRgb
from scal2.ics import *
from scal2.binary_time_line import CenterNode

from scal2.cal_modules import moduleNames, jd_to, to_jd, convert, DATE_GREG, avgYearLength
from scal2.locale_man import tr as _
from scal2.locale_man import getMonthName, textNumEncode
from scal2 import core
from scal2.core import myRaise, getEpochFromJd, getEpochFromJhms, log, getAbsWeekNumberFromJd, dataToJson

from scal2.ics import icsHeader, getIcsTimeByEpoch, getIcsDateByJd, getJdByIcsDate, getEpochByIcsTime

epsTm = 0.01## seconds ## configure somewhere? FIXME
dayLen = 24*3600

icsMinStartYear = 1970
icsMaxEndYear = 2050

eventsDir = join(confDir, 'event', 'events')
groupsDir = join(confDir, 'event', 'groups')
accountsDir = join(confDir, 'event', 'accounts')

makeDir(eventsDir)
makeDir(groupsDir)
makeDir(accountsDir)

###########################################################################

class ClassGroup(list):
    def __init__(self):
        list.__init__(self)
        self.names = []
        self.byName = {}
        self.byDesc = {}
    def register(self, cls):
        assert cls.name != ''
        self.append(cls)
        self.names.append(cls.name)
        self.byName[cls.name] = cls
        self.byDesc[cls.desc] = cls
        return cls

class classes:
    rule = ClassGroup()
    notifier = ClassGroup()
    event = ClassGroup()
    group = ClassGroup()
    account = ClassGroup()

defaultEventTypeIndex = 0 ## FIXME
defaultGroupTypeIndex = 0 ## FIXME

__plugin_api_get__ = [
    'classes', 'defaultEventTypeIndex', 'defaultGroupTypeIndex',
    'EventRule', 'EventNotifier', 'Event', 'EventGroup', 'Account',
]


###########################################################################

class BadEventFile(Exception):## FIXME
    pass

def simplifyNumList(nums, minCount=3):## nums must be sorted, minCount >= 2
    ranges = []
    tmp = []
    for n in nums:
        if tmp and n - tmp[-1] != 1:
            if len(tmp)>minCount:
                ranges.append((tmp[0], tmp[-1]))
            else:
                ranges += tmp
            tmp = []
        tmp.append(n)
    if tmp:
        if len(tmp)>minCount:
            ranges.append((tmp[0], tmp[-1]))
        else:
            ranges += tmp
    return ranges

def cleanTimeRangeList(timeRangeList):
    num = len(timeRangeList)
    i = 0
    while i<num-1:
        if timeRangeList[i][1] == timeRangeList[i+1][0]:
            timeRangeList[i] = (timeRangeList[i][0], timeRangeList[i+1][1])
            timeRangeList.pop(i+1)
            num -= 1
        else:
            i += 1

def intersectionOfTwoTimeRangeList(rList1, rList2):
    #frontiers = []
    frontiers = set()
    for (start, end) in rList1 + rList2:
        frontiers.add(start)
        frontiers.add(end)
    frontiers = sorted(frontiers)
    partsNum = len(frontiers)-1
    partsContained = [[False, False] for i in range(partsNum)]
    for (start, end) in rList1:
        startIndex = frontiers.index(start)
        endIndex = frontiers.index(end)
        for i in range(startIndex, endIndex):
            partsContained[i][0] = True
    for (start, end) in rList2:
        startIndex = frontiers.index(start)
        endIndex = frontiers.index(end)
        for i in range(startIndex, endIndex):
            partsContained[i][1] = True
    result = []
    for i in range(partsNum):
        if partsContained[i][0] and partsContained[i][1]:
            result.append((frontiers[i], frontiers[i+1]))
    #cleanTimeRangeList(result)## not needed when both timeRangeList are clean!
    return result


class EventBaseClass:
    getData = lambda self: None
    setData = lambda self: None
    copyFrom = lambda self, other: self.setData(other.getData())
    def copy(self):
        newObj = self.__class__()
        newObj.copyFrom(self)
        return newObj


class JsonEventBaseClass(EventBaseClass):
    file = ''
    getJson = lambda self: dataToJson(self.getData())
    setJson = lambda self, jsonStr: self.setData(jsonToData(jsonStr))
    def save(self):
        jstr = self.getJson()
        open(self.file, 'w').write(jstr)
    def load(self):
        if not isfile(self.file):
            raise IOError('error while loading json file %r: no such file'%self.file)
        jstr = open(self.file).read()
        if jstr:
            self.setJson(jstr)## FIXME


class Occurrence(EventBaseClass):
    def __init__(self):
        self.event = None
    def __nonzero__(self):
        raise NotImplementedError
    def intersection(self):
        raise NotImplementedError
    getDaysJdList = lambda self: []
    getTimeRangeList = lambda self: []
    def getFloatJdRangeList(self):
        ls = []
        for ep0, ep1 in self.getTimeRangeList():
            if ep1 is None:## FIXME
                ep1 = ep0 + eps
            ls.append((getFloatJdFromEpoch(ep0), getFloatJdFromEpoch(ep1)))
        return ls
    containsMoment = lambda self, epoch: False
    def getStartEpoch(self):
        raise NotImplementedError
    def getEndEpoch(self):
        raise NotImplementedError
    #__iter__ = lambda self: iter(self.getTimeRangeList())

class JdListOccurrence(Occurrence):
    name = 'jdList'
    def __init__(self, jdList=None):
        Occurrence.__init__(self)
        if not jdList:
            jdList = []
        self.jdSet = set(jdList)
    __repr__ = lambda self: 'JdListOccurrence(%r)'%list(self.jdSet)
    __nonzero__ = lambda self: bool(self.jdSet)
    __len__ = lambda self: len(self.jdSet)
    getStartEpoch = lambda self: getEpochFromJd(min(self.jdSet))
    getEndEpoch = lambda self: getEpochFromJd(max(self.jdSet)+1)
    def intersection(self, occur):
        if isinstance(occur, JdListOccurrence):
            return JdListOccurrence(self.jdSet.intersection(occur.jdSet))
        elif isinstance(occur, TimeRangeListOccurrence):
            return TimeRangeListOccurrence(intersectionOfTwoTimeRangeList(self.getTimeRangeList(), occur.getTimeRangeList()))
        elif isinstance(occur, TimeListOccurrence):
            return occur.intersection(self)
        else:
            raise TypeError
    getDaysJdList = lambda self: self.jdSet
    getTimeRangeList = lambda self: [(getEpochFromJd(jd), getEpochFromJd(jd+1)) for jd in self.jdSet]
    containsMoment = lambda self, epoch: (getJdFromEpoch(epoch) in self.jdSet)
    getData = lambda self: list(self.jdSet)
    def setData(self, jdList):
        self.jdSet = set(jdList)
    def calcJdRanges(self):
        jdList = list(self.jdSet) ## jdList is sorted
        if not jdList:
            return []
        startJd = jdList[0]
        endJd = startJd + 1
        jdRanges = []
        for jd in jdList[1:]:
            if jd == endJd:
                endJd += 1
            else:
               jdRanges.append((startJd, endJd))
               startJd = jd
               endJd = startJd + 1
        jdRanges.append((startJd, endJd))
        return jdRanges


class TimeRangeListOccurrence(Occurrence):
    name = 'timeRange'
    def __init__(self, rangeList=None):
        Occurrence.__init__(self)
        if not rangeList:
            rangeList = []
        self.rangeList = rangeList
    __repr__ = lambda self: 'TimeRangeListOccurrence(%r)'%self.rangeList
    __nonzero__ = lambda self: bool(self.rangeList)
    __len__ = lambda self: len(self.rangeList)
    #__getitem__ = lambda i: self.rangeList.__getitem__(i)## FIXME
    getStartEpoch = lambda self: min([r[0] for r in self.rangeList])
    getEndEpoch = lambda self: max([r[1] for r in self.rangeList]+[r[1] for r in self.rangeList])
    def intersection(self, occur):
        if isinstance(occur, (JdListOccurrence, TimeRangeListOccurrence)):
            return TimeRangeListOccurrence(intersectionOfTwoTimeRangeList(self.getTimeRangeList(), occur.getTimeRangeList()))
        elif isinstance(occur, TimeListOccurrence):
            return occur.intersection(self)
        else:
            raise TypeError('bad type %s (%r)'%(occur.__class__.__name__, occur))
    def getDaysJdList(self):
        jdList = []
        for (startEpoch, endEpoch) in self.rangeList:
            for jd in getJdListFromEpochRange(startEpoch, endEpoch):
                if not jd in jdList:
                    jdList.append(jd)
        return jdList
    getTimeRangeList = lambda self: self.rangeList
    def containsMoment(self, epoch):
        for (startEpoch, endEpoch) in self.rangeList:
            if startEpoch <= epoch < endEpoch:
                return True
        return False
    def getData(self):
        return self.rangeList
    def setData(self, rangeList):
        self.rangeList = rangeList


class TimeListOccurrence(Occurrence):
    name = 'repeativeTime'
    def __init__(self, *args):
        Occurrence.__init__(self)
        if len(args)==0:
            self.startEpoch = 0
            self.endEpoch = 0
            self.stepSeconds = -1
            self.epochList = set()
        if len(args)==1:
            self.epochList = set(args[0])
        elif len(args)==3:
            self.setRange(*args)
        else:
            raise ValueError
    __repr__ = lambda self: 'TimeListOccurrence(%r)'%self.epochList
    #__nonzero__ = lambda self: self.startEpoch == self.endEpoch
    __nonzero__ = lambda self: bool(self.epochList)
    getStartEpoch = lambda self: min(self.epochList)
    getEndEpoch = lambda self: max(self.epochList)+1
    def setRange(self, startEpoch, endEpoch, stepSeconds):
        self.startEpoch = startEpoch
        self.endEpoch = endEpoch
        self.stepSeconds = stepSeconds
        self.epochList = set(arange(startEpoch, endEpoch, stepSeconds))
    def intersection(self, occur):
        if isinstance(occur, (JdListOccurrence, TimeRangeListOccurrence)):
            return TimeListOccurrence(self.getMomentsInsideTimeRangeList(occur.getTimeRangeList()))
        elif isinstance(occur, TimeListOccurrence):
            return TimeListOccurrence(self.epochList.intersection(occur.epochList))
        else:
            raise TypeError
    def getDaysJdList(self):## improve performance ## FIXME
        jdList = []
        for epoch in self.epochList:
            jd = getJdFromEpoch(epoch)
            if not jd in jdList:
                jdList.append(jd)
        return jdList
    def getTimeRangeList(self):
        return [(epoch, epoch + epsTm) for epoch in self.epochList]## or end=None ## FIXME
    def containsMoment(self, epoch):## FIXME
        return (epoch in self.epochList)
    def getMomentsInsideTimeRangeList(self, timeRangeList):
        #print 'getMomentsInsideTimeRangeList', timeRangeList, self.epochList
        epochBetween = []
        for epoch in self.epochList:
            for (startEpoch, endEpoch) in timeRangeList:
                if startEpoch <= epoch < endEpoch:
                    epochBetween.append(epoch)
                    break
        return epochBetween
    def setData(self, data):
        self.startEpoch = data['startEpoch']
        self.endEpoch = data['endEpoch']
        self.stepSeconds = data['stepSeconds']
        self.epochList = set(arange(self.startEpoch, self.endEpoch, self.stepSeconds))
    def getData(self):
        return {
            'startEpoch': self.startEpoch,
            'endEpoch': self.endEpoch,
            'stepSeconds': self.stepSeconds,
        }


## Should not be registered, or instantiate directly
class EventRule(EventBaseClass):
    name = ''
    desc = ''
    provide = ()
    need = ()
    conflict = ()
    sgroup = -1
    expand = False
    params = ()
    def __init__(self, parent):## parent can be an event or group
        self.parent = parent
    getMode = lambda self: self.parent.mode
    def changeMode(self, mode):
        return True
    def calcOccurrence(self, startEpoch, endEpoch, event):
        raise NotImplementedError
    def getData(self):
        return dict([(param, getattr(self, param)) for param in self.params])
    def setData(self, data):
        #if isinstance(data, dict):## FIXME
        for (key, value) in data.items():
            if key in self.params:
                setattr(self, key, value)
    getInfo = lambda self: self.desc + ': %s'%self

## Should not be registered, or instantiate directly
class MultiValueEventRule(EventRule):
    #params = ('values',)
    expand = True## FIXME
    def __init__(self, parent):
        EventRule.__init__(self, parent)
        self.values = []
    getData = lambda self: self.values
    def setData(self, data):
        if not isinstance(data, (tuple, list)):
            data = [data]
        self.values = data
    formatValue = lambda self, v: _(v)
    __str__ = lambda self: textNumEncode(numRangesEncode(self.values))
    def hasValue(self, value):
        for item in self.values:
            if isinstance(item, (tuple, list)):
                if item[0] <= value <= item[1]:
                    return True
            else:
                if item == value:
                    return True
        return False
    jdMatches = lambda self, jd: True
    def calcOccurrence(self, startEpoch, endEpoch, event):## improve performance ## FIXME
        jdList = []
        for jd in getJdListFromEpochRange(startEpoch, endEpoch):
            if jd not in jdList and self.jdMatches(jd):
                jdList.append(jd)
        return JdListOccurrence(jdList)
    def getValuesPlain(self):
        ls = []
        for item in self.values:
            if isinstance(item, (tuple, list)):
                ls += range(item[0], item[1]+1)
            else:
                ls.append(item)
        return ls
    def setValuesPlain(self, values):
        self.values = simplifyNumList(values)

@classes.rule.register
class YearEventRule(MultiValueEventRule):
    name = 'year'
    desc = _('Year')
    conflict = ('date',)
    def __init__(self, parent):
        MultiValueEventRule.__init__(self, parent)
        self.values = [core.getSysDate(self.getMode())[0]]
    jdMatches = lambda self, jd: self.hasValue(jd_to(jd, self.getMode())[0])
    def newModeValues(self, newMode):
        curMode = self.getMode()
        yearConv = lambda year: convert(year, 7, 1, curMode, newMode)[0]
        values2 = []
        for item in self.values:
            if isinstance(item, (tuple, list)):
                values2.append((
                    yearConv(item[0]),
                    yearConv(item[1]),
                ))
            else:
                values2.append(yearConv(item))
        return values
    def changeMode(self, mode):
        self.values = self.newModeValues(mode)
        return True

@classes.rule.register
class MonthEventRule(MultiValueEventRule):
    name = 'month'
    desc = _('Month')
    conflict = ('date',)
    def __init__(self, parent):
        MultiValueEventRule.__init__(self, parent)
        self.values = [1]
    jdMatches = lambda self, jd: self.hasValue(jd_to(jd, self.getMode())[1])
    ## overwrite __str__? FIXME
    def changeMode(self, mode):
        return False

@classes.rule.register
class DayOfMonthEventRule(MultiValueEventRule):
    name = 'day'
    desc = _('Day of Month')
    conflict = ('date',)
    def __init__(self, parent):
        MultiValueEventRule.__init__(self, parent)
        self.values = [1]
    jdMatches = lambda self, jd: self.hasValue(jd_to(jd, self.getMode())[2])
    def changeMode(self, mode):
        return False

@classes.rule.register
class WeekNumberModeEventRule(EventRule):
    name = 'weekNumMode'
    desc = _('Week Number')
    need = ('start',)## FIXME
    conflict = ('date',)
    params = ('weekNumMode',)
    (EVERY_WEEK, ODD_WEEKS, EVEN_WEEKS) = range(3) ## remove EVERY_WEEK? FIXME
    weekNumModeNames = ('any', 'odd', 'even')## remove 'any'? FIXME
    def __init__(self, parent):
        EventRule.__init__(self, parent)
        self.weekNumMode = self.EVERY_WEEK
    getData = lambda self: self.weekNumModeNames[self.weekNumMode]
    def setData(self, modeName):
        if not modeName in self.weekNumModeNames:
            raise BadEventFile('bad rule weekNumMode=%r, the value for weekNumMode must be one of %r'\
                %(modeName, self.weekNumModeNames))
        self.weekNumMode = self.weekNumModeNames.index(modeName)
    def calcOccurrence(self, startEpoch, endEpoch, event):## improve performance ## FIXME
        startAbsWeekNum = getAbsWeekNumberFromJd(event['start'].getJd()) - 1 ## 1st week ## FIXME
        jdListAll = getJdListFromEpochRange(startEpoch, endEpoch)
        if self.weekNumMode==self.EVERY_WEEK:
            jdList = jdListAll
        elif self.weekNumMode==self.ODD_WEEKS:
            jdList = []
            for jd in jdListAll:
                if (getAbsWeekNumberFromJd(jd)-startAbsWeekNum)%2==1:
                    jdList.append(jd)
        elif self.weekNumMode==self.EVEN_WEEKS:
            jdList = []
            for jd in jdListAll:
                if (getAbsWeekNumberFromJd(jd)-startAbsWeekNum)%2==0:
                    jdList.append(jd)
        return JdListOccurrence(jdList)
    def getInfo(self):
        if self.weekNumMode == self.EVERY_WEEK:
            return ''
        elif self.weekNumMode == self.ODD_WEEKS:
            return _('Odd Weeks')
        elif self.weekNumMode == self.EVEN_WEEKS:
            return _('Even Weeks')

@classes.rule.register
class WeekDayEventRule(EventRule):
    name = 'weekDay'
    desc = _('Day of Week')
    conflict = ('date',)
    params = ('weekDayList',)
    def __init__(self, parent):
        EventRule.__init__(self, parent)
        self.weekDayList = range(7) ## or [] ## FIXME
    def getData(self):
        return self.weekDayList
    def setData(self, data):
        if isinstance(data, int):
            self.weekDayList = [data]
        elif isinstance(data, (tuple, list)):
            self.weekDayList = data
        else:
            raise BadEventFile('bad rule weekDayList=%s, value for weekDayList must be a list of integers (0 for sunday)'%data)
    def calcOccurrence(self, startEpoch, endEpoch, event):## improve performance ## FIXME
        jdList = []
        for jd in getJdListFromEpochRange(startEpoch, endEpoch):
            if core.jwday(jd) in self.weekDayList and not jd in jdList:
                jdList.append(jd)
        return JdListOccurrence(jdList)
    def getInfo(self):
        if self.weekDayList == range(7):
            return ''
        sep = _(',') + ' '
        sep2 = ' ' + _('or') + ' '
        return _('Day of Week') + ': ' + \
               sep.join([core.weekDayName[wd] for wd in self.weekDayList[:-1]]) + \
               sep2 + core.weekDayName[self.weekDayList[-1]]

@classes.rule.register
class DateEventRule(EventRule):
    name = 'date'
    desc = _('Date')
    need = ()
    conflict = (
        'year', 'month', 'day', 'weekNumMode', 'weekDay'
        'start', 'end', 'cycleDays', 'duration', 'cycleLen'
    )## all rules except for dayTime and dayTimeRange (and possibly hourList, minuteList, secondList)
    ## also conflict with 'holiday' ## FIXME
    __str__ = lambda self: dateEncode(self.date)
    def __init__(self, parent):
        EventRule.__init__(self, parent)
        self.date = core.getSysDate(self.getMode())
    getData = lambda self: str(self)
    def setData(self, data):
        self.date = dateDecode(data)
    def getJd(self):
        (year, month, day) = self.date
        return to_jd(year, month, day, self.getMode())
    getEpoch = lambda self: getEpochFromJd(self.getJd())
    def setJd(self, jd):
        self.date = jd_to(jd, self.getMode())
    def calcOccurrence(self, startEpoch, endEpoch, event):
        myJd = self.getJd()
        myStartEpoch = getEpochFromJd(myJd)
        myEndEpoch = getEpochFromJd(myJd+1)
        if startEpoch <= myStartEpoch and myEndEpoch <= endEpoch:
            return JdListOccurrence([myJd])
        startEpoch = max(startEpoch, myStartEpoch)
        endEpoch = min(endEpoch, myEndEpoch)
        if endEpoch >= startEpoch:
            return TimeRangeListOccurrence(
                [
                    (startEpoch, endEpoch),
                ]
            )
        else:
            return TimeRangeListOccurrence()
    def changeMode(self, mode):
        self.date = jd_to(self.getJd(), mode)
        return True

class DateAndTimeEventRule(DateEventRule):
    sgroup = 1
    params = ('date', 'time')
    def __init__(self, parent):
        DateEventRule.__init__(self, parent)
        self.time = localtime()[3:6]
    getEpoch = lambda self: getEpochFromJhms(self.getJd(), *tuple(self.time))
    getDate = lambda self, mode: convert(self.date[0], self.date[1], self.date[2], self.mode, mode)
    getData = lambda self: {
        'date': dateEncode(self.date),
        'time': timeEncode(self.time),
    }
    def setData(self, arg):
        if isinstance(arg, dict):
            self.date = dateDecode(arg['date'])
            if arg.has_key('time'):
                self.time = timeDecode(arg['time'])
        elif isinstance(arg, basestring):
            self.date = dateDecode(arg)
        else:
            raise BadEventFile('bad rule %s=%r'%(self.name, arg))
    getInfo = lambda self: self.desc + ': ' + dateEncode(self.date) + _(',') + ' ' + _('Time') + ': ' + timeEncode(self.time)



@classes.rule.register
class DayTimeEventRule(EventRule):## Moment Event
    name = 'dayTime'
    desc = _('Time in Day')
    provide = ('time',)
    conflict = ('dayTimeRange', 'cycleLen',)
    params = ('dayTime',)
    def __init__(self, parent):
        EventRule.__init__(self, parent)
        self.dayTime = localtime()[3:6]
    getData = lambda self: timeEncode(self.dayTime)
    def setData(self, data):
        self.dayTime = timeDecode(data)
    def calcOccurrence(self, startEpoch, endEpoch, event):
        mySec = core.getSecondsFromHms(*self.dayTime)
        (startJd, startExtraSec) = core.getJdAndSecondsFromEpoch(startEpoch)
        (endJd, endExtraSec) = core.getJdAndSecondsFromEpoch(endEpoch)
        if startExtraSec > mySec:
            startJd += 1
        if endExtraSec < mySec:
            endJd -= 1
        return TimeListOccurrence(## FIXME
            getEpochFromJd(startJd) + mySec,
            getEpochFromJd(endJd) + mySec + 1,
            dayLen,
        )
    getInfo = lambda self: _('Time in Day') + ': ' + timeEncode(self.dayTime)

@classes.rule.register
class DayTimeRangeEventRule(EventRule):
    name = 'dayTimeRange'
    desc = _('Day Time Range')
    conflict = ('dayTime', 'cycleLen',)
    params = ('dayTimeStart', 'dayTimeEnd')
    def __init__(self, parent):
        EventRule.__init__(self, parent)
        self.dayTimeStart = (0, 0, 0)
        self.dayTimeEnd = (24, 0, 0)
    def setRange(self, start, end):
        self.dayTimeStart = tuple(start)
        self.dayTimeEnd = tuple(end)
    getHourRange = lambda self: (
        timeToFloatHour(*self.dayTimeStart),
        timeToFloatHour(*self.dayTimeEnd),
    )
    getSecondsRange = lambda self: (
        getSecondsFromHms(*self.dayTimeStart),
        getSecondsFromHms(*self.dayTimeEnd),
    )
    getData = lambda self: (timeEncode(self.dayTimeStart), timeEncode(self.dayTimeEnd))
    setData = lambda self, data: self.setRange(timeDecode(data[0]), timeDecode(data[1]))
    def calcOccurrence(self, startEpoch, endEpoch, event):
        daySecStart = getSecondsFromHms(*self.dayTimeStart)
        daySecEnd = getSecondsFromHms(*self.dayTimeEnd)
        startDiv = int(startEpoch//dayLen)
        endDiv = int(endEpoch//dayLen)
        return TimeRangeListOccurrence(intersectionOfTwoTimeRangeList(
            [(i*dayLen+daySecStart, i*dayLen+daySecEnd) for i in range(startDiv, endDiv+1)],
            [(startEpoch, endEpoch)],
        ))


@classes.rule.register
class StartEventRule(DateAndTimeEventRule):
    name = 'start'
    desc = _('Start')
    conflict = ('date',)
    def calcOccurrence(self, startEpoch, endEpoch, event):
        myEpoch = self.getEpoch()
        if endEpoch <= myEpoch:
            return TimeRangeListOccurrence([])
        if startEpoch < myEpoch:
            startEpoch = myEpoch
        return TimeRangeListOccurrence([(startEpoch, endEpoch)])

@classes.rule.register
class EndEventRule(DateAndTimeEventRule):
    name = 'end'
    desc = _('End')
    conflict = ('date', 'duration',)
    def calcOccurrence(self, startEpoch, endEpoch, event):
        endEpoch = min(endEpoch, self.getEpoch())
        if startEpoch >= endEpoch:## how about startEpoch==endEpoch FIXME
            return TimeRangeListOccurrence([])
        else:
            return TimeRangeListOccurrence([(startEpoch, endEpoch)])

@classes.rule.register
class DurationEventRule(EventRule):
    name = 'duration'
    desc = _('Duration')
    need = ('start',)
    conflict = ('date', 'end',)
    sgroup = 1
    def __init__(self, parent):
        EventRule.__init__(self, parent)
        self.value = 0
        self.unit = 1 ## seconds
    getSeconds = lambda self: self.value * self.unit
    def setData(self, data):
        try:
            (self.value, self.unit) = durationDecode(data)
        except Exception, e:
            log.error('Error while loading event rule "%s": %s'%(self.name, e))
    getData = lambda self: durationEncode(self.value, self.unit)
    def calcOccurrence(self, startEpoch, endEpoch, event):
        endEpoch = min(endEpoch, self.event['start'].getEpoch() + self.getSeconds())
        if startEpoch >= endEpoch:## how about startEpoch==endEpoch FIXME
            return TimeRangeListOccurrence([])
        else:
            return TimeRangeListOccurrence([(startEpoch, endEpoch)])

@classes.rule.register
class CycleDaysEventRule(EventRule):
    name = 'cycleDays'
    desc = _('Cycle Days Number')
    need = ('start',)
    conflict = ('date', 'cycleLen')
    params = ('cycleDays',)
    def __init__(self, parent):
        EventRule.__init__(self, parent)
        self.cycleDays = 7
    getData = lambda self: self.cycleDays
    def setData(self, cycleDays):
        self.cycleDays = cycleDays
    def calcOccurrence(self, startEpoch, endEpoch, event):## improve performance ## FIXME
        startJd = max(event['start'].getJd(), core.getJdFromEpoch(startEpoch))
        endJd = core.getJdFromEpoch(endEpoch - epsTm) + 1
        return JdListOccurrence(range(startJd, endJd, self.cycleDays))
    getInfo = lambda self: _('Repeat: Every %s Days')%_(self.cycleDays)

@classes.rule.register
class CycleLenEventRule(EventRule):
    name = 'cycleLen'
    desc = _('Cycle Length (Days & Time)')
    provide = ('time',)
    need = ('start',)
    conflict = ('date', 'dayTime', 'dayTimeRange', 'cycleDays',)
    params = ('cycleDays', 'cycleExtraTime',)
    def __init__(self, parent):
        EventRule.__init__(self, parent)
        self.cycleDays = 7
        self.cycleExtraTime = (0, 0, 0)
    def getData(self):
        return {
            'days': self.cycleDays,
            'extraTime': timeEncode(self.cycleExtraTime)
        }
    def setData(self, arg):
        self.cycleDays = arg['days']
        self.cycleExtraTime = timeDecode(arg['extraTime'])
    def calcOccurrence(self, startEpoch, endEpoch, event):
        startEpoch = max(startEpoch, self.event['start'].getEpoch())
        cycleSec = self.cycleDays*dayLen + core.getSecondsFromHms(*self.cycleExtraTime)
        return TimeListOccurrence(startEpoch, endEpoch, cycleSec)
    getInfo = lambda self: _('Repeat: Every %s Days and %s')%(_(self.cycleDays), timeEncode(self.cycleExtraTime))

@classes.rule.register
class ExYearEventRule(YearEventRule):
    name = 'ex_year'
    desc = '[%s] %s'%(_('Exception'), _('Year'))
    conflict = ('date',)
    jdMatches = lambda self, jd: not YearEventRule.jdMatches(self, jd)

@classes.rule.register
class ExMonthEventRule(MonthEventRule):
    name = 'ex_month'
    desc = '[%s] %s'%(_('Exception'), _('Month'))
    conflict = ('date',)
    jdMatches = lambda self, jd: not MonthEventRule.jdMatches(self, jd)

@classes.rule.register
class ExDayOfMonthEventRule(DayOfMonthEventRule):
    name = 'ex_day'
    desc = '[%s] %s'%(_('Exception'), _('Day of Month'))
    conflict = ('date',)
    jdMatches = lambda self, jd: not DayOfMonthEventRule.jdMatches(self, jd)

@classes.rule.register
class ExDatesEventRule(EventRule):
    name = 'ex_dates'
    desc = '[%s] %s'%(_('Exception'), _('Date'))
    #conflict = ('date',)## FIXME
    params = ('dates',)
    def __init__(self, parent):
        EventRule.__init__(self, parent)
        self.setDates([])
    def setDates(self, dates):
        self.dates = dates
        self.jdList = [to_jd(y, m, d, self.getMode()) for (y, m, d) in dates]
    def calcOccurrence(self, startEpoch, endEpoch, event):## improve performance ## FIXME
        return JdListOccurrence(
            set(getJdListFromEpochRange(startEpoch, endEpoch)).difference(self.jdList)
        )
    def getData(self):
        datesConf = []
        for date in self.dates:
            datesConf.append(dateEncode(date))
        return datesConf
    def setData(self, datesConf):
        dates = []
        if isinstance(datesConf, basestring):
            for date in datesConf.split(','):
                dates.append(dateDecode(date.strip()))
        else:
            for date in datesConf:
                if isinstance(date, basestring):
                    date = dateDecode(date)
                elif isinstance(date, (tuple, list)):
                    checkDate(date)
                dates.append(date)
        self.setDates(dates)
    def changeMode(self, mode):
        dates = []
        for jd in self.jdList:
            dates.append(jd_to(jd, mode))
        self.dates = dates

#@classes.rule.register
#class HolidayEventRule(EventRule):## FIXME
#    name = 'holiday'
#    desc = _('Holiday')
#    conflict = ('date',)


#@classes.rule.register
#class ShowInMCalEventRule(EventRule):## FIXME
#    name = 'show_cal'
#    desc = _('Show in Calendar')

#@classes.rule.register
#class SunTimeRule(EventRule):## FIXME
## ... minutes before Sun Rise      eval('sunRise-x')
## ... minutes after Sun Rise       eval('sunRise+x')
## ... minutes before Sun Set       eval('sunSet-x')
## ... minutes after Sun Set        eval('sunSet+x')


## Should not be registered, or instantiate directly
class EventNotifier(EventBaseClass):
    name = ''
    desc = ''
    params = ()
    def __init__(self, event):
        self.event = event
    getMode = lambda self: self.event.mode
    def notify(self, finishFunc):
        pass
    def getData(self):
        return dict([(param, getattr(self, param)) for param in self.params])
    def setData(self, data):
        #if isinstance(data, dict):## FIXME
        for (key, value) in data.items():
            if key in self.params:
                setattr(self, key, value)

@classes.notifier.register
class AlarmNotifier(EventNotifier):
    name = 'alarm'
    desc = _('Alarm')
    params = ('alarmSound', 'playerCmd')
    def __init__(self, event):
        EventNotifier.__init__(self, event)
        self.alarmSound = '' ## FIXME
        self.playerCmd = 'mplayer'

@classes.notifier.register
class FloatingMsgNotifier(EventNotifier):
    name = 'floatingMsg'
    desc = _('Floating Message')
    params = ('fillWidth', 'speed', 'bgColor', 'textColor')
    def __init__(self, event):
        EventNotifier.__init__(self, event)
        ###
        self.fillWidth = False
        self.speed = 100
        self.bgColor = (255, 255, 0)
        self.textColor = (0, 0, 0)

@classes.notifier.register
class WindowMsgNotifier(EventNotifier):
    name = 'windowMsg'
    desc = _('Message Window')## FIXME
    params = ('extraMessage',)
    def __init__(self, event):
        EventNotifier.__init__(self, event)
        self.extraMessage = ''
        ## window icon ## FIXME

#@classes.notifier.register## FIXME
class CommandNotifier(EventNotifier):
    name = 'command'
    desc = _('Run a Command')
    params = ('command', 'pyEval')
    def __init__(self, event):
        EventNotifier.__init__(self, event)
        self.command = ''
        self.pyEval = False


class RuleContainer:
    requiredRules = ()
    supportedRules = None
    def __init__(self):
        self.clearRules()
        self.rulesHash = None
    def clearRules(self):
        self.rulesOd = OrderedDict()
    getRule = lambda self, key: self.rulesOd.__getitem__(key)
    setRule = lambda self, key, value: self.rulesOd.__setitem__(key, value)
    getRulesData = lambda self: [(rule.name, rule.getData()) for rule in self.rulesOd.values()]
    getRulesHash = lambda self: hash(str(sorted(self.getRulesData())))
    getRuleNames = lambda self: self.rulesOd.keys()
    addRule = lambda self, rule: self.rulesOd.__setitem__(rule.name, rule)
    def addNewRule(self, ruleType):
        rule = classes.rule.byName[ruleType](self)
        self.addRule(rule)
        return rule
    def getAddRule(self, ruleType):
        try:
            return self.getRule(ruleType)
        except KeyError:
            return self.addNewRule(ruleType)
    removeRule = lambda self, rule: self.rulesOd.__delitem__(rule.name)
    __delitem__ = lambda self, key: self.rulesOd.__delitem__(key)
    __getitem__ = lambda self, key: self.getRule(key)
    __setitem__ = lambda self, key, value: self.setRule(key, value)
    __iter__ = lambda self: self.rulesOd.itervalues()
    def setRulesData(self, rulesData):
        self.clearRules()
        for (ruleName, ruleData) in rulesData:
            rule = classes.rule.byName[ruleName](self)
            rule.setData(ruleData)
            self.addRule(rule)
    def addRequirements(self):
        for name in self.requiredRules:
            if not name in self.rulesOd:
                self.addNewRule(name)
    def checkAndAddRule(self, rule):
        (ok, msg) = self.checkRulesDependencies(newRule=rule)
        if ok:
            self.addRule(rule)
        return (ok, msg)
    def removeSomeRuleTypes(self, *rmTypes):
        for ruleType in rmTypes:
            try:
                del self.rulesOd[ruleType]
            except KeyError:
                pass
    def checkAndRemoveRule(self, rule):
        (ok, msg) = self.checkRulesDependencies(disabledRule=rule)
        if ok:
            self.removeRule(rule)
        return (ok, msg)
    def checkRulesDependencies(self, newRule=None, disabledRule=None, autoCheck=True):
        rulesOd = self.rulesOd.copy()
        if newRule:
            rulesOd[newRule.name] = newRule
        if disabledRule:
            #try:
            del rulesOd[disabledRule.name]
            #except:
            #    pass
        provideList = []
        for ruleName, rule in rulesOd.items():
            provideList.append(ruleName)
            provideList += rule.provide
        for rule in rulesOd.values():
            for conflictName in rule.conflict:
                if conflictName in provideList:
                    return (False, '%s "%s" %s "%s"'%(
                        _('Conflict between'),
                        _(rule.desc),
                        _('and'),
                        _(rulesOd[conflictName].desc),
                    ))
            for needName in rule.need:
                if not needName in provideList:
                    ## find which rule(s) provide(s) needName ## FIXME
                    return (False, '"%s" %s "%s"'%(
                        _(rule.desc),
                        _('needs'),
                        _(needName), #_(rulesOd[needName].desc)
                    ))
        return (True, '')
    def copyRulesFrom(self, other):
        if self.supportedRules is None:
            self.rulesOd = other.rulesOd.copy()
        else:
            for ruleName, rule in other.rulesOd.items():
                if ruleName in self.supportedRules:
                    try:
                        self.rulesOd[ruleName].copyFrom(rule)
                    except KeyError:
                        self.addRule(rule)


## Should not be registered, or instantiate directly
class Event(JsonEventBaseClass, RuleContainer):
    name = 'custom'## or 'event' or '' FIXME
    desc = _('Custom Event')
    iconName = ''
    #requiredNotifiers = ()## needed? FIXME
    @classmethod
    def getDefaultIcon(cls):
        return join(pixDir, 'event', cls.iconName+'.png') if cls.iconName else ''
    __nonzero__ = lambda self: bool(self.rulesOd) ## FIXME
    def __init__(self, eid=None, parent=None):
        self.setId(eid)
        self.parent = parent
        try:
            self.mode = parent.mode
        except:
            self.mode = core.primaryMode
        self.icon = self.__class__.getDefaultIcon()
        self.summary = self.desc + ' (' + _(self.id) + ')'
        self.description = ''
        #self.showInTimeLine = False ## FIXME
        self.files = []
        ######
        RuleContainer.__init__(self)
        self.notifiers = []
        self.notifyBefore = (0, 1) ## (value, unit) like DurationEventRule
        ## self.snoozeTime = (5, 60) ## (value, unit) like DurationEventRule ## FIXME
        self.addRequirements()
        self.setDefaults()
        if parent is not None:
            self.setDefaultsFromGroup(parent)
        ######
        self.modified = time()
        self.remoteIds = None## (accountId, groupId, eventId)
        ## remote groupId and eventId both can be integer or string or unicode (depending on remote account type)
    def getShownDescription(self):
        if not self.description:
            return ''
        try:
            showFull = self.parent.showFullEventDesc
        except:
            showFull = False
        if showFull:
            return self.description
        else:
            return self.description.split('\n')[0]
    def afterModify(self):
        self.modified = time()
        #self.parent.eventsModified = self.modified
        ###
        if self.parent:
            rulesHash = self.getRulesHash()
            if rulesHash != self.rulesHash:
                self.parent.updateOccurrenceNodeEvent(self)
                self.rulesHash = rulesHash
        else:## None or enbale=False
            self.rulesHash = ''
    getNotifyBeforeSec = lambda self: self.notifyBefore[0] * self.notifyBefore[1]
    getNotifyBeforeMin = lambda self: int(self.getNotifyBeforeSec()/60)
    def setDefaults(self):
        '''
            sets default values that depends on event type
            not common parameters, like those are set in __init__
            DON'T call this method from parent event class
        '''
        pass
    def setDefaultsFromGroup(self, group):
        '''
            Call this method from parent event class
        '''
        if group.icon:## and not self.icon FIXME
            self.icon = group.icon
    def getInfo(self):
        lines = []
        rulesDict = self.rulesOd.copy()
        for rule in rulesDict.values():
            lines.append(rule.getInfo())
        return '\n'.join(lines)
    #def addRequirements(self):
    #    RuleContainer.addRequirements(self)
    #    notifierNames = (notifier.name for notifier in self.notifiers)
    #    for name in self.requiredNotifiers:
    #        if not name in notifierNames:
    #            self.notifiers.append(classes.notifier.byName[name](self))
    #def load(self):
    #    JsonEventBaseClass.load(self)
    #    self.addRequirements()
    def loadFiles(self):
        self.files = []
        if isdir(self.filesDir):
            for fname in listdir(self.filesDir):
                if isfile(join(self.filesDir, fname)) and not fname.endswith('~'):## FIXME
                    self.files.append(fname)
    getUrlForFile = lambda self, fname: 'file:' + os.sep*2 + self.filesDir + os.sep + fname
    def getFilesUrls(self):
        data = []
        baseUrl = self.getUrlForFile('')
        for fname in self.files:
            data.append((
                baseUrl + fname,
                _('File') + ': ' + fname,
            ))
        return data
    #getText = lambda self: self.summary if self.summary else self.description
    def getText(self):## FIXME
        try:
            sep = self.parent.eventTextSep
        except:
            sep = core.eventTextSep
        if self.summary:
            if self.description:
                return '%s%s%s'%(self.summary, sep, self.description)
            else:
                return self.summary
        else:
            return self.description
    def setId(self, eid=None):
        if eid is None or eid<0:
            eid = core.lastEventId + 1 ## FIXME
            core.lastEventId = eid
        elif eid > core.lastEventId:
            core.lastEventId = eid
        self.id = eid
        self.dir = join(eventsDir, str(self.id))
        self.file = join(self.dir, 'event.json')
        self.occurrenceFile = join(self.dir, 'occurrence')## file or directory? ## FIXME
        self.filesDir = join(self.dir, 'files')
        self.loadFiles()
    def save(self):
        makeDir(self.dir)
        JsonEventBaseClass.save(self)
    getJd = lambda self: None
    setJd = lambda self, jd: None
    def copyFrom(self, other):## FIXME
        for attr in ('mode', 'icon', 'summary', 'description'):# 'showInTimeLine'
            setattr(
                self,
                attr,
                getattr(other, attr),
            )
        self.notifyBefore = other.notifyBefore[:]
        #self.files = other.files[:]
        self.notifiers = other.notifiers[:]## FIXME
        self.copyRulesFrom(other)
        self.addRequirements()
        ####
        ## copy dates between different rule types in different event types
        jd = other.getJd()
        if jd is not None:
            self.setJd(jd)
    def getData(self):
        data = {
            'type': self.name,
            'calType': moduleNames[self.mode],
            'rules': self.getRulesData(),
            'notifiers': self.getNotifiersData(),
            'notifyBefore': durationEncode(*self.notifyBefore),
        }
        for attr in ('icon', 'summary', 'description', 'remoteIds', 'modified'):
            data[attr] = getattr(self, attr)
        return data
    def setData(self, data):
        if 'id' in data:
            self.setId(data['id'])
        if 'calType' in data:
            calType = data['calType']
            try:
                self.mode = moduleNames.index(calType)
            except ValueError:
                raise ValueError('Invalid calType: %r'%calType)
        self.clearRules()
        if 'rules' in data:
            self.setRulesData(data['rules'])
        self.notifiers = []
        if 'notifiers' in data:
            for (notifierName, notifierData) in data['notifiers']:
                notifier = classes.notifier.byName[notifierName](self)
                notifier.setData(notifierData)
                self.notifiers.append(notifier)
        if 'notifyBefore' in data:
            self.notifyBefore = durationDecode(data['notifyBefore'])
        for attr in ('icon', 'summary', 'description', 'remoteIds', 'modified'):
            try:
                setattr(self, attr, data[attr])
            except KeyError:
                pass
    #def load(self):## skipRules arg for use in ui_gtk/event/notify.py ## FIXME
    getNotifiersData = lambda self: [(notifier.name, notifier.getData()) for notifier in self.notifiers]
    getNotifiersDict = lambda self: dict(self.getNotifiersData())
    def calcOccurrenceForJdRange(self, startJd, endJd):## float jd ## cache Occurrences ## FIXME
        rules = self.rulesOd.values()
        if not rules:
            return JdListOccurrence()
        startEpoch = getEpochFromJd(startJd)
        endEpoch = getEpochFromJd(endJd)
        occur = rules[0].calcOccurrence(startEpoch, endEpoch, self)
        for rule in rules[1:]:
            try:
                startEpoch = occur.getStartEpoch()
            except ValueError:
                pass
            try:
                endEpoch = occur.getEndEpoch()
            except ValueError:
                pass
            occur = occur.intersection(rule.calcOccurrence(startEpoch, endEpoch, self))
        occur.event = self
        return occur ## FIXME
    calcOccurrenceAll = lambda self: self.calcOccurrenceForJdRange(self.parent.startJd, self.parent.endJd)
    #def calcFirstOccurrenceAfterJd(self, startJd):## too much tricky! FIXME
    def notify(self, finishFunc):
        self.n = len(self.notifiers)
        def notifierFinishFunc():
            self.n -= 1
            if self.n<=0:
                try:
                    finishFunc()
                except:
                    pass
        for notifier in self.notifiers:
            notifier.notify(notifierFinishFunc)
    def setJd(self, jd):
        pass
    def getIcsData(self, prettyDateTime=False):## FIXME
        return None
    def setIcsDict(self, data):
        return False
    def changeMode(self, mode):
        ## don't forget to call event.load() if this function failed (returned False)
        if mode != self.mode:
            for rule in self.rulesOd.values():
                if not rule.changeMode(mode):
                    return False
            self.mode = mode
        return True


@classes.event.register
class TaskEvent(Event):
    ## Y/m/d H:M none              ==> start, None
    ## Y/m/d H:M for H:M           ==> start, end
    ## Y/m/d H:M until Y/m/d H:M   ==> start, end
    name = 'task'
    desc = _('Task')
    iconName = 'task'
    requiredRules = ('start',)
    supportedRules = ('start', 'end', 'duration')
    def setDefaults(self):
        self.setStart(
            core.getSysDate(self.mode),
            tuple(localtime()[3:6]),
        )
        self.setEnd('duration', 1, 3600)
    def setDefaultsFromGroup(self, group):
        Event.setDefaultsFromGroup(self, group)
        if group.name == 'taskList':
            value, unit = group.defaultDuration
            if value > 0:
                self.setEnd('duration', value, unit)
    def setStart(self, date, dayTime):
        startRule = self['start']
        startRule.date = date
        startRule.time = dayTime
    def setEnd(self, endType, *values):
        self.removeSomeRuleTypes('end', 'duration')
        if endType=='date':
            rule = EndEventRule(self)
            (rule.date, rule.time) = values
        elif endType=='duration':
            rule = DurationEventRule(self)
            (rule.value, rule.unit) = values
        else:
            raise ValueError('invalid endType=%r'%endType)
        self.addRule(rule)
    def getStart(self):
        startRule = self['start']
        return (startRule.date, startRule.time)
    getStartEpoch = lambda self: self['start'].getEpoch()
    def getEnd(self):
        try:
            rule = self['end']
        except KeyError:
            pass
        else:
            return ('date', (rule.date, rule.time))
        try:
            rule = self['duration']
        except KeyError:
            pass
        else:
            return ('duration', (rule.value, rule.unit))
        raise ValueError('no end date neither duration specified for task')
    def getEndEpoch(self):
        try:
            rule = self['end']
        except KeyError:
            pass
        else:
            return rule.getEpoch()
        try:
            rule = self['duration']
        except KeyError:
            pass
        else:
            return self['start'].getEpoch() + rule.getSeconds()
        raise ValueError('no end date neither duration specified for task')
    getJd = lambda self: self['start'].getJd()
    setJd = lambda self, jd: self['start'].setJd(jd)
    def copyFrom(self, other):
        Event.copyFrom(self, other)
        myStartRule = self['start']
        ##
        try:
            myStartRule.time = other['dayTime'].dayTime
        except KeyError:
            pass
    def calcOccurrenceForJdRange(self, startJd, endJd):
        startEpoch = max(getEpochFromJd(startJd), self.getStartEpoch())
        endEpoch = getEpochFromJd(endJd)
        myEndEpoch = self.getEndEpoch()
        if myEndEpoch is None:
            if endEpoch >= startEpoch:
                return TimeRangeListOccurrence(
                    [
                        (startEpoch, None),
                    ]
                )
            else:
                return TimeRangeListOccurrence()
        else:
            endEpoch = min(endEpoch, myEndEpoch)
            if endEpoch >= startEpoch:
                return TimeRangeListOccurrence(
                    [
                        (startEpoch, endEpoch),
                    ]
                )
            else:
                return TimeRangeListOccurrence()
    setJd = lambda self, jd: self['start'].setJd(jd)
    def getIcsData(self, prettyDateTime=False):
        return [
            ('DTSTART', getIcsTimeByEpoch(self.getStartEpoch(), prettyDateTime)),
            ('DTEND', getIcsTimeByEpoch(self.getEndEpoch(), prettyDateTime)),
            ('TRANSP', 'OPAQUE'),
            ('CATEGORIES', self.name),## FIXME
        ]

@classes.event.register
class DailyNoteEvent(Event):
    name = 'dailyNote'
    desc = _('Daily Note')
    iconName = 'note'
    requiredRules = ('date',)
    supportedRules = ('date',)
    getDate = lambda self: self['date'].date
    def setDate(self, year, month, day):
        self['date'].date = (year, month, day)
    getJd = lambda self: self['date'].getJd()
    setJd = lambda self, jd: self['date'].setJd(jd)
    def setDefaults(self):
        self.setDate(*core.getSysDate(self.mode))
    def calcOccurrenceForJdRange(self, startJd, endJd):## float jd
        jd = self.getJd()
        return JdListOccurrence([jd] if startJd <= jd < endJd else [])
    def getIcsData(self, prettyDateTime=False):
        jd = self.getJd()
        return [
            ('DTSTART', getIcsDateByJd(jd, prettyDateTime)),
            ('DTEND', getIcsDateByJd(jd+1, prettyDateTime)),
            ('TRANSP', 'TRANSPARENT'),
            ('CATEGORIES', self.name),## FIXME
        ]
    def setIcsDict(self, data):
        self.setJd(getJdByIcsDate(data['DTSTART']))
        return True

@classes.event.register
class YearlyEvent(Event):
    name = 'yearly'
    desc = _('Yearly Event')
    iconName = 'birthday'
    requiredRules = ('month', 'day')
    supportedRules = ('month', 'day', 'start')
    getMonth = lambda self: self['month'].values[0]
    setMonth = lambda self, month: self.getAddRule('month').setData(month)
    getDay = lambda self: self['day'].values[0]
    setDay = lambda self, day: self.getAddRule('day').setData(day)
    def setDefaults(self):
        (y, m, d) = core.getSysDate(self.mode)
        self.setMonth(m)
        self.setDay(d)
    def getJd(self):## used only for copyFrom
        y, m, d = core.getSysDate(self.mode)
        m = self.getMonth()
        d = self.getDay()
        return to_jd(y, m, d, self.mode)
    def setJd(self, jd):## used only for copyFrom
        y, m, d = jd_to(jd, self.mode)
        self.setMonth(m)
        self.setDay(d)
    def calcOccurrenceForJdRange(self, startJd, endJd):## float jd
        mode = self.mode
        month = self.getMonth()
        day = self.getDay()
        try:
            startRule = self['start']
        except:
            pass
        else:
            startJd = max(startJd, startRule.getJd())
        startYear = jd_to(ifloor(startJd), mode)[0]
        endYear = jd_to(iceil(endJd), mode)[0]
        jdList = []
        for year in range(startYear, endYear+1):
            jd = to_jd(year, month, day, mode)
            if startJd <= jd < endJd:
                jdList.append(jd)
        return JdListOccurrence(jdList)
    def setJd(self, jd):
        (y, m, d) = jd_to(jd, self.mode)
        self.setMonth(m)
        self.setDay(d)
    def getData(self):
        data = Event.getData(self)
        try:
            data['startYear'] = int(self['start'].date[0])
        except KeyError:
            pass
        data['month'] = self.getMonth()
        data['day'] = self.getDay()
        del data['rules']
        return data
    def setData(self, data):
        Event.setData(self, data)
        try:
            startYear = int(data['startYear'])
        except KeyError:
            pass
        except Exception, e:
            print str(e)
        else:
            self.getAddRule('start').date = (startYear, 1, 1)
        try:
            month = data['month']
        except KeyError:
            pass
        else:
            self.setMonth(month)
        try:
            day = data['day']
        except KeyError:
            pass
        else:
            self.setDay(day)
    def getText(self):
        text = Event.getText(self)
        newParts = [
            _(self.getDay()),
            getMonthName(self.mode, self.getMonth()),
        ]
        try:
            startRule = self['start']
        except KeyError:
            pass
        else:
            newParts.append(_(startRule.date[0]))
        return ' '.join(newParts) + ': ' + text
    def getIcsData(self, prettyDateTime=False):
        if self.mode != DATE_GREG:
            return None
        month = self.getMonth()
        day = self.getDay()
        startYear = icsMinStartYear
        try:
            startRule = self['start']
        except:
            try:
                startYear = jd_to(self.parent.startJd, DATE_GREG)[0]
            except AttributeError:
                pass
        else:
            startYear = startRule.getDate(DATE_GREG)[0]
        jd = to_jd(
            startYear,
            month,
            day,
            DATE_GREG,
        )
        return [
            ('DTSTART', getIcsDateByJd(jd, prettyDateTime)),
            ('DTEND', getIcsDateByJd(jd+1, prettyDateTime)),
            ('RRULE', 'FREQ=YEARLY;BYMONTH=%d;BYMONTHDAY=%d'%(month, day)),
            ('TRANSP', 'TRANSPARENT'),
            ('CATEGORIES', self.name),## FIXME
        ]
    def setIcsDict(self, data):
        rrule = dict(splitIcsValue(data['RRULE']))
        try:
            month = int(rrule['BYMONTH'])## multiple values are not supported
        except:
            return False
        try:
            day = int(rrule['BYMONTHDAY'])## multiple values are not supported
        except:
            return False
        self.setMonth(month)
        self.setDay(day)
        self.mode = DATE_GREG
        return True

#@classes.event.register
#class UniversityCourseOwner(Event):## FIXME

@classes.event.register
class UniversityClassEvent(Event):
    name = 'universityClass'
    desc = _('Class')
    iconName = 'university'
    requiredRules  = ('weekNumMode', 'weekDay', 'dayTimeRange',)
    supportedRules = ('weekNumMode', 'weekDay', 'dayTimeRange',)
    def __init__(self, *args, **kw):
        ## assert group is not None ## FIXME
        Event.__init__(self, *args, **kw)
        self.courseId = None ## FIXME
    #def setDefaults(self):
    #    pass
    def setDefaultsFromGroup(self, group):
        Event.setDefaultsFromGroup(self, group)
        if group.name=='universityTerm':
            try:
                (tm0, tm1) = group.classTimeBounds[:2]
            except:
                myRaise()
            else:
                self['dayTimeRange'].setRange(
                    tm0 + (0,),
                    tm1 + (0,),
                )
    getCourseName = lambda self: self.parent.getCourseNameById(self.courseId)
    getWeekDayName = lambda self: core.weekDayName[self['weekDay'].weekDayList[0]]
    def updateSummary(self):
        self.summary = _('%s Class')%self.getCourseName() + ' (' + self.getWeekDayName() + ')'
    def copyFrom(self, other):
        Event.copyFrom(self, other)
        self.courseId = other.courseId
    def getData(self):
        data = Event.getData(self)
        data['courseId'] = self.courseId
        return data
    def setData(self, data):
        Event.setData(self, data)
        try:
            self.courseId = data['courseId']
        except KeyError:
            pass
    def setJd(self, jd):
        self['weekDay'].weekDayList = [core.jwday(jd)]
        ## set weekNumMode from absWeekNumber FIXME
    def getIcsData(self, prettyDateTime=False):
        startJd = self['start'].getJd()
        endJd = self['end'].getJd()
        occur = event.calcOccurrenceForJdRange(startJd, endJd)
        tRangeList = occur.getTimeRangeList()
        if not tRangeList:
            return
        return [
            ('DTSTART', getIcsTimeByEpoch(
                tRangeList[0][0],
                prettyDateTime,
            )),
            ('DTEND', getIcsTimeByEpoch(
                tRangeList[0][1],
                prettyDateTime,
            )),
            ('RRULE', 'FREQ=WEEKLY;UNTIL=%s;INTERVAL=%s;BYDAY=%s'%(
                getIcsDateByJd(endJd, prettyDateTime),
                1 if event['weekNumMode'].getData()=='any' else 2,
                encodeIcsWeekDayList(event['weekDay'].weekDayList),
            )),
            ('TRANSP', 'OPAQUE'),
            ('CATEGORIES', self.name),## FIXME
        ]

@classes.event.register
class UniversityExamEvent(DailyNoteEvent):
    name = 'universityExam'
    desc = _('Exam')
    iconName = 'university'
    requiredRules  = ('date', 'dayTimeRange',)
    supportedRules = ('date', 'dayTimeRange',)
    def __init__(self, *args, **kw):
        ## assert group is not None ## FIXME
        DailyNoteEvent.__init__(self, *args, **kw)
        self.courseId = None ## FIXME
    def setDefaults(self):
        self['dayTimeRange'].setRange((9, 0), (11, 0))## FIXME
    def setDefaultsFromGroup(self, group):
        DailyNoteEvent.setDefaultsFromGroup(self, group)
        if group.name=='universityTerm':
            self.setDate(*group['end'].date)## FIXME
    getCourseName = lambda self: self.parent.getCourseNameById(self.courseId)
    def updateSummary(self):
        self.summary = _('%s Exam')%self.getCourseName()
    def copyFrom(self, other):
        Event.copyFrom(self, other)
        self.courseId = other.courseId
    def getData(self):
        data = Event.getData(self)
        data['courseId'] = self.courseId
        return data
    def setData(self, data):
        Event.setData(self, data)
        try:
            self.courseId = data['courseId']
        except KeyError:
            pass
    def calcOccurrenceForJdRange(self, startJd, endJd):
        return DailyNoteEvent.calcOccurrenceForJdRange(self, startJd, endJd).intersection(
            self['dayTimeRange'].calcOccurrence(
                getEpochFromJd(startJd),
                getEpochFromJd(endJd),
                self,
            )
        )
    def getIcsData(self, prettyDateTime=False):
        dayStart = self['date'].getEpoch()
        (startSec, endSec) = self['dayTimeRange'].getSecondsRange()
        return [
            ('DTSTART', getIcsTimeByEpoch(
                dayStart + startSec,
                prettyDateTime,
            )),
            ('DTEND', getIcsTimeByEpoch(
                dayStart + endSec,
                prettyDateTime
            )),
            ('TRANSP', 'OPAQUE'),
        ]

@classes.event.register
class LargeScaleEvent(Event):
    name = 'largeScale'
    desc = _('Large Scale Event')
    __nonzero__ = lambda self: True
    def __init__(self, *args, **kw):
        self.scale = 1 ## 1, 1000, 1000**2, 1000**3
        self.start = 0
        self.duration = 1
        Event.__init__(self, *args, **kw)
    def setDefaultsFromGroup(self, group):
        Event.setDefaultsFromGroup(self, group)
        if group.name == 'largeScale':
            self.scale = group.scale
            self.start = group.getStartValue()
    def copyFrom(self, other):
        Event.copyFrom(self, other)
        if other.name == self.name:
            self.scale = other.scale
            self.start = other.start
            self.duration = other.duration
    def getData(self):
        data = Event.getData(self)
        for attr in ('scale', 'start', 'duration'):
            data[attr] = getattr(self, attr)
        return data
    def setData(self, data):
        Event.setData(self, data)
        for attr in ('scale', 'start', 'duration'):
            try:
                setattr(self, attr, data[attr])
            except KeyError:
                pass
    def calcOccurrenceForJdRange(self, startJd, endJd):
        myStartJd = iceil(to_jd(self.scale*self.start, 1, 1, self.mode))
        myEndJd = ifloor(to_jd(self.scale*(self.start+self.duration), 1, 1, self.mode))
        ## myEndJd = ifloor(startJd + self.scale*self.duration*avgYearLength)
        return TimeRangeListOccurrence(
            intersectionOfTwoTimeRangeList(
                [
                    (getEpochFromJd(startJd), getEpochFromJd(endJd))
                ],
                [
                    (getEpochFromJd(myStartJd), getEpochFromJd(myEndJd))
                ],
            )
        )
    #def getIcsData(self, prettyDateTime=False):
    #    pass


@classes.event.register
class CustomEvent(Event):
    name = 'custom'
    desc = _('Custom Event')

class EventContainer(JsonEventBaseClass):
    name = ''
    desc = ''
    def __getitem__(self, key):
        if isinstance(key, int):## eventId
            return self.getEvent(key)
        else:
            raise TypeError('invalid key type %r give to EventContainer.__getitem__'%key)
    def __init__(self):
        self.mode = core.primaryMode
        self.idList = []
        self.title = 'Untitled'
        self.icon = ''
        self.showFullEventDesc = False
        ######
        self.modified = time()
        #self.eventsModified = self.modified
    def afterModify(self):
        self.modified = time()
    def getEvent(self, eid):
        assert eid in self.idList
        eventFile = join(eventsDir, str(eid), 'event.json')
        if not isfile(eventFile):
            raise IOError('error while loading event file %r: no such file (container title: %s)'%(eventFile, self.title))
        data = jsonToData(open(eventFile).read())
        data['id'] = eid ## FIXME
        event = classes.event.byName[data['type']](eid)
        event.setData(data)
        return event
    def getEventsGen(self):
        for eid in self.idList:
            yield self.getEvent(eid)
    __iter__ = lambda self: IteratorFromGen(self.getEventsGen())
    __len__ = lambda self: len(self.idList)
    insert = lambda self, index, event: self.idList.insert(index, event.id)
    append = lambda self, event: self.idList.append(event.id)
    index = lambda self, eid: self.idList.index(eid)
    moveUp = lambda self, index: self.idList.insert(index-1, self.idList.pop(index))
    moveDown = lambda self, index: self.idList.insert(index+1, self.idList.pop(index))
    def remove(self, event):## call when moving to trash
        '''
            excludes event from this container (group or trash), not delete event data completely
            and returns the index of (previously contained) event
        '''
        index = self.idList.index(event.id)
        self.idList.remove(event.id)
        return index
    def copyFrom(self, other):
        for attr in (
            'mode', 'title', 'icon', 'showFullEventDesc', 'idList',
        ):
            setattr(
                self,
                attr,
                getattr(other, attr),
            )
    def getData(self):
        data = {
            'calType': moduleNames[self.mode],
        }
        for attr in ('title', 'icon', 'showFullEventDesc', 'idList'):
            data[attr] = getattr(self, attr)
        return data
    def setData(self, data):
        if 'calType' in data:
            calType = data['calType']
            try:
                self.mode = moduleNames.index(calType)
            except ValueError:
                raise ValueError('Invalid calType: %r'%calType)
        ####
        for attr in ('title', 'icon', 'showFullEventDesc', 'idList'):
            try:
                setattr(self, attr, data[attr])
            except KeyError:
                pass


@classes.group.register
class EventGroup(EventContainer):
    name = 'group'
    desc = _('Event Group')
    acceptsEventTypes = ('yearly', 'dailyNote', 'task', 'largeScale', 'custom')
    canConvertTo = ()
    actions = []## [('Export to ICS', 'exportToIcs')]
    eventActions = [] ## FIXME
    sortBys = (
        ('mode', _('Calendar Type')),
        ('summary', _('Summary')),
        ('description', _('Description')),
        ('icon', _('Icon')),
    )
    sortByDefault = 'summary'
    getSortByValue = lambda self, event, attr: getattr(event, attr, None)
    def sort(self, attr='summary', reverse=False):
        event_cmp = lambda event1, event2: cmp(
            (event1.name, self.getSortByValue(event1, attr)),
            (event2.name, self.getSortByValue(event2, attr)),
        )
        eid_cmp = lambda eid1, eid2: event_cmp(
            self.getEvent(eid1),
            self.getEvent(eid2),
        )
        self.idList = sorted(self.idList, cmp=eid_cmp, reverse=reverse)
    def __getitem__(self, key):
        #if isinstance(key, basestring):## ruleName
        #    return self.getRule(key)
        if isinstance(key, int):## eventId
            return self.getEvent(key)
        else:
            raise TypeError('invalid key type %r give to EventGroup.__getitem__'%key)
    def __setitem__(self, key, value):
        #if isinstance(key, basestring):## ruleName
        #    return self.setRule(key, value)
        if isinstance(key, int):## eventId
            raise TypeError('can not assign event to group')## FIXME
        else:
            raise TypeError('invalid key type %r give to EventGroup.__setitem__'%key)
    def __delitem__(self, key):
        if isinstance(key, int):## eventId
            self.remove(self.getEvent(key))
        else:
            raise TypeError('invalid key type %r give to EventGroup.__delitem__'%key)
    def checkEventToAdd(self, event):
        return event.name in self.acceptsEventTypes
    def __init__(self, gid=None, title=None):
        EventContainer.__init__(self)
        self.setId(gid)
        self.enable = True
        if title is None:
            title = self.desc
        self.title = title
        self.color = hslToRgb(random.uniform(0, 360), 1, 0.5)## FIXME
        #self.defaultNotifyBefore = (10, 60) ## FIXME
        if len(self.acceptsEventTypes)==1:
            self.defaultEventType = self.acceptsEventTypes[0]
            icon = classes.event.byName[self.acceptsEventTypes[0]].getDefaultIcon()
            if icon:
                self.icon = icon
        else:
            self.defaultEventType = 'custom'
        self.eventCacheSize = 0
        self.eventTextSep = core.eventTextSep
        #self.nodeLoaded = False
        ###
        self.eventCache = {} ## from eid to event object
        ###
        (year, month, day) = core.getSysDate(self.mode)
        self.startJd = to_jd(year-10, 1, 1, self.mode)
        self.endJd = to_jd(year+5, 1, 1, self.mode)
        ###
        self.node = CenterNode(offset=self.startJd)## offset=?? (J2000 by default)
        ###
        self.setDefaults()
        ###########
        self.remoteIds = None## (accountId, groupId)
        ## remote groupId can be an integer or string or unicode (depending on remote account type)
        self.remoteSyncData = {}
        self.eventIdByRemoteIds = {}
    #def load(self):
    #    EventContainer.load(self)
    #    self.addRequirements()
    def afterSync(self):
        self.remoteSyncData[self.remoteIds] = time()
    def getLastSync(self):
        if self.remoteIds:
            try:
                return self.remoteSyncData[self.remoteIds]
            except KeyError:
                pass
    def setDefaults(self):
        '''
            sets default values that depends on group type
            not common parameters, like those are set in __init__
        '''
    __nonzero__ = lambda self: self.enable ## FIXME
    def setId(self, gid=None):
        if gid is None or gid<0:
            gid = core.lastEventGroupId + 1 ## FIXME
            core.lastEventGroupId = gid
        elif gid > core.lastEventGroupId:
            core.lastEventGroupId = gid
        self.id = gid
        self.file = join(groupsDir, '%d.json'%self.id)
    def copyFrom(self, other):
        EventContainer.copyFrom(self, other)
        for attr in (
            'enable', 'color', 'eventCacheSize', 'eventTextSep',
            'remoteIds', 'remoteSyncData', 'eventIdByRemoteIds',
            'startJd', 'endJd',
        ):#'defaultEventType'
            setattr(
                self,
                attr,
                getattr(other, attr),
            )
    def getBasicData(self):
        data = EventContainer.getData(self)
        data['type'] = self.name
        for attr in (
            'enable', 'color', 'eventCacheSize', 'eventTextSep', 'startJd', 'endJd',
            ## 'defaultEventType'
        ):
            data[attr] = getattr(self, attr)
        return data
    def getData(self):
        data = self.getBasicData()
        data['remoteIds'] = self.remoteIds
        data['remoteSyncData'] = sorted(self.remoteSyncData.items())
        data['eventIdByRemoteIds'] = sorted(self.eventIdByRemoteIds.items())
        return data
    def setBasicData(self, data):
        EventContainer.setData(self, data)
        if 'id' in data:
            self.setId(data['id'])
        for attr in (
            'enable', 'color', 'eventCacheSize', 'eventTextSep', 'startJd', 'endJd',
            ## 'defaultEventType'
        ):
            try:
                setattr(self, attr, data[attr])
            except KeyError:
                pass
        self.startJd = int(self.startJd)
        self.endJd = int(self.endJd)
        ####
        #if 'defaultEventType' in data:
        #    self.defaultEventType = data['defaultEventType']
        #    if not self.defaultEventType in classes.event.names:
        #        raise ValueError('Invalid defaultEventType: %r'%self.defaultEventType)
    def setData(self, data):
        self.setBasicData(data)
        if 'remoteIds' in data:
            self.remoteIds = data['remoteIds']
        if 'remoteSyncData' in data:
            self.remoteSyncData = {}
            for remoteIds, syncData in data['remoteSyncData']:
                if remoteIds is None:
                    continue
                if isinstance(syncData, (list, tuple)):
                    syncData = syncData[1]
                self.remoteSyncData[tuple(remoteIds)] = syncData
        if 'eventIdByRemoteIds' in data:
            self.eventIdByRemoteIds = {}
            for remoteIds, eventId in data['eventIdByRemoteIds']:
                self.eventIdByRemoteIds[tuple(remoteIds)] = eventId
            #print self.eventIdByRemoteIds
    ################# Event objects should be accessed from outside only within one of these 3 methods
    def getEvent(self, eid):
        if not eid in self.idList:
            print 'EventGroup.getEvent(%s): not in %s'%(eid, self.idList)
        assert eid in self.idList
        if eid in self.eventCache:
            return self.eventCache[eid]
        event = EventContainer.getEvent(self, eid)
        event.parent = self
        event.rulesHash = event.getRulesHash()
        if len(self.eventCache) < self.eventCacheSize:
            self.eventCache[eid] = event
        return event
    def createEvent(self, eventType):
        assert eventType in self.acceptsEventTypes
        event = classes.event.byName[eventType](parent=self)
        return event
    def copyEventWithType(self, event, eventType):## FIXME
        newEvent = self.createEvent(eventType)
        newEvent.setId(event.id)
        newEvent.changeMode(event.mode)
        newEvent.copyFrom(event)
        return newEvent
    ###############################################
    def remove(self, event):## call when moving to trash
        event.parent = None
        index = EventContainer.remove(self, event)
        try:
            del self.eventCache[event.id]
        except:
            pass
        try:
            del self.eventIdByRemoteIds[event.remoteIds]
        except:
            pass
        self.node.delEvent(event.id)
        return index
    def removeAll(self):## clearEvents or excludeAll or removeAll FIXME
        for event in self.eventCache.values():
            event.parent = None ## needed? FIXME
        ###
        self.idList = []
        self.eventCache = {}
        self.node.clear()
    def _postAdd(self, event):
        event.parent = self ## needed? FIXME
        if len(self.eventCache) < self.eventCacheSize:
            self.eventCache[event.id] = event
        if event.remoteIds:
            self.eventIdByRemoteIds[event.remoteIds] = event.id
        ## need to update self.node?
        ## its done in event.afterModify() right? not when moving event from another group
        if self.enable:
            self.updateOccurrenceNodeEvent(event)
    def insert(self, index, event):
        self.idList.insert(index, event.id)
        self._postAdd(event)
    def append(self, event):
        self.idList.append(event.id)
        self._postAdd(event)
    def updateCache(self, event):
        if event.id in self.eventCache:
            self.eventCache[event.id] = event
        self.node.delEvent(event.id)
        event.afterModify()
    def copy(self):
        newGroup = EventBaseClass.copy(self)
        newGroup.removeAll()
        return newGroup
    def copyAs(self, newGroupType):
        newGroup = classes.group.byName[newGroupType]()
        newGroup.copyFrom(self)
        newGroup.removeAll()
        return newGroup
    def deepCopy(self):
        newGroup = self.copy()
        for event in self:
            newEvent = event.copy()
            newEvent.save()
            newGroup.append(newEvent)
        return newGroup
    def deepConvertTo(self, newGroupType):
        newGroup = self.copyAs(newGroupType)
        newEventType = newGroup.acceptsEventTypes[0]
        newGroup.enable = False ## to prevent per-event node update
        for event in self:
            newEvent = newGroup.createEvent(newEventType)
            newEvent.changeMode(event.mode)## FIXME needed?
            newEvent.copyFrom(event)
            newEvent.setId(event.id)
            newEvent.save()
            newGroup.append(newEvent)
        newGroup.enable = self.enable
        self.removeAll()## events with the same id's, can not be contained by two groups
        return newGroup
    def calcOccurrenceAll(self):
        occurList = []
        startJd = self.startJd
        endJd = self.endJd
        for event in self:
            occur = event.calcOccurrenceForJdRange(startJd, endJd)
            if occur:
                occurList.append((event.id, occur))
        return occurList
    def afterModify(self):## FIXME
        EventContainer.afterModify(self)
        if self.enable:
            #print 'EventGroup.afterModify: running updateOccurrenceNode'
            self.updateOccurrenceNode()## FIXME
        else:
            self.node.clear()
    def updateOccurrenceNodeEvent(self, event):
        #print 'updateOccurrenceNodeEvent', self.id, self.title, event.id
        node = self.node
        eid = event.id
        node.delEvent(eid)
        for t0, t1 in event.calcOccurrenceAll().getTimeRangeList():
            node.addEvent(t0, t1, eid)
    def updateOccurrenceNode(self):
        #stm0 = time()
        #print 'updateOccurrenceNode', self.id, self.title
        self.node.clear()
        for eid, occur in self.calcOccurrenceAll():
            for t0, t1 in occur.getTimeRangeList():
                self.node.addEvent(t0, t1, eid)
        #self.nodeLoaded = True
        #print time()-stm0
    def getIcsText(self, startJd, endJd):
        icsText = icsHeader
        currentTimeStamp = getIcsTimeByEpoch(time())
        for event in self:
            icsData = event.getIcsData()
            vevent = 'BEGIN:VEVENT\n'
            vevent += 'CREATED:%s\n'%currentTimeStamp
            vevent += 'LAST-MODIFIED:%s\n'%currentTimeStamp
            vevent += 'SUMMARY:%s\n'%event.summary
            #vevent += 'CATEGORIES:%s\n'%self.title## FIXME
            vevent += 'CATEGORIES:%s\n'%event.name## FIXME
            if icsData is None:
                occur = event.calcOccurrenceForJdRange(startJd, endJd)
                if occur:
                    if isinstance(occur, JdListOccurrence):
                        for sectionStartJd, sectionEndJd in occur.calcJdRanges():
                            vevent += 'DTSTART;VALUE=DATE:%.4d%.2d%.2d\n'%jd_to(sectionStartJd, DATE_GREG)
                            vevent += 'DTEND;VALUE=DATE:%.4d%.2d%.2d\n'%jd_to(sectionEndJd, DATE_GREG)
                            vevent += 'TRANSP:TRANSPARENT\n' ## http://www.kanzaki.com/docs/ical/transp.html
                    elif isinstance(occur, (TimeRangeListOccurrence, TimeListOccurrence)):
                        for startEpoch, endEpoch in occur.getTimeRangeList():
                            vevent += 'DTSTART:%s\n'%getIcsTimeByEpoch(startEpoch)
                            if endEpoch is not None and endEpoch-startEpoch > 1:
                                vevent += 'DTEND:%s\n'%getIcsTimeByEpoch(int(endEpoch))## why its float? FIXME
                            vevent += 'TRANSP:OPAQUE\n' ## FIXME ## http://www.kanzaki.com/docs/ical/transp.html
                    else:
                        raise RuntimeError
            else:
                for key, value in icsData:
                    vevent += '%s:%s\n'%(key, value)
            vevent += 'END:VEVENT\n'
            icsText += vevent
        icsText += 'END:VCALENDAR\n'
        return icsText
    def exportToIcs(self, fpath, startJd, endJd):
        icsText = self.getIcsText(startJd, endJd)
        open(fpath, 'w').write(icsText)
    def exportData(self, putInfo=True):
        data = self.getBasicData()
        data['events'] = []
        for eventId in self.idList:
            eventData = EventContainer.getEvent(self, eventId).getData()
            data['events'].append(eventData)
        del data['idList']
        if putInfo:
            data['info'] = {
                'appName': core.APP_NAME,
                'version': core.VERSION,
                #'exportDate':
            }
        return data
    def importData(self, data):
        self.setBasicData(data)
        for eventData in data['events']:
            event = self.createEvent(eventData['type'])
            event.setData(eventData)## or setBasicData FIXME
            event.save()
            self.append(event)
        self.save()

@classes.group.register
class TaskList(EventGroup):
    name = 'taskList'
    desc = _('Task List')
    acceptsEventTypes = ('task',)
    #actions = EventGroup.actions + []
    sortBys = EventGroup.sortBys + (
        ('start', _('Start')),
        ('end', _('End')),
    )
    sortByDefault = 'start'
    def getSortByValue(self, event, attr):
        if event.name in self.acceptsEventTypes:
            if attr=='start':
                return event.getStartEpoch()
            elif attr=='end':
                return event.getEndEpoch()
        return EventGroup.getSortByValue(self, event, attr)
    def __init__(self, gid=None, title=None):
        EventGroup.__init__(self, gid, title)
        self.defaultDuration = (0, 1) ## (value, unit)
        ## if defaultDuration[0] is set to zero, the checkbox for task's end, will be unchecked for new tasks
    def copyFrom(self, other):
        EventGroup.copyFrom(self, other)
        if other.name == self.name:
            self.defaultDuration = other.defaultDuration[:]
    def getData(self):
        data = EventGroup.getData(self)
        data['defaultDuration'] = durationEncode(*self.defaultDuration)
        return data
    def setData(self, data):
        EventGroup.setData(self, data)
        if 'defaultDuration' in data:
            self.defaultDuration = durationDecode(data['defaultDuration'])

@classes.group.register
class NoteBook(EventGroup):
    name = 'noteBook'
    desc = _('Note Book')
    acceptsEventTypes = ('dailyNote',)
    canConvertTo = ('yearly',)
    #actions = EventGroup.actions + []
    sortBys = EventGroup.sortBys + (
        ('date', _('Date')),
    )
    sortByDefault = 'date'
    def getSortByValue(self, event, attr):
        if event.name in self.acceptsEventTypes:
            if attr=='date':
                return event.getDate()
        return EventGroup.getSortByValue(self, event, attr)


@classes.group.register
class YearlyGroup(EventGroup):
    name = 'yearly'
    desc = _('Yearly Events Group')
    acceptsEventTypes = ('yearly',)
    canConvertTo = ('noteBook',)
                

@classes.group.register
class UniversityTerm(EventGroup):
    name = 'universityTerm'
    desc = _('University Term')
    acceptsEventTypes = ('universityClass', 'universityExam')
    actions = EventGroup.actions + [('View Weekly Schedule', 'viewWeeklySchedule')]
    sortBys = EventGroup.sortBys + (
        ('course', _('Course')),
        ('time', _('Time')),
    )
    sortByDefault = 'time'
    def getSortByValue(self, event, attr):
        if event.name in self.acceptsEventTypes:
            if attr=='course':
                return event.name, event.courseId
            elif attr=='time':
                if event.name == 'universityClass':
                    wd = event['weekDay'].weekDayList[0]
                    return (wd - core.firstWeekDay)%7, event['dayTimeRange'].getHourRange()
                elif event.name == 'universityExam':
                    return event['date'].getJd(), event['dayTimeRange'].getHourRange()
        return EventGroup.getSortByValue(self, event, attr)
    def __init__(self, gid=None, title=None):
        EventGroup.__init__(self, gid, title)
        self.classesEndDate = core.getSysDate(self.mode)## FIXME
        self.setCourses([]) ## list of (courseId, courseName, courseUnits)
        self.classTimeBounds = [
            (8, 0),
            (10, 0),
            (12, 0),
            (14, 0),
            (16, 0),
            (18, 0),
        ] ## FIXME
    def getClassBoundsFormatted(self):
        count = len(self.classTimeBounds)
        if count < 2:
            return
        titles = []
        tmfactors = []
        firstTm = timeToFloatHour(*self.classTimeBounds[0])
        lastTm = timeToFloatHour(*self.classTimeBounds[-1])
        deltaTm = lastTm - firstTm
        for i in range(count-1):
            (tm0, tm1) = self.classTimeBounds[i:i+2]
            titles.append(
                textNumEncode(simpleTimeEncode(tm0)) + ' ' + _('to') + ' ' + textNumEncode(simpleTimeEncode(tm1))
            )
        for tm1 in self.classTimeBounds:
            tmfactors.append((timeToFloatHour(*tm1)-firstTm)/deltaTm)
        return (titles, tmfactors)
    def getWeeklyScheduleData(self, currentWeekOnly=False):
        boundsCount = len(self.classTimeBounds)
        boundsHour = [h + m/60.0 for h,m in self.classTimeBounds]
        data = [
            [
                [] for i in range(boundsCount-1)
            ] for weekDay in range(7)
        ]
        ## data[weekDay][intervalIndex] = {'name': 'Course Name', 'weekNumMode': 'odd'}
        ###
        if currentWeekOnly:
            currentJd = core.getCurrentJd()
            if ( getAbsWeekNumberFromJd(currentJd) -  getAbsWeekNumberFromJd(self['start'].getJd()) ) % 2 == 1:
                currentWeekNumMode = 'odd'
            else:
                currentWeekNumMode = 'even'
            #print 'currentWeekNumMode = %r'%currentWeekNumMode
        else:
            currentWeekNumMode = ''
        ###
        for event in self:
            if event.name != 'universityClass':
                continue
            weekNumMode = event['weekNumMode'].getData()
            if currentWeekNumMode:
                if weekNumMode not in ('any', currentWeekNumMode):
                    continue
                weekNumMode = ''
            else:
                if weekNumMode=='any':
                    weekNumMode = ''
            ###
            weekDay = event['weekDay'].weekDayList[0]
            (h0, h1) = event['dayTimeRange'].getHourRange()
            startIndex = findNearestIndex(boundsHour, h0)
            endIndex = findNearestIndex(boundsHour, h1)
            ###
            classData = {
                'name': self.getCourseNameById(event.courseId),
                'weekNumMode': weekNumMode,
            }
            for i in range(startIndex, endIndex):
                data[weekDay][i].append(classData)

        return data
    def setCourses(self, courses):
        self.courses = courses
        self.lastCourseId = max([1]+[course[0] for course in self.courses])
    #getCourseNamesDictById = lambda self: dict([c[:2] for c in self.courses])
    def getCourseNameById(self, courseId):
        for course in self.courses:
            if course[0] == courseId:
                return course[1]
        return _('Deleted Course')
    def setDefaults(self):
        calType = core.moduleNames[self.mode]
        ## FIXME
        ## odd term or even term?
        jd = core.getCurrentJd()
        (year, month, day) = jd_to(jd, self.mode)
        md = (month, day)
        if calType=='jalali':
            ## 0/07/01 to 0/11/01
            ## 0/11/15 to 1/03/20
            if (1, 1) <= md < (4, 1):
                self.startJd = to_jd(year-1, 11, 15, self.mode)
                self.classesEndDate = (year, 3, 20)
                self.endJd = to_jd(year, 4, 10, self.mode)
            elif (4, 1) <= md < (10, 1):
                self.startJd = to_jd(year, 7, 1, self.mode)
                self.classesEndDate = (year, 11, 1)
                self.endJd = to_jd(year, 11, 1, self.mode)
            else:## md >= (10, 1)
                self.startJd = to_jd(year, 11, 15, self.mode)
                self.classesEndDate = (year+1, 3, 1)
                self.endJd = to_jd(year+1, 3, 20, self.mode)
        #elif calType=='gregorian':
        #    pass
    def getNewCourseID(self):
        self.lastCourseId += 1
        return self.lastCourseId
    def copyFrom(self, other):
        EventGroup.copyFrom(self, other)
        if other.name == self.name:
            self.classesEndDate = other.classesEndDate[:]
            self.courses = other.courses[:]
            self.classTimeBounds = other.classTimeBounds[:]
    def getData(self):
        data = EventGroup.getData(self)
        data.update({
            'classTimeBounds': [hmEncode(hm) for hm in self.classTimeBounds],
            'classesEndDate': dateEncode(self.classesEndDate),
        })
        for attr in ('courses',):
            data.update({attr: getattr(self, attr)})
        return data
    def setData(self, data):
        EventGroup.setData(self, data)
        if 'classesEndDate' in data:
            self.classesEndDate = dateDecode(data['classesEndDate'])
        if 'classTimeBounds' in data:
            self.classTimeBounds = sorted([hmDecode(hm) for hm in data['classTimeBounds']])
        for attr in ('courses',):
            try:
                setattr(self, attr, data[attr])
            except KeyError:
                pass


@classes.group.register
class LargeScaleGroup(EventGroup):
    name = 'largeScale'
    desc = _('Large Scale Events Group')
    acceptsEventTypes = ('largeScale',)
    sortBys = EventGroup.sortBys + (
        ('start', _('Start')),
    )
    sortByDefault = 'start'
    def getSortByValue(self, event, attr):
        if event.name in self.acceptsEventTypes:
            if attr=='start':
                return event.name, event.start * event.scale
        return EventGroup.getSortByValue(self, event, attr)
    def __init__(self, gid=None, title=None):
        self.scale = 1 ## 1, 1000, 1000**2, 1000**3
        EventGroup.__init__(self, gid, title)
    def setDefaults(self):
        self.startJd = 0
        self.endJd = self.startJd + self.scale * 9999
    def copyFrom(self, other):
        EventGroup.copyFrom(self, other)
        if other.name == self.name:
            self.scale = other.scale
    def getData(self):
        data = EventGroup.getData(self)
        data['scale'] = self.scale
        return data
    def setData(self, data):
        EventGroup.setData(self, data)
        try:
            self.scale = data['scale']
        except KeyError:
            pass
    getStartValue = lambda self: jd_to(self.startJd, self.mode)[0]//self.scale
    getEndValue = lambda self: jd_to(self.endJd, self.mode)[0]//self.scale
    def setStartValue(self, start):
        self.startJd = int(to_jd(start*self.scale, 1, 1, self.mode))
    def setEndValue(self, end):
        self.endJd = int(to_jd(end*self.scale, 1, 1, self.mode))

class JsonObjectsHolder(JsonEventBaseClass):
    ## keeps all objects in memory
    ## Only use to keep groups and accounts, but not events
    def __init__(self):
        self.clear()
    def clear(self):
        self.byId = {}
        self.idList = []
    def iterGen(self):
        for _id in self.idList:
            yield self.byId[_id]
    __iter__ = lambda self: IteratorFromGen(self.iterGen())
    __len__ = lambda self: len(self.idList)
    __nonzero__ = lambda self: bool(self.idList)
    index = lambda self, _id: self.idList.index(_id) ## or get object instead of obj_id? FIXME
    __getitem__ = lambda self, _id: self.byId.__getitem__(_id)
    byIndex = lambda self, index: self.byId[self.idList[index]]
    #byIndex = lambda
    __setitem__ = lambda self, _id, group: self.byId.__setitem__(_id, group)
    def insert(self, index, obj):
        assert not obj.id in self.idList
        self.byId[obj.id] = obj
        self.idList.insert(index, obj.id)
    def append(self, obj):
        assert not obj.id in self.idList
        self.byId[obj.id] = obj
        self.idList.append(obj.id)
    def delete(self, obj):
        assert obj.id in self.idList
        try:
            os.remove(obj.file)
        except:
            myRaise()
        else:
            del self.byId[obj.id]
            self.idList.remove(obj.id)
    def pop(self, index):
        return self.byId.pop(self.idList.pop(index))
    moveUp = lambda self, index: self.idList.insert(index-1, self.idList.pop(index))
    moveDown = lambda self, index: self.idList.insert(index+1, self.idList.pop(index))
    def setData(self, data):
        self.idList = data
    def getData(self):
        return self.idList


class EventGroupsHolder(JsonObjectsHolder):
    file = join(confDir, 'event', 'group_list.json')
    def delete(self, obj):
        assert not obj.idList ## FIXME
        JsonObjectsHolder.delete(self, obj)
    def appendNew(self, data):
        obj = classes.group.byName[data['type']](data['id'])
        obj.setData(data)
        self.append(obj)
        return obj
    def load(self):
        #print '------------ EventGroupsHolder.load'
        self.clear()
        #eventIdList = []
        if isfile(self.file):
            for _id in jsonToData(open(self.file).read()):
                objFile = join(groupsDir, '%s.json'%_id)
                if not isfile(objFile):
                    log.error('error while loading group file %r: no such file'%objFile)## FIXME
                    continue
                data = jsonToData(open(objFile).read())
                data['id'] = _id ## FIXME
                obj = self.appendNew(data)
                if obj.enable:
                    obj.updateOccurrenceNode()
                ## here check that non of obj.idList are in eventIdList ## FIXME
                #eventIdList += obj.idList
        else:
            for cls in classes.group:
                obj = cls()## FIXME
                obj.setData({'title': cls.desc})## FIXME
                obj.save()
                self.append(obj)
            ###
            #trash = EventTrash()## FIXME
            #obj.save()
            #self.append(trash)
            ###
            self.save()
        ## here check for non-grouped event ids ## FIXME
    def moveToTrash(self, group, trash, addToFirst=True):
        if addToFirst:
            trash.idList = group.idList + trash.idList
        else:
            trash.idList += group.idList
        group.idList = []
        self.delete(group)
        self.save()
        trash.save()
    def convertGroupTo(self, group, newGroupType):
        groupIndex = self.index(group.id)
        newGroup = group.deepConvertTo(newGroupType)
        newGroup.setId(group.id)
        newGroup.afterModify()
        newGroup.save()
        self.byId[newGroup.id] = newGroup
        return newGroup
        ## and then never use old `group` object
    def exportData(self, gidList):
        data = {
            'groups': [],
            'info': {
                'appName': core.APP_NAME,
                'version': core.VERSION,
                #'exportDate':
            },
        }
        for gid in gidList:
            data['groups'].append(self.byId[gid].exportData(False))
        return data
    def importData(self, data):
        newGroups = []
        for gdata in data['groups']:
            group = classes.group.byName[gdata['type']]()
            group.importData(gdata)
            self.append(group)
            newGroups.append(group)
        self.save()## FIXME
        return newGroups
    importJsonFile = lambda self, fpath: self.importData(jsonToData(open(fpath, 'rb').read()))
    def checkForOrphans(self):
        newGroup = EventGroup()
        newGroup.setData({
            'title': 'Orphan Events',
            'enable': False,
            'color': (255, 255, 0),
        })
        for gid_fname in listdir(groupsDir):
            try:
                gid = int(splitext(gid_fname)[0])
            except ValueError:
                continue
            if not gid in self.idList:
                try:
                    os.remove(join(groupsDir, gid_fname))
                except:
                    myRaise()
        ######
        myEventIds = []
        for group in self:
            myEventIds += group.idList
        myEventIds = set(myEventIds)
        ##
        for eid_dname in listdir(eventsDir):
            try:
                eid = int(eid_dname)
            except ValueError:
                continue
            if not eid in myEventIds:
                newGroup.idList.append(eid)
        if newGroup.idList:
            newGroup.save()
            self.append(newGroup)
            self.save()
            return newGroup
        else:
            return


class EventAccountsHolder(JsonObjectsHolder):
    file = join(confDir, 'event', 'account_list.json')
    def load(self):
        #print '------------ EventAccountsHolder.load'
        self.clear()
        if isfile(self.file):
            for _id in jsonToData(open(self.file).read()):
                objFile = join(accountsDir, '%s.json'%_id)
                if not isfile(objFile):
                    log.error('error while loading account file %r: no such file'%objFile)## FIXME
                    continue
                data = jsonToData(open(objFile).read())
                data['id'] = _id ## FIXME
                obj = classes.account.byName[data['type']](_id)
                obj.setData(data)
                self.append(obj)


class EventTrash(EventContainer):
    name = 'trash'
    desc = _('Trash')
    file = join(confDir, 'event', 'trash.json')## FIXME
    def __init__(self):
        EventContainer.__init__(self)
        self.title = _('Trash')
        self.icon = join(pixDir, 'trash.png')
        self.enable = False
    def delete(self, eid):
        ## different from EventContainer.remove
        ## remove() only removes event from this group, but event file and data still available
        ## and probably will be added to another event container
        ## but after delete(), there is no event file, and not event data
        if not isinstance(eid, int):
            raise TypeError("delete takes event ID that is integer")
        assert eid in self.idList
        try:
            shutil.rmtree(join(eventsDir, str(eid)))
        except:
            myRaise()
        else:
            self.idList.remove(eid)
    def empty(self):
        idList2 = self.idList[:]
        for eid in self.idList:
            try:
                shutil.rmtree(join(eventsDir, str(eid)))
            except:
                myRaise()
            idList2.remove(eid)
        self.idList = idList2
        self.save()
    def load(self):
        if isfile(self.file):
            jsonStr = open(self.file).read()
            if jsonStr:
                self.setJson(jsonStr)## FIXME
        else:
            self.save()


def getDayOccurrenceData(curJd, groups):
    data = []
    for group in groups:
        if not group.enable:
            continue
        #print '\nupdateData: checking event', event.summary
        gid = group.id
        for epoch0, epoch1, eid in group.node.getEvents(getEpochFromJd(curJd), getEpochFromJd(curJd+1)):
            event = group[eid]
            text = event.getText()
            for url, fname in event.getFilesUrls():
                text += '\n<a href="%s">%s</a>'%(url, fname)
            if epoch1-epoch0==dayLen:
                data.append({
                    'time':'',
                    'text':text,
                    'icon':event.icon,
                    'ids': (gid, eid),
                })
            else:
                h0, m0, s0 = getHmsFromSeconds(epoch0 % dayLen)
                h1, m1, s1 = getHmsFromSeconds(epoch1 % dayLen)
                data.append({
                    'time':hmsRangeToStr(h0, m0, s0, h1, m1, s1),
                    'text':text,
                    'icon':event.icon,
                    'ids': (gid, eid),
                })

            '''
            occur = event.calcOccurrenceForJdRange(curJd, curJd+1)
            if not occur:
                continue
            if isinstance(occur, JdListOccurrence):
                ### len(occur) == len(occur.getDaysJdList()) == 1
                data.append({
                    'time':'',
                    'text':text,
                    'icon':icon,
                    'ids': ids,
                })
            elif isinstance(occur, TimeRangeListOccurrence):
                #print 'updateData: TimeRangeListOccurrence', occur.getTimeRangeList()
                for (startEpoch, endEpoch) in occur.getTimeRangeList():
                    (jd1, h1, min1, s1) = core.getJhmsFromEpoch(startEpoch)
                    if endEpoch is None:
                        data.append({
                            'time':timeEncode((h1, min1, s1), True),
                            'text':text,
                            'icon':icon,
                            'ids': ids,
                        })
                    else:
                        (jd2, h2, min2, s2) = core.getJhmsFromEpoch(endEpoch)
                        if jd1==curJd==jd2:
                            data.append({
                                'time':hmsRangeToStr(h1, min1, s1, h2, min2, s2),
                                'text':text,
                                'icon':icon,
                                'ids': ids,
                            })
                        elif jd1==curJd and curJd < jd2:
                            data.append({
                                'time':hmsRangeToStr(h1, min1, s1, 24, 0, 0),
                                'text':text,
                                'icon':icon,
                                'ids': ids,
                            })
                        elif jd1 < curJd < jd2:
                            data.append({
                                'time':'',
                                'text':text,
                                'icon':icon,
                                'ids': ids,
                            })
                        elif jd1 < curJd and curJd==jd2:
                            data.append({
                                'time':hmsRangeToStr(0, 0, 0, h2, min2, s2),
                                'text':text,
                                'icon':icon,
                                'ids': ids,
                            })
            elif isinstance(occur, TimeListOccurrence):
                #print 'updateData: TimeListOccurrence', occur.epochList
                for epoch in occur.epochList:
                    (jd, hour, minute, sec) = core.getJhmsFromEpoch(epoch)
                    if jd == curJd:
                        data.append({
                            'time':timeEncode((hour, minute, sec), True),
                            'text':text,
                            'icon':icon,
                            'ids': ids,
                        })
            else:
                raise TypeError
            '''
    return data


## Should not be registered, or instantiate directly
class Account(JsonEventBaseClass):
    name = ''
    desc = ''
    def __init__(self, aid=None):
        self.setId(aid)
        self.enable = True
        self.title = 'Account'
        self.remoteGroups = []## a list of dictionarise {'id':..., 'title':...}
        self.status = None## {'action': 'pull', 'done': 10, 'total': 20}
        ## action values: 'fetchGroups', 'pull', 'push'
    def setId(self, aid=None):
        if aid is None or aid<0:
            aid = core.lastEventAccountId + 1 ## FIXME
            core.lastEventAccountId = aid
        elif aid > core.lastEventAccountId:
            core.lastEventAccountId = aid
        self.id = aid
        self.file = join(accountsDir, '%d.json'%self.id)
    def stop(self):
        self.status = None
    def fetchGroups(self):
        raise NotImplementedError
    def fetchAllEventsInGroup(self, remoteGroupId):
        raise NotImplementedError
    def sync(self, group, remoteGroupId):
        raise NotImplementedError
    def getData(self):
        data = {
            'type': self.name,
        }
        for attr in ('enable', 'title', 'remoteGroups'):
            data[attr] = getattr(self, attr)
        return data
    def setData(self, data):
        for attr in ('enable', 'title', 'remoteGroups'):
            try:
                setattr(self, attr, data[attr])
            except KeyError:
                pass

########################################################################

def getWeekOccurrenceData(curAbsWeekNumber, groups):
    (startJd, endJd) = core.getJdRangeOfAbsWeekNumber(absWeekNumber)
    data = []
    for group in groups:
        if not group.enable:
            continue
        for event in group:
            if not event:
                continue
            occur = event.calcOccurrenceForJdRange(startJd, endJd)
            if not occur:
                continue
            text = event.getText()
            icon = event.icon
            ids = (group.id, event.id)
            if isinstance(occur, JdListOccurrence):
                for jd in occur.getDaysJdList():
                    (wnum, weekDay) = core.getWeekDateFromJd(jd)
                    if wnum==curAbsWeekNumber:
                        data.append({
                            'weekDay':weekDay,
                            'time':'',
                            'text':text,
                            'icon':icon,
                            'ids': ids,
                        })
            elif isinstance(occur, TimeRangeListOccurrence):
                for (startEpoch, endEpoch) in occur.getTimeRangeList():
                    (jd1, h1, min1, s1) = core.getJhmsFromEpoch(startEpoch)
                    (jd2, h2, min2, s2) = core.getJhmsFromEpoch(endEpoch)
                    (wnum, weekDay) = core.getWeekDateFromJd(jd1)
                    if wnum==curAbsWeekNumber:
                        if jd1==jd2:
                            data.append({
                                'weekDay':weekDay,
                                'time':hmsRangeToStr(h1, min1, s1, h2, min2, s2),
                                'text':text,
                                'icon':icon,
                                'ids': ids,
                            })
                        else:## FIXME
                            data.append({
                                'weekDay':weekDay,
                                'time':hmsRangeToStr(h1, min1, s1, 24, 0, 0),
                                'text':text,
                                'icon':icon,
                                'ids': ids,
                            })
                            for jd in range(jd1+1, jd2):
                                (wnum, weekDay) = core.getWeekDateFromJd(jd)
                                if wnum==curAbsWeekNumber:
                                    data.append({
                                        'weekDay':weekDay,
                                        'time':'',
                                        'text':text,
                                        'icon':icon,
                                        'ids': ids,
                                    })
                                else:
                                    break
                            (wnum, weekDay) = core.getWeekDateFromJd(jd2)
                            if wnum==curAbsWeekNumber:
                                data.append({
                                    'weekDay':weekDay,
                                    'time':hmsRangeToStr(0, 0, 0, h2, min2, s2),
                                    'text':text,
                                    'icon':icon,
                                    'ids': ids,
                                })
            elif isinstance(occur, TimeListOccurrence):
                for epoch in occur.epochList:
                    (jd, hour, minute, sec) = core.getJhmsFromEpoch(epoch)
                    (wnum, weekDay) = core.getWeekDateFromJd(jd)
                    if wnum==curAbsWeekNumber:
                        data.append({
                            'weekDay':weekDay,
                            'time':timeEncode((hour, minute, sec), True),
                            'text':text,
                            'icon':icon,
                            'ids': ids,
                        })
            else:
                raise TypeError
    return data


def getMonthOccurrenceData(curYear, curMonth, groups):
    (startJd, endJd) = core.getJdRangeForMonth(curYear, curMonth, core.primaryMode)
    data = []
    for group in groups:
        if not group.enable:
            continue
        for event in group:
            if not event:
                continue
            occur = event.calcOccurrenceForJdRange(startJd, endJd)
            if not occur:
                continue
            text = event.getText()
            icon = event.icon
            ids = (group.id, event.id)
            if isinstance(occur, JdListOccurrence):
                for jd in occur.getDaysJdList():
                    (y, m, d) = jd_to(jd, core.primaryMode)
                    if y==curYear and m==curMonth:
                        data.append({
                            'day':d,
                            'time':'',
                            'text':text,
                            'icon':icon,
                            'ids': ids,
                        })
            elif isinstance(occur, TimeRangeListOccurrence):
                for (startEpoch, endEpoch) in occur.getTimeRangeList():
                    (jd1, h1, min1, s1) = core.getJhmsFromEpoch(startEpoch)
                    (jd2, h2, min2, s2) = core.getJhmsFromEpoch(endEpoch)
                    (y, m, d) = jd_to(jd1, core.primaryMode)
                    if y==curYear and m==curMonth:
                        if jd1==jd2:
                            data.append({
                                'day':d,
                                'time':hmsRangeToStr(h1, min1, s1, h2, min2, s2),
                                'text':text,
                                'icon':icon,
                                'ids': ids,
                            })
                        else:## FIXME
                            data.append({
                                'day':d,
                                'time':hmsRangeToStr(h1, min1, s1, 24, 0, 0),
                                'text':text,
                                'icon':icon,
                                'ids': ids,
                            })
                            for jd in range(jd1+1, jd2):
                                (y, m, d) = jd_to(jd, core.primaryMode)
                                if y==curYear and m==curMonth:
                                    data.append({
                                        'day':d,
                                        'time':'',
                                        'text':text,
                                        'icon':icon,
                                        'ids': ids,
                                    })
                                else:
                                    break
                            (y, m, d) = jd_to(jd2, core.primaryMode)
                            if y==curYear and m==curMonth:
                                data.append({
                                    'day':d,
                                    'time':hmsRangeToStr(0, 0, 0, h2, min2, s2),
                                    'text':text,
                                    'icon':icon,
                                    'ids': ids,
                                })
            elif isinstance(occur, TimeListOccurrence):
                for epoch in occur.epochList:
                    (jd, hour, minute, sec) = core.getJhmsFromEpoch(epoch)
                    (y, m, d) = jd_to(jd1, core.primaryMode)
                    if y==curYear and m==curMonth:
                        data.append({
                            'day':d,
                            'time':timeEncode((hour, minute, sec), True),
                            'text':text,
                            'icon':icon,
                            'ids': ids,
                        })
            else:
                raise TypeError
    return data



#################################################################################

def loadEventTrash(groups=[]):
    trash = EventTrash()
    trash.load()
    ###
    groupedIds = trash.idList[:]
    for group in groups:
        groupedIds += group.idList
    nonGroupedIds = []
    for eid in listdir(eventsDir):
        try:
            eid = int(eid)
        except:
            continue
        if not eid in groupedIds:
            nonGroupedIds.append(eid)
    if nonGroupedIds:
        trash.idList += nonGroupedIds
        trash.save()
    ###
    return trash

def startDaemon():
    from subprocess import Popen
    Popen([daemonFile])

def checkAndStartDaemon():
    from scal2.os_utils import dead
    pidFile = join(confDir, 'event', 'daemon.pid')
    if isfile(pidFile):
        pid = int(open(pidFile).read())
        if not dead(pid):
            return
    startDaemon()

def stopDaemon():
    from scal2.os_utils import goodkill
    pidFile = join(confDir, 'event', 'daemon.pid')
    if not isfile(pidFile):
        return
    pid = int(open(pidFile).read())
    try:
        goodkill(pid)
    except Exception, e:
        log.error('Error while killing daemon process: %s'%e)
        raise e
    else:
        try:
            os.remove(pidFile)## FIXME, it should have done in daemon's source itself, using atexit! But it doesn't work
        except:
            pass

def restartDaemon():
    print 'stopping event daemon...'
    stopDaemon()
    print 'event daemon stopped, starting again...'
    startDaemon()
    print 'event daemon started'


########################################################################


def testIntersection():
    pprint.pprint(intersectionOfTwoTimeRangeList(
        [(0,1.5), (3,5), (7,9)],
        [(1,3.5), (4,7.5), (8,10)]
    ))

def testJdRanges():
    pprint.pprint(JdListOccurrence([1, 3, 4, 5, 7, 9, 10, 11, 12, 13, 14, 18]).calcJdRanges())

def testSimplifyNumList():
    pprint.pprint(simplifyNumList([1, 2, 3, 4, 5, 7, 9, 10, 14, 16, 17, 18, 19, 21, 22, 23, 24]))

if __name__=='__main__':
    import pprint
    #testIntersection()
    #testJdRanges()
    testSimplifyNumList()


