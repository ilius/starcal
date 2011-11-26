# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

import time, json, random, os, shutil
from os.path import join, split, isdir, isfile
from os import listdir
from paths import *

from scal2.utils import arange, ifloor, iceil, IteratorFromGen
from scal2.time_utils import encodeDuration, decodeDuration
from scal2.color_utils import hslToRgb

from scal2.locale_man import tr as _
from scal2.locale_man import getMonthName
from scal2 import core
from scal2.core import myRaise, getEpochFromJd, getEpochFromJhms, log, to_jd, jd_to

def makeDir(direc):
    if not isdir(direc):
        os.makedirs(direc)

eventsDir = join(confDir, 'event', 'events')
groupsDir = join(confDir, 'event', 'groups')
groupListFile = join(confDir, 'event', 'group_list.json')

trashFile = join(confDir, 'event', 'trash.json')## FIXME

makeDir(eventsDir)
makeDir(groupsDir)

class BadEventFile(Exception):## FIXME
    pass


def dateEncode(date):
    return '%.4d/%.2d/%.2d'%tuple(date)

def timeEncode(tm, checkSec=False):
    if checkSec:
        if len(tm)==3 and tm[2]>0:
            return '%.2d:%.2d:%.2d'%tuple(tm)
        else:
            return '%.2d:%.2d'%tuple(tm[:2])
    else:
        return '%.2d:%.2d:%.2d'%tuple(tm)

def dateDecode(st):
    parts = st.split('/')
    if len(parts)!=3:
        raise ValueError('bad date %s'%st)
    try:
        date = tuple([int(p) for p in parts])
    except ValueError:
        raise ValueError('bad date %s'%st)
    return date

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


hmsRangeToStr = lambda h1, m1, s1, h2, m2, s2: timeEncode((h1, m1, s1), True) + ' - ' + timeEncode((h2, m2, s2), True)


def makeCleanTimeRangeList(timeRangeList):
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
    #makeCleanTimeRangeList(result)## not needed when both timeRangeList are clean!
    return result


dataToJson = lambda data: json.dumps(data, sort_keys=True, indent=4)
dataToCompactJson = lambda data: json.dumps(data, sort_keys=True, separators=(',', ':'))

class EventBaseClass:
    order = 0 ## an int or str or everything, just effect to visible order in GUI
    getData = lambda self: None
    setData = lambda self: None
    getJson = lambda self: dataToJson(self.getData())
    getCompactJson = lambda self: dataToCompactJson(self.getData())
    setJson = lambda self, jsonStr: self.setData(json.loads(jsonStr))
    copyFrom = lambda self, other: self.setData(other.getData())
    def copy(self):
        newObj = self.__class__()
        newObj.copyFrom(self)
        return newObj

#class JsonEventItem(EventBaseClass):## FIXME
#    def __init__(self, jsonPath):
#        self.jsonPath = jsonPath
#    def saveConfig(self):
#        jstr = self.getJson()
#        open(self.jsonPath, 'w').write(jstr)
#    def loadConfig(self):
#        if not isfile(self.jsonPath):
#            raise IOError('error while loading json file %r: no such file'%self.jsonPath)
#        jsonStr = open(self.jsonPath).read()
#        if jsonStr:
#            self.setJson(jsonStr)## FIXME
    
class Occurrence(EventBaseClass):
    def __init__(self):
        self.event = None
    def __nonzero__(self):
        raise NotImplementedError
    def intersection(self):
        raise NotImplementedError
    getDaysJdList = lambda self: []
    getTimeRangeList = lambda self: []
    containsMoment = lambda self, epoch: False

class JdListOccurrence(Occurrence):
    name = 'jdList'
    __repr__ = lambda self: 'JdListOccurrence(%r)'%list(self.jdSet)
    def __init__(self, jdList=None):
        Occurrence.__init__(self)
        if not jdList:
            jdList = []
        self.jdSet = set(jdList)
    __nonzero__ = lambda self: bool(self.jdSet)
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
    containsMoment = lambda self, epoch: (core.getJdFromEpoch(epoch) in self.jdSet)
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
    __repr__ = lambda self: 'TimeRangeListOccurrence(%r)'%self.rangeList
    def __init__(self, rangeList=None):
        Occurrence.__init__(self)
        if not rangeList:
            rangeList = []
        self.rangeList = rangeList
    __nonzero__ = lambda self: bool(self.rangeList)
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
            for jd in core.getJdListFromEpochRange(startEpoch, endEpoch):
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
    __repr__ = lambda self: 'TimeListOccurrence(%r)'%self.epochList
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
    #__nonzero__ = lambda self: self.startEpoch == self.endEpoch
    __nonzero__ = lambda self: bool(self.epochList)
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
            jd = core.getJdFromEpoch(epoch)
            if not jd in jdList:
                jdList.append(jd)
        return jdList
    def getTimeRangeList(self):
        return [(epoch, epoch+0.01) for epoch in self.epochList]## or end=None ## FIXME
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


class EventRule(EventBaseClass):
    name = 'custom'## or 'event' or '' FIXME
    desc = _('Custom Event Rule')## FIXME
    provide = ()
    need = ()
    conflict = ()
    sgroup = -1
    expand = False
    params = ()
    def __init__(self, event):
        self.event = event
        self.mode = None ## use event.mode
    getMode = lambda self: self.event.mode if self.mode is None else self.mode
    def getConfigLine(self):
        return self.name
    def setFromConfig(self, parts):
        pass
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict):
        raise NotImplementedError
    def getData(self):
        return dict([(param, getattr(self, param)) for param in self.params])
    def setData(self, data):
        #if isinstance(data, dict):## FIXME
        for (key, value) in data.items():
            if key in self.params:
                setattr(self, key, value)
    getInfo = lambda self: ''

class YearEventRule(EventRule):
    name = 'year'
    desc = _('Year')
    params = ('year',)
    def __init__(self, event):
        EventRule.__init__(self, event)
        self.year = core.getSysDate(self.getMode())[0] ## FIXME
    def getData(self):
        return self.year
    def setData(self, year):
        self.year = year
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict):## improve performance ## FIXME
        jdList = []
        for jd in core.getJdListFromEpochRange(startEpoch, endEpoch):
            if jd not in jdList and jd_to(jd, self.getMode())[0]==self.year:
                jdList.append(jd)
        return JdListOccurrence(jdList)
    getInfo = lambda self: self.desc + ': ' + _(self.year)




class MonthEventRule(EventRule):
    name = 'month'
    desc = _('Month')
    params = ('month',)
    def __init__(self, event):
        EventRule.__init__(self, event)
        self.month = 1
    def getData(self):
        return self.month
    def setData(self, month):
        self.month = month
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict):## improve performance ## FIXME
        jdList = []
        for jd in core.getJdListFromEpochRange(startEpoch, endEpoch):
            if jd not in jdList and jd_to(jd, self.getMode())[1]==self.month:
                jdList.append(jd)
        return JdListOccurrence(jdList)
    getInfo = lambda self: self.desc + ': ' + getMonthName(self.getMode(), self.month)


class DayOfMonthEventRule(EventRule):
    name = 'day'
    desc = _('Day of Month')
    params = ('day',)
    def __init__(self, event):
        EventRule.__init__(self, event)
        self.day = 1
    def getData(self):
        return self.day
    def setData(self, day):
        self.day = day
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict):## improve performance ## FIXME
        jdList = []
        for jd in core.getJdListFromEpochRange(startEpoch, endEpoch):
            if jd not in jdList and jd_to(jd, self.getMode())[2]==self.day:
                jdList.append(jd)
        return JdListOccurrence(jdList)
    getInfo = lambda self: self.desc + '(' + _(self.getMode()) + '): ' + _(self.day)



class WeekNumberModeEventRule(EventRule):
    name = 'weekNumMode'
    desc = _('Week Number')
    params = ('weekNumMode',)
    (EVERY_WEEK, ODD_WEEKS, EVEN_WEEKS) = range(3) ## remove EVERY_WEEK? FIXME
    weekNumModeNames = ('any', 'odd', 'even')## remove 'any'? FIXME
    def __init__(self, event):
        EventRule.__init__(self, event)
        self.weekNumMode = self.EVERY_WEEK
    def getData(self):
        return self.weekNumModeNames[self.weekNumMode]
    def setData(self, modeName):
        if not modeName in self.weekNumModeNames:
            raise BadEventFile('bad rule weekNumMode=%r, the value for weekNumMode must be one of %r'\
                %(modeName, self.weekNumModeNames))
        self.weekNumMode = self.weekNumModeNames.index(modeName)
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict):## improve performance ## FIXME
        (y, m, d) = rulesDict['start'].date ## ruleStartDate
        startAbsWeekNum = core.getAbsWeekNumberFromJd(to_jd(y, m, d, self.getMode())) - 1 ## 1st week ## FIXME
        jdListAll = core.getJdListFromEpochRange(startEpoch, endEpoch)
        if self.weekNumMode==self.EVERY_WEEK:
            jdList = jdListAll
        elif self.weekNumMode==ODD_WEEKS:
            jdList = []
            for jd in jdListAll:
                if (core.getAbsWeekNumberFromJd(jd)-startAbsWeekNum)%2==1:
                    jdList.append(jd)
        elif self.weekNumMode==EVEN_WEEKS:
            jdList = []
            for jd in jdListAll:
                if (core.getAbsWeekNumberFromJd(jd)-startAbsWeekNum)%2==0:
                    jdList.append(jd)
        return JdListOccurrence(jdList)
    def getInfo(self):
        if self.weekNumMode == self.EVERY_WEEK:
            return ''
        elif self.weekNumMode == self.ODD_WEEKS:
            return _('Odd Weeks')
        elif self.weekNumMode == self.EVEN_WEEKS:
            return _('Even Weeks')

class WeekDayEventRule(EventRule):
    name = 'weekDay'
    desc = _('Day of Week')
    params = ('weekDayList',)
    def __init__(self, event):
        EventRule.__init__(self, event)
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
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict):## improve performance ## FIXME
        jdList = []
        for jd in core.getJdListFromEpochRange(startEpoch, endEpoch):
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

class CycleDaysEventRule(EventRule):
    name = 'cycleDays'
    desc = _('Cycle Days Number')
    need = ('start',)
    conflict = ('dayTime', 'cycleLen')
    params = ('cycleDays',)
    def __init__(self, event):
        EventRule.__init__(self, event)
        self.cycleDays = 7
    def getData(self):
        return self.cycleDays
    def setData(self, cycleDays):
        self.cycleDays = cycleDays
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict):## improve performance ## FIXME
        (year, month, day) = rulesDict['start'].date
        startJd = max(to_jd(year, month, day, self.getMode()),
                      core.getJdFromEpoch(startEpoch))
        endJd = core.getJdFromEpoch(endEpoch-0.01)+1
        if rulesDict.has_key('end'):
            (year, month, day) = rulesDict['end'].date
            endJd = min(endJd, to_jd(year, month, day, self.getMode())+1) ## +1 FIXME
        return JdListOccurrence(range(startJd, endJd, self.cycleDays))
    getInfo = lambda self: _('Repeat: Every %s Days')%_(self.cycleDays)

class DayTimeEventRule(EventRule):## Moment Event
    name = 'dayTime'
    desc = _('Time in Day')
    provide = ('time',)
    conflict = ('cycleLen',)
    params = ('dayTime',)
    def __init__(self, event):
        EventRule.__init__(self, event)
        self.dayTime = time.localtime()[3:6]
    def getData(self):
        return timeEncode(self.dayTime)
    def setData(self, data):
        self.dayTime = timeDecode(data)
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict):
        mySec = core.getSecondsFromHms(*self.dayTime)
        (startJd, startExtraSec) = core.getJdAndSecondsFromEpoch(startEpoch)
        (endJd, endExtraSec) = core.getJdAndSecondsFromEpoch(endEpoch)
        if startExtraSec > mySec:
            startJd += 1
        if endExtraSec < mySec:
            endJd -= 1
        return TimeListOccurrence(## FIXME
            getEpochFromJd(startJd)+mySec,
            getEpochFromJd(endJd)+mySec+1,
            24*3600,
        )
        
    getInfo = lambda self: _('Time in Day') + ': ' + timeEncode(self.dayTime)


class DayTimeRangeEventRule(EventRule):## use for UniversityClassEvent
    name = 'dayTimeRange'
    desc = 'Day Time Range'
    conflict = ('dayTime',)
    params = ('dayTimeStart', 'dayTimeEnd')
    def __init__(self, event):
        EventRule.__init__(self, event)
        self.dayTimeStart = (0, 0, 0)
        self.dayTimeEnd = (24, 0, 0)
    def getData(self):
        return (timeEncode(self.dayTimeStart), timeEncode(self.dayTimeEnd))
    def setData(self, data):
        self.dayTimeStart = timeDecode(data[0])
        self.dayTimeEnd = timeEncode(data[1])
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict):
        daySecStart = getSecondsFromHms(*self.dayTimeStart)
        daySecEnd = getSecondsFromHms(*self.dayTimeEnd)
        startDiv, startMod = divmod(startEpoch, 24*3600)
        endDiv, endMod = divmod(endEpoch, 24*3600)
        return intersectionOfTwoTimeRangeList(
            [(i*24*3600+daySecStart, i*24*3600+daySecEnd) for i in range(startDiv, endDiv+1)],
            [(startEpoch, endEpoch)],
        )


class DateAndTimeEventRule(EventRule):
    sgroup = 1
    params = ('date', 'time')
    def __init__(self, event):
        EventRule.__init__(self, event)
        self.date = core.getSysDate(self.getMode())
        self.time = time.localtime()[3:6]
    def getEpoch(self):
        (year, month, day) = self.date
        return getEpochFromJhms(to_jd(year, month, day, self.getMode()), *tuple(self.time))
    def getData(self):
        return {
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

class StartEventRule(DateAndTimeEventRule):
    name = 'start'
    desc = _('Start')
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict):
        myEpoch = self.getEpoch()
        if endEpoch <= myEpoch:
            return TimeRangeListOccurrence([])
        if startEpoch < myEpoch:
            startEpoch = myEpoch
        return TimeRangeListOccurrence([(startEpoch, endEpoch)])

class EndEventRule(DateAndTimeEventRule):
    name = 'end'
    desc = _('End')
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict):
        endEpoch = min(endEpoch, self.getEpoch())
        if startEpoch >= endEpoch:## how about startEpoch==endEpoch FIXME
            return TimeRangeListOccurrence([])
        else:
            return TimeRangeListOccurrence([(startEpoch, endEpoch)])


class DurationEventRule(EventRule):
    name = 'duration'
    desc = _('Duration')
    need = ('start',)
    conflict = ('end',)
    sgroup = 1
    def __init__(self, event):
        EventRule.__init__(self, event)
        self.value = 0
        self.unit = 1 ## seconds
    getSeconds = lambda self: self.value * self.unit
    def setData(self, data):
        try:
            (self.value, self.unit) = decodeDuration(data)
        except Exception, e:
            log.error('Error while loading event rule "%s": %s'%(self.name, e))
    getData = lambda self: encodeDuration(self.value, self.unit)
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict):
        endEpoch = min(endEpoch, rulesDict['start'].getEpoch() + self.getSeconds())
        if startEpoch >= endEpoch:## how about startEpoch==endEpoch FIXME
            return TimeRangeListOccurrence([])
        else:
            return TimeRangeListOccurrence([(startEpoch, endEpoch)])

class CycleLenEventRule(EventRule):
    name = 'cycleLen'
    desc = _('Cycle Length (Days & Time)')
    provide = ('time',)
    need = ('start',)
    conflict = ('dayTime', 'cycleDays',)
    params = ('cycleDays', 'cycleExtraTime',)
    def __init__(self, event):
        EventRule.__init__(self, event)
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
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict):
        startEpoch = max(startEpoch, rulesDict['start'].getEpoch())
        if rulesDict.has_key('end'):
            endEpoch = min(endEpoch, rulesDict['end'].getEpoch())
        elif rulesDict.has_key('duration'):
            endEpoch = min(endEpoch, startEpoch + rulesDict['duration'].getSeconds())
        cycleSec = self.cycleDays*24*3600 + core.getSecondsFromHms(*self.cycleExtraTime)
        return TimeListOccurrence(startEpoch, endEpoch, cycleSec)
    getInfo = lambda self: _('Repeat: Every %s Days and %s')%(_(self.cycleDays), timeEncode(self.cycleExtraTime))

#class HolidayEventRule(EventRule):## FIXME
#    name = 'holiday'
#    desc = _('Holiday')


#class ShowInMCalEventRule(EventRule):## FIXME
#    name = 'show_cal'
#    desc = _('Show in Calendar')

#class SunTimeRule(EventRule):## FIXME
## ... minutes before Sun Rise      eval('sunRise-x')
## ... minutes after Sun Rise       eval('sunRise+x')
## ... minutes before Sun Set       eval('sunSet-x')
## ... minutes after Sun Set        eval('sunSet+x')


class EventNotifier(EventBaseClass):
    name = 'custom'## FIXME
    desc = _('Custom Event Notifier')## FIXME
    params = ()
    def __init__(self, event):
        self.event = event
        self.mode = None ## use event.mode
    getMode = lambda self: self.event.mode if self.mode is None else self.mode
    def notify(self, finishFunc):
        pass
    def getData(self):
        return dict([(param, getattr(self, param)) for param in self.params])
    def setData(self, data):
        #if isinstance(data, dict):## FIXME
        for (key, value) in data.items():
            if key in self.params:
                setattr(self, key, value)



class AlarmNotifier(EventNotifier):
    name = 'alarm'
    desc = _('Alarm')
    params = ('alarmSound', 'playerCmd')
    ###
    defaultAlarmSound = '' ## FIXME
    defaultPlayerCmd = 'mplayer'
    def __init__(self, event):
        EventNotifier.__init__(self, event)
        self.alarmSound = self.defaultAlarmSound
        self.playerCmd = self.defaultPlayerCmd


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




class WindowMsgNotifier(EventNotifier):
    name = 'windowMsg'
    desc = _('Message Window')## FIXME
    params = ('extraMessage',)
    def __init__(self, event):
        EventNotifier.__init__(self, event)
        self.extraMessage = ''
        ## window icon ## FIXME


class CommandNotifier(EventNotifier):
    name = 'command'
    desc = _('Run a Command')
    params = ('command', 'pyEval')
    def __init__(self, event):
        EventNotifier.__init__(self, event)
        self.command = ''
        self.pyEval = False
    

class Event(EventBaseClass):
    name = 'custom'
    desc = _('Custom Event')
    defaultIconName = ''
    requiredRules = ()
    supportedRules = None
    requiredNotifiers = ()
    def __init__(self, eid=None):
        self.setId(eid)
        self.mode = core.primaryMode
        self.icon = '' ## to show in calendar
        self.summary = self.desc + ' (' + _(self.eid) + ')'
        self.description = ''
        self.calType = core.primaryMode
        self.showInTimeLine = False ## FIXME
        self.files = []
        ######
        self.rules = []
        self.notifiers = []
        self.checkRequirements()
        self.setDefaults()
    __nonzero__ = lambda self: bool(self.rules) ## FIXME
    def getInfo(self):
        lines = []
        rulesDict = self.getRulesDict()
        ##
        hasYear = 'year' in rulesDict
        year = rulesDict['year'].year if hasYear else None
        ##
        hasMonth = 'month' in rulesDict
        month = rulesDict['month'].month if hasMonth else None
        ##
        hasDay = 'day' in rulesDict
        day = rulesDict['day'].day if hasDay else None
        ##
        if hasMonth:
            if hasYear:
                if hasDay:
                   lines.append(dateEncode((year, month, day)))
                   del rulesDict['day']
                else:
                   lines.append(getMonthName(self.mode, month, year) + ' ' + _(year))
                del rulesDict['year'], rulesDict['month']
            else:
                if hasDay:
                    lines.append(_(day) + ' ' + getMonthName(self.mode, month, year))
                    rulesDict['month'], rulesDict['day']
        ##
        for rule in sorted(rulesDict.values()):
            lines.append(rule.getInfo())
        return '\n'.join(lines)
    def checkRequirements(self):
        ruleNames = (rule.name for rule in self.rules)
        for name in self.requiredRules:
            if not name in ruleNames:
                self.rules.append(eventRulesClassDict[name](self))
        notifierNames = (notifier.name for notifier in self.notifiers)
        for name in self.requiredNotifiers:
            if not name in notifierNames:
                self.notifiers.append(eventNotifiersClassDict[name](self))
    def setDefaults(self):
        pass
    def setDefaultsFromGroup(self, group):
        if not self.icon:
            self.icon = group.defaultIcon 
    def copyFrom(self, other):## FIXME
        self.mode = other.mode
        self.icon = other.icon
        self.summary = other.summary
        self.description = other.description
        self.calType = other.calType
        self.showInTimeLine = other.showInTimeLine
        self.files = other.files
        ######
        if self.supportedRules is None:
            self.rules = other.rules[:]
        else:
            rulesDict = self.getRulesDict()
            for rule in other.rules:
                if rule.name in self.supportedRules:
                    try:
                        rulesDict[rule.name].copyFrom(rule)
                    except KeyError:
                        self.rules.append(rule)
        self.notifiers = other.notifiers[:]## FIXME
        self.checkRequirements()
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
    getText = lambda self: self.summary if self.summary else self.description
    def setId(self, eid=None):
        if eid is None or eid<0:
            eid = core.lastEventId + 1 ## FIXME
            core.lastEventId = eid
        elif eid > core.lastEventId:
            core.lastEventId = eid
        self.eid = eid
        self.eventDir = join(eventsDir, str(self.eid))
        self.eventFile = join(self.eventDir, 'event.json')
        self.occurrenceFile = join(self.eventDir, 'occurrence')## file or directory? ## FIXME
        self.filesDir = join(self.eventDir, 'files')
        self.loadFiles()
    def getData(self):
        return {
            'type': self.name,
            'calType': core.modules[self.mode].name,
            'rules': self.getRulesData(),
            'notifiers': self.getNotifiersData(),
            'icon': self.icon,
            'summary': self.summary,
            'description': self.description,
        }
    def setData(self, data):
        if 'id' in data:
            self.setId(data['id'])
        for attr in ('icon', 'summary', 'description'):
            if attr in data:
                setattr(self, attr, data[attr])
        ####
        if 'calType' in data:
            calType = data['calType']
            for (i, module) in enumerate(core.modules):
                if module.name == calType:
                    self.mode = i
                    break
            else:
                raise ValueError('Invalid calType: %r'%calType)
        ####
        self.rules = []
        for (rule_name, rule_data) in data['rules']:
            rule = eventRulesClassDict[rule_name](self)
            rule.setData(rule_data)
            self.rules.append(rule)
        ####
        self.notifiers = []
        if 'notifiers' in data:
            for (notifier_name, notifier_data) in data['notifiers']:
                notifier = eventNotifiersClassDict[notifier_name](self)
                notifier.setData(notifier_data)
                self.notifiers.append(notifier)
    def saveConfig(self):
        if not isdir(self.eventDir):
            os.makedirs(self.eventDir)
        jstr = self.getJson()
        open(self.eventFile, 'w').write(jstr)
    def loadConfig(self):## skipRules arg for use in ui_gtk/event/notify.py ## FIXME
        if not isdir(self.eventDir):
            raise IOError('error while loading event directory %r: no such directory'%self.eventDir)
        if not isfile(self.eventFile):
            raise IOError('error while loading event file %r: no such file'%self.eventFile)
        jsonStr = open(self.eventFile).read()
        if jsonStr:
            self.setJson(jsonStr)## FIXME
    def addRule(self, rule):
        (ok, msg) = self.checkRulesDependencies(newRule=rule)
        if ok:
            self.rules.append(rule)
        return (ok, msg)
    def removeRule(self, rule):
        (ok, msg) = self.checkRulesDependencies(disabledRule=rule)
        if ok:
            self.rules.remove(rule)
        return (ok, msg)
    def checkRulesDependencies(self, newRule=None, disabledRule=None, autoCheck=True):
        rules = self.rules[:]
        if newRule:
            rules.append(newRule)
        if disabledRule:
            #try:
            rules.remove(disabledRule)
            #except:
            #    pass
        rulesDict = dict([(rule.name, rule) for rule in rules])
        provideList = []
        for rule in rules:
            provideList.append(rule.name)
            provideList += rule.provide
        for rule in rules:
            for conflictName in rule.conflict:
                if conflictName in provideList:
                    return (False, '%s "%s" %s "%s"'%(
                        _('Conflict between'),
                        _(rule.desc),
                        _('and'),
                        _(rulesDict[conflictName].desc),
                    ))
            for needName in rule.need:
                if not needName in provideList:
                    ## find which rule(s) provide(s) needName ## FIXME
                    return (False, '"%s" %s "%s"'%(
                        _(rule.desc),
                        _('needs'),
                        _(needName), #_(rulesDict[needName].desc)
                    ))
        return (True, '')
    getRulesData = lambda self: [(rule.name, rule.getData()) for rule in self.rules]
    getRulesDict = lambda self: dict([(rule.name, rule) for rule in self.rules])
    getRuleNames = lambda self: [rule.name for rule in self.rules]
    def __getitem__(self, ruleType):## or getRule
        for rule in self.rules:
            if rule.name == ruleType:
                return rule
    getNotifiersData = lambda self: [(notifier.name, notifier.getData()) for notifier in self.notifiers]
    getNotifiersDict = lambda self: dict(self.getNotifiersData())
    def removeSomeRuleTypes(self, *rmTypes):
        rules2 = []
        for rule in self.rules:
            if not rule.name in rmTypes:
                rules2.append(rule)
        self.rules = rules2
    def calcOccurrenceForJdRange(self, startJd, endJd):## float jd ## cache Occurrences ## FIXME
        if not self.rules:
            return []
        startEpoch = getEpochFromJd(startJd)
        endEpoch = getEpochFromJd(endJd)
        rulesDict = self.getRulesDict()
        occur = self.rules[0].calcOccurrence(startEpoch, endEpoch, rulesDict)
        if not hasattr(occur, 'intersection'):
            print self.rules[0].name, occur.__class__.__name__, occur #dir(occur)
            raise
        #if self.eid==3:
        #    print 'occur = %r\n\n'%occur
        for rule in self.rules[1:]:
            #if self.eid==3:
            #    print 'occur = %r'%occur
            #    print 'occur intersection with %r'%rule.calcOccurrence(startEpoch, endEpoch, rulesDict)
            occur = occur.intersection(rule.calcOccurrence(startEpoch, endEpoch, rulesDict))
        #if self.eid==3:
        #    print 'final occur = %r\n\n'%occur
        occur.event = self
        return occur ## FIXME
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


class YearlyEvent(Event):
    name = 'yearly'
    desc = _('Yearly Event')
    requiredRules = ('month', 'day')
    supportedRules = ('month', 'day')
    getMonth = lambda self: self['month'].month
    def setMonth(self, month):
        self['month'].month = month
    getDay = lambda self: self['day'].day
    def setDay(self, day):
        self['day'].day = day
    #getIcon = lambda self: self.icon ## FIXME
    #def setIcon(self, icon): ## FIXME
    #    self.icon = icon
    def setDefaults(self):
        (y, m, d) = core.getSysDate(self.mode)
        self.setMonth(m)
        self.setDay(d)
    def calcOccurrenceForJdRange(self, startJd, endJd):## float jd
        mode = self.mode
        month = self.getMonth()
        day = self.getDay()
        startYear = jd_to(ifloor(startJd), mode)[0]
        endYear = jd_to(iceil(endJd), mode)[0]
        jdList = []
        for year in range(startYear, endYear+1):
            jd = to_jd(year, month, day, mode)
            if startJd <= jd < endJd:
                jdList.append(jd)
        return JdListOccurrence(jdList)


class DailyNoteEvent(YearlyEvent):
    name = 'dailyNote'
    desc = _('Daily Note')
    defaultIconName = 'note'
    requiredRules = ('year', 'month', 'day')
    supportedRules = ('year', 'month', 'day')
    getYear = lambda self: self['year'].year
    def setYear(self, year):
        self['year'].year = year
    getDate = lambda self: (self.getYear(), self.getMonth(), self.getDay())
    getJd = lambda self: to_jd(self.getYear(), self.getMonth(), self.getDay(), self.mode)
    def setDate(self, year, month, day):
        self.setYear(year)
        self.setMonth(month)
        self.setDay(day)
    def setDefaults(self):
        self.setDate(*core.getSysDate(self.mode))
    def calcOccurrenceForJdRange(self, startJd, endJd):## float jd
        jd = self.getJd()
        return JdListOccurrence([jd] if startJd <= jd < endJd else [])

class TaskEvent(Event):
    ## Y/m/d H:M none              ==> start, None
    ## Y/m/d H:M for H:M           ==> start, end
    ## Y/m/d H:M until Y/m/d H:M   ==> start, end
    name = 'task'
    desc = _('Task')
    defaultIconName = 'task'
    requiredRules = ('start',)
    supportedRules = ('start', 'end', 'duration')
    def __init__(self, eid=None):
        Event.__init__(self, eid)
    def setStart(self, date, dayTime):
        startRule = self['start']
        startRule.date = date
        startRule.time = dayTime
    def setEnd(self, endType, *values):
        self.removeSomeRuleTypes('end', 'duration')
        if not endType:
            return
        if not values:
            return
        if endType=='date':
            rule = EndEventRule(self)
            (rule.date, rule.time) = values
        elif endType=='duration':
            rule = DurationEventRule(self)
            (rule.value, rule.unit) = values
        else:
            raise ValueError('invalid endType=%r'%endType)
        self.rules.append(rule)
    def removeEnd(self):
        try:
            self.rules.remove(self['end'])
        except:
            pass
    def getStart(self):
        startRule = self['start']
        return (startRule.date, startRule.time)
    getStartEpoch = lambda self: self['start'].getEpoch()
    def getEnd(self):
        rulesDict = self.getRulesDict()
        try:
            rule = rulesDict['end']
        except KeyError:
            pass
        else:
            return ('date', (rule.date, rule.time))
        try:
            rule = rulesDict['duration']
        except KeyError:
            pass
        else:
            return ('duration', (rule.value, rule.unit))
        return (None, ())
    def getEndEpoch(self):
        rulesDict = self.getRulesDict()
        try:
            rule = rulesDict['end']
        except KeyError:
            pass
        else:
            return rule.getEpoch()
        try:
            rule = rulesDict['duration']
        except KeyError:
            pass
        else:
            return rulesDict['start'].getEpoch() + rule.getSeconds()
        return None
    def setDefaults(self):
        self.setStart(
            core.getSysDate(self.mode),
            tuple(time.localtime()[3:6]),
        )
    def setDefaultsFromGroup(self, group):
        Event.setDefaultsFromGroup(self, group)
        if group.name == 'taskList':
            value, unit = group.defaultDuration
            if value > 0:
                self.setEnd('duration', value, unit)
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



class UniversityClassEvent(Event):## FIXME
    ## start, end, weekDay, weekNumberMode, dayTime --- notifierName='alarm' --- showInTimeLine
    name = 'universityClass'
    desc = _('University Class')
    defaultIconName = 'university'
    #requiredRules = 
    #supportedRules = 

class EventContainer(EventBaseClass):
    name = ''
    desc = ''
    def __init__(self):
       self.eventIds = [] 
       self.title = 'Untitled'
    def getEvent(self, eid):
        assert eid in self.eventIds
        eventFile = join(eventsDir, str(eid), 'event.json')
        if not isfile(eventFile):
            raise IOError('error while loading event file %r: no such file (container title: %s)'%(eventFile, self.title))
        data = json.loads(open(eventFile).read())
        data['eid'] = eid ## FIXME
        event = eventsClassDict[data['type']](eid)
        event.setData(data)
        return event
    def getEventsGen(self):
        for eid in self.eventIds:
            yield self.getEvent(eid)
    __iter__ = lambda self: IteratorFromGen(self.getEventsGen())
    __len__ = lambda self: len(self.eventIds)
    insert = lambda self, index, event: self.eventIds.insert(index, event.eid)
    append = lambda self, event: self.eventIds.append(event.eid)
    index = lambda self, eid: self.eventIds.index(eid)
    moveUp = lambda self, index: self.eventIds.insert(index-1, self.eventIds.pop(index))
    moveDown = lambda self, index: self.eventIds.insert(index+1, self.eventIds.pop(index))
    def excludeEvent(self, eid):## call when moving to trash
        '''
            excludes event from this container (group or trash), not remove event data completely
            and returns the index of (previously contained) event
        '''
        index = self.eventIds.index(eid)
        self.eventIds.remove(eid)
        return index

class EventGroup(EventContainer):
    name = 'group'
    desc = _('Event Group')
    acceptsEventTypes = None ## None means all event types
    actions = []## [('Export to CSV', 'exportCsv')]
    eventActions = [] ## FIXME
    def __init__(self, gid=None, title=None):
        EventContainer.__init__(self)
        self.setId(gid)
        self.enable = True
        if title is None:
            title = self.desc
        self.title = title
        self.color = hslToRgb(random.uniform(0, 360), 1, 0.5)## FIXME
        self.defaultIcon = ''
        if self.acceptsEventTypes:
            if len(self.acceptsEventTypes)==1:
                defaultIconName = eventsClassDict[self.acceptsEventTypes[0]].defaultIconName
                if defaultIconName:
                    self.defaultIcon = join(pixDir, 'event', defaultIconName+'.png')
        self.defaultEventType = 'custom'
        self.defaultMode = core.primaryMode
        self.eventCacheSize = 0
        self.eventCache = {} ## from eid to event object
    __nonzero__ = lambda self: True ## FIXME
    def setId(self, gid=None):
        if gid is None or gid<0:
            gid = core.lastEventGroupId + 1 ## FIXME
            core.lastEventGroupId = gid
        elif gid > core.lastEventGroupId:
            core.lastEventGroupId = gid
        self.gid = gid
        self.groupFile = join(groupsDir, '%d.json'%self.gid)
    def getData(self):
        return {
            'enable': self.enable,
            'type': self.name,
            'title': self.title,
            'color': self.color,
            'defaultIcon': self.defaultIcon,
            'defaultEventType': self.defaultEventType,
            'defaultCalType': core.modules[self.defaultMode].name,
            'eventCacheSize': self.eventCacheSize,
            'eventIds': self.eventIds,
        }
    def setData(self, data):
        if 'id' in data:
            self.setId(data['id'])
        for attr in ('enable', 'title', 'color', 'defaultIcon', 'eventCacheSize', 'eventIds'):
            if attr in data:
                setattr(self, attr, data[attr])
        ####
        if 'defaultEventType' in data:
            self.defaultEventType = data['defaultEventType']
            if not self.defaultEventType in eventsClassDict:
                raise ValueError('Invalid defaultEventType: %r'%self.defaultEventType)
        ####
        if 'defaultCalType' in data:
            defaultCalType = data['defaultCalType']
            for (i, module) in enumerate(core.modules):
                if module.name == defaultCalType:
                    self.defaultMode = i
                    break
            else:
                raise ValueError('Invalid defaultCalType: %r'%defaultCalType)
    def saveConfig(self):
        jstr = self.getJson()
        open(self.groupFile, 'w').write(jstr)
    def loadConfig(self):
        if not isfile(self.groupFile):
            raise IOError('error while loading group file %r: no such file'%self.groupFile)
        jsonStr = open(self.groupFile).read()
        if jsonStr:
            self.setJson(jsonStr)## FIXME
    def getEvent(self, eid):
        assert eid in self.eventIds
        if eid in self.eventCache:
            return self.eventCache[eid]
        event = EventContainer.getEvent(self, eid)
        if len(self.eventCache) < self.eventCacheSize:
            self.eventCache[eid] = event
        return event
    def excludeEvent(self, eid):## call when moving to trash
        index = EventContainer.excludeEvent(self, eid)
        try:
            del self.eventCache[eid]
        except:
            pass
        return index
    def excludeAll(self):
        self.eventIds = []
        self.eventCache = {}
    def insert(self, index, event):
        self.eventIds.insert(index, event.eid)
        if len(self.eventCache) < self.eventCacheSize:
            self.eventCache[event.eid] = event
    def append(self, event):
        self.eventIds.append(event.eid)
        if len(self.eventCache) < self.eventCacheSize:
            self.eventCache[event.eid] = event
    def exportToIcs(self, fpath, startJd, endJd):
        from scal2.ics import icsTmFormat, icsHeader, getIcsTimeByEpoch
        from time import strftime
        icsText = icsHeader
        currentTimeStamp = strftime(icsTmFormat)
        for event in self:
            occur = event.calcOccurrenceForJdRange(startJd, endJd)
            if not occur:
                continue
            if isinstance(occur, JdListOccurrence):
                for sectionStartJd, sectionEndJd in occur.calcJdRanges():
                    icsText += 'BEGIN:VEVENT\n'
                    icsText += 'CREATED:%s\n'%currentTimeStamp
                    icsText += 'LAST-MODIFIED:%s\n'%currentTimeStamp
                    icsText += 'DTSTART;VALUE=DATE:%.4d%.2d%.2d\n'%jd_to(sectionStartJd, DATE_GREG)
                    icsText += 'DTEND;VALUE=DATE:%.4d%.2d%.2d\n'%jd_to(sectionEndJd, DATE_GREG)
                    icsText += 'CATEGORIES:%s\n'%self.title
                    icsText += 'TRANSP:TRANSPARENT\n' ## http://www.kanzaki.com/docs/ical/transp.html
                    icsText += 'SUMMARY:%s\n'%event.summary
                    icsText += 'END:VEVENT\n'
            elif isinstance(occur, (TimeRangeListOccurrence, TimeListOccurrence)):
                for startEpoch, endEpoch in occur.getTimeRangeList():
                    icsText += 'BEGIN:VEVENT\n'
                    icsText += 'CREATED:%s\n'%currentTimeStamp
                    icsText += 'LAST-MODIFIED:%s\n'%currentTimeStamp
                    icsText += 'DTSTART:%s\n'%getIcsTimeByEpoch(startEpoch)
                    if endEpoch is not None and endEpoch-startEpoch > 1:
                        icsText += 'DTEND:%s\n'%getIcsTimeByEpoch(int(endEpoch))## why its float? FIXME
                    icsText += 'CATEGORIES:%s\n'%self.title
                    icsText += 'TRANSP:OPAQUE\n' ## FIXME ## http://www.kanzaki.com/docs/ical/transp.html
                    icsText += 'SUMMARY:%s\n'%event.summary
                    icsText += 'END:VEVENT\n'
            else:
                raise RuntimeError
        icsText += 'END:VCALENDAR\n'
        open(fpath, 'w').write(icsText)


## TaskList, NoteBook, UniversityTerm, EventGroup

class TaskList(EventGroup):
    name = 'taskList'
    desc = _('Task List')
    acceptsEventTypes = ('task',)
    #actions = EventGroup.actions + []
    def __init__(self, gid=None, title=None):
        EventGroup.__init__(self, gid, title)
        self.defaultDuration = (0, 1) ## (value, unit)
        ## if defaultDuration[0] is set to zero, the checkbox for task's end, will be unchecked for new tasks
    def getData(self):
        data = EventGroup.getData(self)
        data.update({
            'defaultDuration': encodeDuration(*self.defaultDuration),
        })
        return data
    def setData(self, data):
        EventGroup.setData(self, data)
        if 'defaultDuration' in data:
            self.defaultDuration = decodeDuration(data['defaultDuration'])


class NoteBook(EventGroup):
    name = 'noteBook'
    desc = _('Note Book')
    acceptsEventTypes = ('dailyNote',)
    #actions = EventGroup.actions + []

class UniversityTerm(EventGroup):
    name = 'universityTerm'
    desc = _('University Term')
    acceptsEventTypes = ('universityClass',)
    #actions = EventGroup.actions + []

class EventGroupsHolder:
    def __init__(self):
        self.clear()
    def clear(self):
        self.groupsDict = {}
        self.groupIds = []
    def iterGen(self):
        for gid in self.groupIds:
            yield self.groupsDict[gid]
    __iter__ = lambda self: IteratorFromGen(self.iterGen())
    __len__ = lambda self: len(self.groupIds)
    index = lambda self, gid: self.groupIds.index(gid) ## or get group obj instead of gid? FIXME
    __getitem__ = lambda self, gid: self.groupsDict.__getitem__(gid)
    __setitem__ = lambda self, gid, group: self.groupsDict.__setitem__(gid, group)
    def insert(self, index, group):
        gid = group.gid
        assert not gid in self.groupIds
        self.groupsDict[gid] = group
        self.groupIds.insert(index, gid)
    def append(self, group):
        gid = group.gid
        assert not gid in self.groupIds
        self.groupsDict[gid] = group
        self.groupIds.append(gid)
    def delete(self, group):
        gid = group.gid
        assert gid in self.groupIds
        assert not group.eventIds ## FIXME
        try:
            os.remove(group.groupFile)
        except:
            myRaise()
        else:
            del self.groupsDict[gid]
            self.groupIds.remove(gid)
    def pop(self, index):
        gid = self.groupIds.pop(index)
        group = self.groupsDict.pop(gid)
        return group
    moveUp = lambda self, index: self.groupIds.insert(index-1, self.groupIds.pop(index))
    moveDown = lambda self, index: self.groupIds.insert(index+1, self.groupIds.pop(index))
    #def moveUp(self, gid):
    #    index = self.groupIds.index(gid)
    #    assert index > 0
    #    self.groupIds.insert(index-1, self.groupIds.pop(index))
    #def moveDown(self, gid):
    #    index = self.groupIds.index(gid)
    #    assert index < len(self.groupIds) - 1
    #    self.groupIds.insert(index+1, self.groupIds.pop(index))
    #def swap(self, gid1, gid2):
    #    #assert gid1 in self.groupIds and gid2 in self.groupIds
    #    i1 = self.groupIds.index(gid1)
    #    group1 = self.groupIds.pop(i1)
    #    i2 = self.groupIds.index(gid2)
    #    self.groupIds.insert(i2+1, group1)
    def loadConfig(self):
        self.clear()
        #eventIds = []
        if isfile(groupListFile):
            for gid in json.loads(open(groupListFile).read()):
                groupFile = join(groupsDir, '%s.json'%gid)
                if not isfile(groupFile):
                    log.error('error while loading group file %r: no such file'%groupFile)## FIXME
                    continue
                data = json.loads(open(groupFile).read())
                data['gid'] = gid ## FIXME
                group = eventGroupsClassDict[data['type']](gid)
                group.setData(data)
                self.append(group)
                ## here check that non of group.eventIds are in eventIds ## FIXME
                #eventIds += group.eventIds
        else:
            for cls in eventGroupsClassList:
                group = cls()## FIXME
                group.setData({'title': cls.desc})## FIXME
                group.saveConfig()
                self.append(group)
            ###
            #trash = EventTrash()## FIXME
            #group.saveConfig()
            #self.append(trash)
            ###
            self.saveConfig()
        ## here check for non-grouped event ids ## FIXME
    def saveConfig(self):
        jstr = dataToJson(self.groupIds)
        open(groupListFile, 'w').write(jstr)



class EventTrash(EventContainer):
    name = 'trash'
    desc = _('Trash')
    def __init__(self):
        EventContainer.__init__(self)
        self.title = _('Trash')
        self.icon = join(pixDir, 'trash.png')
    def deleteEvent(self, eid):
        if not isinstance(eid, int):
            raise TypeError("deleteEvent takes event ID that is integer")
        assert eid in self.eventIds
        try:
            shutil.rmtree(join(eventsDir, str(eid)))
        except:
            myRaise()
        else:
            self.eventIds.remove(eid)
    def empty(self):
        eventIds2 = self.eventIds[:]
        for eid in self.eventIds:
            try:
                shutil.rmtree(join(eventsDir, str(eid)))
            except:
                myRaise()
            else:
                eventIds2.remove(eid)
        self.eventIds = eventIds2
        self.saveConfig()
    def getData(self):
        return {
            'title': self.title,
            'icon': self.icon,
            'eventIds': self.eventIds,
        }
    def setData(self, data):
        self.title = data.get('title', _('Trash'))
        self.icon = data.get('icon', '')
        self.eventIds = data.get('eventIds', [])
    def saveConfig(self):
        jstr = self.getJson()
        open(trashFile, 'w').write(jstr)
    def loadConfig(self):
        if isfile(trashFile):
            jsonStr = open(trashFile).read()
            if jsonStr:
                self.setJson(jsonStr)## FIXME
        else:
            self.saveConfig()


class OccurrenceView:
    #name = ''## a GtkWidget will inherit a child of this class FIXME
    #desc = _('Occurrence View')
    #def __init__(self):
    #    self.updateData()
    def getJdRange(self):
        raise NotImplementedError
    def setJd(self, jd):
        raise NotImplementedError
    def updateData(self):
        raise NotImplementedError
    def updateDataByGroups(self):
        raise NotImplementedError


## current CustomDay widget (below month calendar) is something like DayOccurrenceView
## we should not use this class directly
## we use classes inside scal2.ui_gtk.event.occurrenceViews
class DayOccurrenceView(OccurrenceView):
    #name = 'day'## a GtkWidget will inherit this class FIXME
    #desc = _('Day Occurrence View')
    def __init__(self, jd):
        self.jd = jd
        self.updateData()
    getJdRange = lambda self: (self.jd, self.jd+1)
    def setJd(self, jd):
        if jd != self.jd:
            self.jd = jd
            self.updateData()
    def updateDataByGroups(self, groups):
        startJd = self.jd
        endJd = self.jd + 1
        self.data = []
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
                for url, fname in event.getFilesUrls():
                    text += '\n<a href="%s">%s</a>'%(url, fname)
                icon = event.icon
                #print '\nupdateData: checking event', event.summary
                ids = (group.gid, event.eid)
                if isinstance(occur, JdListOccurrence):
                    #print 'updateData: JdListOccurrence', occur.getDaysJdList()
                    for jd in occur.getDaysJdList():
                        if jd==self.jd:
                            self.data.append({
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
                            self.data.append({
                                'time':timeEncode((h1, min1, s1), True),
                                'text':text,
                                'icon':icon,
                                'ids': ids,
                            })
                        else:
                            (jd2, h2, min2, s2) = core.getJhmsFromEpoch(endEpoch)
                            if jd1==self.jd==jd2:
                                self.data.append({
                                    'time':hmsRangeToStr(h1, min1, s1, h2, min2, s2),
                                    'text':text,
                                    'icon':icon,
                                    'ids': ids,
                                })
                            elif jd1==self.jd and self.jd < jd2:
                                self.data.append({
                                    'time':hmsRangeToStr(h1, min1, s1, 24, 0, 0),
                                    'text':text,
                                    'icon':icon,
                                    'ids': ids,
                                })
                            elif jd1 < self.jd < jd2:
                                self.data.append({
                                    'time':'',
                                    'text':text,
                                    'icon':icon,
                                    'ids': ids,
                                })
                            elif jd1 < self.jd and self.jd==jd2:
                                self.data.append({
                                    'time':hmsRangeToStr(0, 0, 0, h2, min2, s2),
                                    'text':text,
                                    'icon':icon,
                                    'ids': ids,
                                })
                elif isinstance(occur, TimeListOccurrence):
                    #print 'updateData: TimeListOccurrence', occur.epochList
                    for epoch in occur.epochList:
                        (jd, hour, minute, sec) = core.getJhmsFromEpoch(epoch)
                        if jd == self.jd:
                            self.data.append({
                                'time':timeEncode((hour, minute, sec), True),
                                'text':text,
                                'icon':icon,
                                'ids': ids,
                            })
                else:
                    raise TypeError


class WeekOccurrenceView(OccurrenceView):
    #name = 'week'## a GtkWidget will inherit this class FIXME
    #desc = _('Week Occurrence View')
    def __init__(self, jd):
        self.absWeekNumber = core.getAbsWeekNumberFromJd(jd)
        #self.updateData()
    getJdRange = lambda self: core.getJdRangeOfAbsWeekNumber(self.absWeekNumber)
    def setJd(self, jd):
        absWeekNumber = core.getAbsWeekNumberFromJd(jd)
        if absWeekNumber != self.absWeekNumber:
            self.absWeekNumber = absWeekNumber
            self.updateData()
    def updateDataByGroups(self, groups):
        (startJd, endJd) = self.getJdRange()
        self.data = []
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
                ids = (group.gid, event.eid)
                if isinstance(occur, JdListOccurrence):
                    for jd in occur.getDaysJdList():
                        (absWeekNumber, weekDay) = core.getWeekDateFromJd(jd)
                        if absWeekNumber==self.absWeekNumber:
                            self.data.append({
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
                        (absWeekNumber, weekDay) = core.getWeekDateFromJd(jd1)
                        if absWeekNumber==self.absWeekNumber:
                            if jd1==jd2:
                                self.data.append({
                                    'weekDay':weekDay,
                                    'time':hmsRangeToStr(h1, min1, s1, h2, min2, s2),
                                    'text':text,
                                    'icon':icon,
                                    'ids': ids,
                                })
                            else:## FIXME
                                self.data.append({
                                    'weekDay':weekDay,
                                    'time':hmsRangeToStr(h1, min1, s1, 24, 0, 0),
                                    'text':text,
                                    'icon':icon,
                                    'ids': ids,
                                })
                                for jd in range(jd1+1, jd2):
                                    (absWeekNumber, weekDay) = core.getWeekDateFromJd(jd)
                                    if absWeekNumber==self.absWeekNumber:
                                        self.data.append({
                                            'weekDay':weekDay,
                                            'time':'',
                                            'text':text,
                                            'icon':icon,
                                            'ids': ids,
                                        })
                                    else:
                                        break
                                (absWeekNumber, weekDay) = core.getWeekDateFromJd(jd2)
                                if absWeekNumber==self.absWeekNumber:
                                    self.data.append({
                                        'weekDay':weekDay,
                                        'time':hmsRangeToStr(0, 0, 0, h2, min2, s2),
                                        'text':text,
                                        'icon':icon,
                                        'ids': ids,
                                    })
                elif isinstance(occur, TimeListOccurrence):
                    for epoch in occur.epochList:
                        (jd, hour, minute, sec) = core.getJhmsFromEpoch(epoch)
                        (absWeekNumber, weekDay) = core.getWeekDateFromJd(jd)
                        if absWeekNumber==self.absWeekNumber:
                            self.data.append({
                                'weekDay':weekDay,
                                'time':timeEncode((hour, minute, sec), True),
                                'text':text,
                                'icon':icon,
                                'ids': ids,
                            })
                else:
                    raise TypeError


class MonthOccurrenceView(OccurrenceView):
    #name = 'month'## a GtkWidget will inherit this class FIXME
    #desc = _('Month Occurrence View')
    def __init__(self, jd):
        (year, month, day) = jd_to(jd, core.primaryMode)## what mode? FIXME
        self.year = year
        self.month = month
        #self.updateData()
    getJdRange = lambda self: core.getJdRangeForMonth(self.year, self.month, core.primaryMode)
    def setJd(self, jd):
        (year, month, day) = jd_to(jd, core.primaryMode)
        if (year, month) != (self.year, self.month):
            self.year = year
            self.month = month
            self.updateData()
    def updateDataByGroups(self, groups):
        (startJd, endJd) = self.getJdRange()
        self.data = []
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
                ids = (group.gid, event.eid)
                if isinstance(occur, JdListOccurrence):
                    for jd in occur.getDaysJdList():
                        (year, month, day) = jd_to(jd, core.primaryMode)
                        if year==self.year and month==self.month:
                            self.data.append({
                                'day':day,
                                'time':'',
                                'text':text,
                                'icon':icon,
                                'ids': ids,
                            })
                elif isinstance(occur, TimeRangeListOccurrence):
                    for (startEpoch, endEpoch) in occur.getTimeRangeList():
                        (jd1, h1, min1, s1) = core.getJhmsFromEpoch(startEpoch)
                        (jd2, h2, min2, s2) = core.getJhmsFromEpoch(endEpoch)
                        (year, month, day) = jd_to(jd1, core.primaryMode)
                        if year==self.year and month==self.month:
                            if jd1==jd2:
                                self.data.append({
                                    'day':day,
                                    'time':hmsRangeToStr(h1, min1, s1, h2, min2, s2),
                                    'text':text,
                                    'icon':icon,
                                    'ids': ids,
                                })
                            else:## FIXME
                                self.data.append({
                                    'day':day,
                                    'time':hmsRangeToStr(h1, min1, s1, 24, 0, 0),
                                    'text':text,
                                    'icon':icon,
                                    'ids': ids,
                                })
                                for jd in range(jd1+1, jd2):
                                    (year, month, day) = jd_to(jd, core.primaryMode)
                                    if year==self.year and month==self.month:
                                        self.data.append({
                                            'day':day,
                                            'time':'',
                                            'text':text,
                                            'icon':icon,
                                            'ids': ids,
                                        })
                                    else:
                                        break
                                (year, month, day) = jd_to(jd2, core.primaryMode)
                                if year==self.year and month==self.month:
                                    self.data.append({
                                        'day':day,
                                        'time':hmsRangeToStr(0, 0, 0, h2, min2, s2),
                                        'text':text,
                                        'icon':icon,
                                        'ids': ids,
                                    })
                elif isinstance(occur, TimeListOccurrence):
                    for epoch in occur.epochList:
                        (jd, hour, minute, sec) = core.getJhmsFromEpoch(epoch)
                        (year, month, day) = jd_to(jd1, core.primaryMode)
                        if year==self.year and month==self.month:
                            self.data.append({
                                'day':day,
                                'time':timeEncode((hour, minute, sec), True),
                                'text':text,
                                'icon':icon,
                                'ids': ids,
                            })
                else:
                    raise TypeError

def loadEventTrash(groups=[]):
    trash = EventTrash()
    trash.loadConfig()
    ###
    groupedIds = trash.eventIds[:]
    for group in groups:
        groupedIds += group.eventIds
    nonGroupedIds = []
    for eid in listdir(eventsDir):
        try:
            eid = int(eid)
        except:
            continue
        if not eid in groupedIds:
            nonGroupedIds.append(eid)
    if nonGroupedIds:
        trash.eventIds += nonGroupedIds
        trash.saveConfig()
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
    stopDaemon()
    startDaemon()


########################################################################

eventsClassList = [TaskEvent, DailyNoteEvent, YearlyEvent, UniversityClassEvent, Event]
eventsClassDict = dict([(cls.name, cls) for cls in eventsClassList])
eventsClassByDesc = dict([(cls.desc, cls) for cls in eventsClassList])

eventsClassNameList = [cls.name for cls in eventsClassList]
#eventsClassNameDescList = [(cls.name, cls.desc) for cls in eventsClassList]
defaultEventTypeIndex = 0 ## FIXME

eventRulesClassList = [
    YearEventRule,
    MonthEventRule,
    DayOfMonthEventRule,
    WeekNumberModeEventRule,
    WeekDayEventRule,
    CycleDaysEventRule,
    DayTimeEventRule,
    StartEventRule,
    EndEventRule,
    DurationEventRule,
    CycleLenEventRule,
]
eventRulesClassDict = dict([(cls.name, cls) for cls in eventRulesClassList])

eventNotifiersClassList = [
    AlarmNotifier,
    FloatingMsgNotifier,
    WindowMsgNotifier,
]
eventNotifiersClassDict = dict([(cls.name, cls) for cls in eventNotifiersClassList])

eventGroupsClassList = [
    EventGroup,
    TaskList,
    NoteBook,
    UniversityTerm,
]
eventGroupsClassNameList = [cls.name for cls in eventGroupsClassList]
defaultGroupTypeIndex = 0 ## FIXME
eventGroupsClassDict = dict([(cls.name, cls) for cls in eventGroupsClassList])


#occurrenceViewClassList = [
#    MonthOccurrenceView,
#    WeekOccurrenceView,
#    DayOccurrenceView,
#]
#occurrenceViewClassDict = dict([(cls.name, cls) for cls in occurrenceViewClassList])


def testIntersection():
    import pprint
    pprint.pprint(intersectionOfTwoTimeRangeList(
        [(0,1.5), (3,5), (7,9)],
        [(1,3.5), (4,7.5), (8,10)]
    ))
    

def testJdRanges():
    import pprint
    pprint.pprint(JdListOccurrence([1, 3, 4, 5, 7, 9, 10, 11, 12, 13, 14, 18]).calcJdRanges())


if __name__=='__main__':
    #testIntersection()
    testJdRanges()


