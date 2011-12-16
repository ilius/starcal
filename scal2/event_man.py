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
from collections import OrderedDict

from paths import *

from scal2.utils import arange, ifloor, iceil, IteratorFromGen, findNearestIndex
from scal2.time_utils import *
from scal2.color_utils import hslToRgb

from scal2.locale_man import tr as _
from scal2.locale_man import getMonthName, textNumLocale
from scal2 import core
from scal2.core import myRaise, getEpochFromJd, getEpochFromJhms, log, to_jd, jd_to, getAbsWeekNumberFromJd

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
    def getStartEpoch(self):
        raise NotImplementedError
    def getEndEpoch(self):
        raise NotImplementedError
    

class JdListOccurrence(Occurrence):
    name = 'jdList'
    __repr__ = lambda self: 'JdListOccurrence(%r)'%list(self.jdSet)
    def __init__(self, jdList=None):
        Occurrence.__init__(self)
        if not jdList:
            jdList = []
        self.jdSet = set(jdList)
    __nonzero__ = lambda self: bool(self.jdSet)
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
    name = 'custom'## or 'rule' or '' FIXME
    desc = _('Custom Event Rule')## FIXME
    provide = ()
    need = ()
    conflict = ()
    sgroup = -1
    expand = False
    params = ()
    def __init__(self, parent):## parent can be an event or group
        self.parent = parent
    getMode = lambda self: self.parent.mode
    def getConfigLine(self):
        return self.name
    def setFromConfig(self, parts):
        pass
    def calcOccurrence(self, startEpoch, endEpoch, event):
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
    def __init__(self, parent):
        EventRule.__init__(self, parent)
        self.year = core.getSysDate(self.getMode())[0] ## FIXME
    def getData(self):
        return self.year
    def setData(self, year):
        self.year = year
    def calcOccurrence(self, startEpoch, endEpoch, event):## improve performance ## FIXME
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
    def __init__(self, parent):
        EventRule.__init__(self, parent)
        self.month = 1
    def getData(self):
        return self.month
    def setData(self, month):
        self.month = month
    def calcOccurrence(self, startEpoch, endEpoch, event):## improve performance ## FIXME
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
    def __init__(self, parent):
        EventRule.__init__(self, parent)
        self.day = 1
    def getData(self):
        return self.day
    def setData(self, day):
        self.day = day
    def calcOccurrence(self, startEpoch, endEpoch, event):## improve performance ## FIXME
        jdList = []
        for jd in core.getJdListFromEpochRange(startEpoch, endEpoch):
            if jd not in jdList and jd_to(jd, self.getMode())[2]==self.day:
                jdList.append(jd)
        return JdListOccurrence(jdList)
    getInfo = lambda self: self.desc + '(' + _(self.getMode()) + '): ' + _(self.day)



class WeekNumberModeEventRule(EventRule):
    name = 'weekNumMode'
    desc = _('Week Number')
    need = ('start',)## FIXME
    params = ('weekNumMode',)
    (EVERY_WEEK, ODD_WEEKS, EVEN_WEEKS) = range(3) ## remove EVERY_WEEK? FIXME
    weekNumModeNames = ('any', 'odd', 'even')## remove 'any'? FIXME
    def __init__(self, parent):
        EventRule.__init__(self, parent)
        self.weekNumMode = self.EVERY_WEEK
    def getData(self):
        return self.weekNumModeNames[self.weekNumMode]
    def setData(self, modeName):
        if not modeName in self.weekNumModeNames:
            raise BadEventFile('bad rule weekNumMode=%r, the value for weekNumMode must be one of %r'\
                %(modeName, self.weekNumModeNames))
        self.weekNumMode = self.weekNumModeNames.index(modeName)
    def calcOccurrence(self, startEpoch, endEpoch, event):## improve performance ## FIXME
        startAbsWeekNum = getAbsWeekNumberFromJd(event['start'].getJd()) - 1 ## 1st week ## FIXME
        jdListAll = core.getJdListFromEpochRange(startEpoch, endEpoch)
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

class WeekDayEventRule(EventRule):
    name = 'weekDay'
    desc = _('Day of Week')
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
    def __init__(self, parent):
        EventRule.__init__(self, parent)
        self.cycleDays = 7
    def getData(self):
        return self.cycleDays
    def setData(self, cycleDays):
        self.cycleDays = cycleDays
    def calcOccurrence(self, startEpoch, endEpoch, event):## improve performance ## FIXME
        startJd = max(event['start'].getJd(), core.getJdFromEpoch(startEpoch))
        endJd = core.getJdFromEpoch(endEpoch-0.01)+1
        return JdListOccurrence(range(startJd, endJd, self.cycleDays))
    getInfo = lambda self: _('Repeat: Every %s Days')%_(self.cycleDays)

class DayTimeEventRule(EventRule):## Moment Event
    name = 'dayTime'
    desc = _('Time in Day')
    provide = ('time',)
    conflict = ('cycleLen',)
    params = ('dayTime',)
    def __init__(self, parent):
        EventRule.__init__(self, parent)
        self.dayTime = time.localtime()[3:6]
    def getData(self):
        return timeEncode(self.dayTime)
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
            getEpochFromJd(startJd)+mySec,
            getEpochFromJd(endJd)+mySec+1,
            24*3600,
        )
        
    getInfo = lambda self: _('Time in Day') + ': ' + timeEncode(self.dayTime)


class DayTimeRangeEventRule(EventRule):
    name = 'dayTimeRange'
    desc = _('Day Time Range')
    conflict = ('dayTime',)
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
    getData = lambda self: (timeEncode(self.dayTimeStart), timeEncode(self.dayTimeEnd))
    setData = lambda self, data: self.setRange(timeDecode(data[0]), timeDecode(data[1]))
    def calcOccurrence(self, startEpoch, endEpoch, event):
        daySecStart = getSecondsFromHms(*self.dayTimeStart)
        daySecEnd = getSecondsFromHms(*self.dayTimeEnd)
        startDiv, startMod = divmod(startEpoch, 24*3600)
        endDiv, endMod = divmod(endEpoch, 24*3600)
        return TimeRangeListOccurrence(intersectionOfTwoTimeRangeList(
            [(i*24*3600+daySecStart, i*24*3600+daySecEnd) for i in range(startDiv, endDiv+1)],
            [(startEpoch, endEpoch)],
        ))


class DateAndTimeEventRule(EventRule):
    sgroup = 1
    params = ('date', 'time')
    def __init__(self, parent):
        EventRule.__init__(self, parent)
        self.date = core.getSysDate(self.getMode())
        self.time = time.localtime()[3:6]
    def getJd(self):
        (year, month, day) = self.date
        return to_jd(year, month, day, self.getMode())
    def getEpoch(self):
        return getEpochFromJhms(self.getJd(), *tuple(self.time))
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
    def calcOccurrence(self, startEpoch, endEpoch, event):
        myEpoch = self.getEpoch()
        if endEpoch <= myEpoch:
            return TimeRangeListOccurrence([])
        if startEpoch < myEpoch:
            startEpoch = myEpoch
        return TimeRangeListOccurrence([(startEpoch, endEpoch)])

class EndEventRule(DateAndTimeEventRule):
    name = 'end'
    desc = _('End')
    def calcOccurrence(self, startEpoch, endEpoch, event):
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

class CycleLenEventRule(EventRule):
    name = 'cycleLen'
    desc = _('Cycle Length (Days & Time)')
    provide = ('time',)
    need = ('start',)
    conflict = ('dayTime', 'cycleDays',)
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
    name = 'custom'## or 'notifier' or '' FIXME
    desc = _('Custom Event Notifier')## FIXME
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



class AlarmNotifier(EventNotifier):
    name = 'alarm'
    desc = _('Alarm')
    params = ('alarmSound', 'playerCmd')
    def __init__(self, event):
        EventNotifier.__init__(self, event)
        self.alarmSound = '' ## FIXME
        self.playerCmd = 'mplayer'


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


class RuleContainer:
    requiredRules = ()
    supportedRules = None
    def clearRules(self):
        self.rulesOd = OrderedDict()
    __iter__ = lambda self: self.rulesOd.itervalues()
    __getitem__ = lambda self, key: self.rulesOd.__getitem__(key)
    __setitem__ = lambda self, key, value: self.rulesOd.__setitem__(key, value)
    getRulesData = lambda self: [(rule.name, rule.getData()) for rule in self.rulesOd.values()]
    getRuleNames = lambda self: self.rulesOd.keys()
    addRule = lambda self, rule: self.rulesOd.__setitem__(rule.name, rule)
    addNewRule = lambda self, ruleType: self.addRule(eventRulesClassDict[ruleType](self))
    removeRule = lambda self, rule: self.rulesOd.__delitem__(rule.name)
    def setRulesData(self, rulesData):
        self.clearRules()
        for (ruleName, ruleData) in rulesData:
            rule = eventRulesClassDict[ruleName](self)
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



class Event(EventBaseClass, RuleContainer):
    name = 'custom'## or 'event' or '' FIXME
    desc = _('Custom Event')
    iconName = ''
    requiredNotifiers = ()
    @classmethod
    def getDefaultIcon(cls):
        return join(pixDir, 'event', cls.iconName+'.png') if cls.iconName else ''
    def __init__(self, eid=None):
        self.setId(eid)
        self.group = None
        self.mode = core.primaryMode
        self.icon = self.__class__.getDefaultIcon()
        self.summary = self.desc + ' (' + _(self.eid) + ')'
        self.description = ''
        #self.showInTimeLine = False ## FIXME
        self.files = []
        ######
        self.clearRules()
        self.notifiers = []
        self.notifyBefore = (0, 1) ## (value, unit) like DurationEventRule
        ## self.snoozeTime = (5, 60) ## (value, unit) like DurationEventRule ## FIXME
        self.addRequirements()
        self.setDefaults()
    getNotifyBeforeSec = lambda self: self.notifyBefore[0] * self.notifyBefore[1]
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
    __nonzero__ = lambda self: bool(self.rulesOd) ## FIXME
    def getInfo(self):
        lines = []
        rulesDict = self.rulesOd.copy()
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
    def addRequirements(self):
        RuleContainer.addRequirements(self)
        notifierNames = (notifier.name for notifier in self.notifiers)
        for name in self.requiredNotifiers:
            if not name in notifierNames:
                self.notifiers.append(eventNotifiersClassDict[name](self))
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
    def copyFrom(self, other):## FIXME
        self.mode = other.mode
        self.copyRulesFrom(other)
        self.notifiers = other.notifiers[:]## FIXME
        self.notifyBefore = other.notifyBefore[:]
        self.icon = other.icon
        self.summary = other.summary
        self.description = other.description
        #self.showInTimeLine = other.showInTimeLine
        #self.files = other.files[:]
        self.addRequirements()
    def getData(self):
        return {
            'type': self.name,
            'calType': core.modules[self.mode].name,
            'rules': self.getRulesData(),
            'notifiers': self.getNotifiersData(),
            'notifyBefore': durationEncode(*self.notifyBefore),
            'icon': self.icon,
            'summary': self.summary,
            'description': self.description,
        }
    def setData(self, data):
        if 'id' in data:
            self.setId(data['id'])
        if 'calType' in data:
            calType = data['calType']
            for (i, module) in enumerate(core.modules):
                if module.name == calType:
                    self.mode = i
                    break
            else:
                raise ValueError('Invalid calType: %r'%calType)
        self.setRulesData(data['rules'])
        self.notifiers = []
        if 'notifiers' in data:
            for (notifier_name, notifier_data) in data['notifiers']:
                notifier = eventNotifiersClassDict[notifier_name](self)
                notifier.setData(notifier_data)
                self.notifiers.append(notifier)
        if 'notifyBefore' in data:
            self.notifyBefore = durationDecode(data['notifyBefore'])
        for attr in ('icon', 'summary', 'description'):
            try:
                setattr(self, attr, data[attr])
            except KeyError:
                pass
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
    def __getitem__(self, key):
        try:
            return self.rulesOd[key]
        except KeyError:
            try:
                return self.group.rulesOd[key]
            except (KeyError, AttributeError):
                raise KeyError('Event %s has no rule %s'%(self.eid, key))
    getNotifiersData = lambda self: [(notifier.name, notifier.getData()) for notifier in self.notifiers]
    getNotifiersDict = lambda self: dict(self.getNotifiersData())
    def getRulesWithGroup(self):
        rulesOd = self.group.rulesOd.copy()
        rulesOd.update(self.rulesOd)
        return rulesOd.values()
    def calcOccurrenceForJdRange(self, startJd, endJd):## float jd ## cache Occurrences ## FIXME
        rules = self.getRulesWithGroup()
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

class YearlyEvent(Event):
    name = 'yearly'
    desc = _('Yearly Event')
    iconName = 'birthday'
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
    def copyFrom(self, other):
        Event.copyFrom(self, other)
        try:
            (y, m, d) = other['start'].date
        except KeyError:
            pass
        else:
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
    def setJd(self, jd):
        (y, m, d) = core.jd_to(jd, self.mode)
        self.setMonth(m)
        self.setDay(d)

class DailyNoteEvent(YearlyEvent):
    name = 'dailyNote'
    desc = _('Daily Note')
    iconName = 'note'
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
    def copyFrom(self, other):
        Event.copyFrom(self, other)
        try:
            self.setDate(*other['start'].date)
        except KeyError:
            pass
    def calcOccurrenceForJdRange(self, startJd, endJd):## float jd
        jd = self.getJd()
        return JdListOccurrence([jd] if startJd <= jd < endJd else [])
    def setJd(self, jd):
        (y, m, d) = core.jd_to(jd, self.mode)
        self.setYear(y)
        self.setMonth(m)
        self.setDay(d)

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
            tuple(time.localtime()[3:6]),
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
    def copyFrom(self, other):
        Event.copyFrom(self, other)
        myStartRule = self['start']
        ##
        date = list(myStartRule.date)
        try:
            date[0] = other['year'].year
        except KeyError:
            pass
        try:
            date[1] = other['month'].month
        except KeyError:
            pass
        try:
            date[2] = other['day'].day
        except KeyError:
            pass
        myStartRule.date = tuple(date)
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
    def setJd(self, jd):
        self['start'].date = core.jd_to(jd, self.mode)

#class UniversityCourseOwner(Event):## FIXME

class UniversityClassEvent(Event):
    name = 'universityClass'
    desc = _('Class')
    iconName = 'university'
    requiredRules  = ('weekNumMode', 'weekDay', 'dayTimeRange',)
    supportedRules = ('weekNumMode', 'weekDay', 'dayTimeRange',)
    def __init__(self, eid=None):
        ## assert group is not None ## FIXME
        Event.__init__(self, eid)
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
    getCourseName = lambda self: self.group.getCourseNameById(self.courseId)
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

class UniversityExamEvent(DailyNoteEvent):
    name = 'universityExam'
    desc = _('Exam')
    iconName = 'university'
    requiredRules  = ('year', 'month', 'day', 'dayTimeRange',)
    supportedRules = ('year', 'month', 'day', 'dayTimeRange',)
    def __init__(self, eid=None):
        ## assert group is not None ## FIXME
        DailyNoteEvent.__init__(self, eid)
        self.courseId = None ## FIXME
    def setDefaults(self):
        self['dayTimeRange'].setRange((9, 0), (11, 0))## FIXME
    def setDefaultsFromGroup(self, group):
        DailyNoteEvent.setDefaultsFromGroup(self, group)
        if group.name=='universityTerm':
            self.setDate(*group['end'].date)## FIXME
    getCourseName = lambda self: self.group.getCourseNameById(self.courseId)
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

class EventGroup(EventContainer, RuleContainer):
    name = 'group'
    desc = _('Event Group')
    acceptsEventTypes = ('yearly', 'dailyNote', 'task', 'custom')
    actions = []## [('Export to CSV', 'exportCsv')]
    eventActions = [] ## FIXME
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
        self.icon = ''
        #self.defaultNotifyBefore = (10, 60) ## FIXME
        if len(self.acceptsEventTypes)==1:
            self.defaultEventType = self.acceptsEventTypes[0]
            icon = eventsClassDict[self.acceptsEventTypes[0]].getDefaultIcon()
            if icon:
                self.icon = icon
        else:
            self.defaultEventType = 'custom'
        self.mode = core.primaryMode
        self.eventCacheSize = 0
        self.eventCache = {} ## from eid to event object
        self.clearRules()
        self.addRequirements()
        self.setDefaults()
    def setDefaults(self):
        '''
            sets default values that depends on group type
            not common parameters, like those are set in __init__
        '''
        pass
    __nonzero__ = lambda self: True ## FIXME
    def setId(self, gid=None):
        if gid is None or gid<0:
            gid = core.lastEventGroupId + 1 ## FIXME
            core.lastEventGroupId = gid
        elif gid > core.lastEventGroupId:
            core.lastEventGroupId = gid
        self.gid = gid
        self.groupFile = join(groupsDir, '%d.json'%self.gid)
    def copyFrom(self, other):
        self.enable = other.enable
        self.mode = other.mode
        self.copyRulesFrom(other)
        self.icon = other.icon
        self.color = other.color
        self.title = other.title
        #self.defaultEventType = other.defaultEventType ## FIXME
        self.eventCacheSize = other.eventCacheSize
        self.eventIds = other.eventIds ## FIXME
        self.addRequirements()
    def getData(self):
        return {
            'enable': self.enable,
            'type': self.name,
            'calType': core.modules[self.mode].name,
            'rules': self.getRulesData(),
            'icon': self.icon,
            'color': self.color,
            'title': self.title,
            #'defaultEventType': self.defaultEventType,
            'eventCacheSize': self.eventCacheSize,
            'eventIds': self.eventIds,
        }
    def setData(self, data):
        if 'id' in data:
            self.setId(data['id'])
        for attr in ('enable', 'title', 'color', 'icon', 'eventCacheSize', 'eventIds'):
            try:
                setattr(self, attr, data[attr])
            except KeyError:
                pass
        ####
        #if 'defaultEventType' in data:
        #    self.defaultEventType = data['defaultEventType']
        #    if not self.defaultEventType in eventsClassDict:
        #        raise ValueError('Invalid defaultEventType: %r'%self.defaultEventType)
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
        if 'rules' in data:
            self.setRulesData(data['rules'])
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
        event.group = self
        if len(self.eventCache) < self.eventCacheSize:
            self.eventCache[eid] = event
        return event
    def createEvent(self, eventType):
        assert eventType in self.acceptsEventTypes
        event = eventsClassDict[eventType]()
        event.group = self
        event.setDefaultsFromGroup(self)
        return event
    def copyEventWithType(self, event, eventType):## FIXME
        newEvent = self.createEvent(eventType)
        newEvent.setId(event.eid)
        newEvent.copyFrom(event)
        return newEvent
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
    def updateCache(self, event):
        if event.eid in self.eventCache:
            self.eventCache[event.eid] = event
    def copy(self):
        newGroup = EventBaseClass.copy(self)
        newGroup.excludeAll()
        return newGroup
    def deepCopy(self):
        newGroup = self.copy()
        for event in self:
            newEvent = event.copy()
            newEvent.saveConfig()
            newGroup.append(newEvent)
        return newGroup
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

class NoteBook(EventGroup):
    name = 'noteBook'
    desc = _('Note Book')
    acceptsEventTypes = ('dailyNote',)
    #actions = EventGroup.actions + []


class UniversityTerm(EventGroup):
    name = 'universityTerm'
    desc = _('University Term')
    requiredRules = ('start', 'end')
    supportedRules = ('start', 'end')
    acceptsEventTypes = ('universityClass', 'universityExam')
    #actions = EventGroup.actions + []
    actions = [('View Weekly Schedule', 'viewWeeklySchedule')]
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
                textNumLocale(simpleTimeEncode(tm0)) + ' ' + _('to') + ' ' + textNumLocale(simpleTimeEncode(tm1))
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
        startRule = self['start']
        endRule = self['end']
        startRule.time = (0, 0, 0)
        endRule.time = (24, 0, 0)## FIXME
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
                startRule.date = (year-1, 11, 15)
                self.classesEndDate = (year, 3, 20)
                endRule.date = (year, 4, 10)
            elif (4, 1) <= md < (10, 1):
                startRule.date = (year, 7, 1)
                self.classesEndDate = (year, 11, 1)
                endRule.date = (year, 11, 1)
            else:## md >= (10, 1)
                startRule.date = (year, 11, 15)
                self.classesEndDate = (year+1, 3, 1)
                endRule.date = (year+1, 3, 20)
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
    #byIndex = lambda 
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


def getDayOccurrenceData(curJd, groups):
    data = []
    for group in groups:
        if not group.enable:
            continue
        for event in group:
            if not event:
                continue
            occur = event.calcOccurrenceForJdRange(curJd, curJd+1)
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
                    if jd==curJd:
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
    return data


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
            ids = (group.gid, event.eid)
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
            ids = (group.gid, event.eid)
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


'''

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
        self.data = getDayOccurrenceData(self.jd, groups)

class WeekOccurrenceView(OccurrenceView):
    #name = 'week'## a GtkWidget will inherit this class FIXME
    #desc = _('Week Occurrence View')
    def __init__(self, jd):
        self.absWeekNumber = getAbsWeekNumberFromJd(jd)
        #self.updateData()
    getJdRange = lambda self: core.getJdRangeOfAbsWeekNumber(self.absWeekNumber)
    def setJd(self, jd):
        wnum = getAbsWeekNumberFromJd(jd)
        if wnum != self.absWeekNumber:
            self.absWeekNumber = wnum
            self.updateData()
    def updateDataByGroups(self, groups):
        self.data = getWeekOccurrenceData(absWeekNumber, groups)

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
        self.data = getMonthOccurrenceData(self.year, self.month, groups)
'''


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


eventsClassList = [TaskEvent, DailyNoteEvent, YearlyEvent, UniversityClassEvent, UniversityExamEvent, Event]
eventsClassDict = dict([(cls.name, cls) for cls in eventsClassList])
eventsClassByDesc = dict([(cls.desc, cls) for cls in eventsClassList])

eventsClassNameList = [cls.name for cls in eventsClassList]
#eventsClassNameDescList = [(cls.name, cls.desc) for cls in eventsClassList]
defaultEventTypeIndex = 0 ## FIXME
getEventDesc = lambda eventType: eventsClassDict[eventType].desc

eventRulesClassList = [
    YearEventRule,
    MonthEventRule,
    DayOfMonthEventRule,
    WeekNumberModeEventRule,
    WeekDayEventRule,
    CycleDaysEventRule,
    DayTimeEventRule,
    DayTimeRangeEventRule,
    StartEventRule,
    EndEventRule,
    DurationEventRule,
    CycleLenEventRule,
]
eventRulesClassDict = dict([(cls.name, cls) for cls in eventRulesClassList])
eventRulesClassByDesc = dict([(cls.desc, cls) for cls in eventRulesClassList])

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


