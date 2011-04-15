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

import time, json
from os.path import join, split, isdir, isfile
from os import listdir
from paths import *


#import numpy as np
from numpy import arange


from scal2.locale_man import tr as _
from scal2 import core


eventsDir = join(confDir, 'events')

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


hmsRangeToStr = lambda h1, m1, s1, h2, m2, s2:\
    timeEncode((h1, m1, s1), True) + ' - ' + timeEncode((h2, m2, s2), True)


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

def intersectionOfTwoTimeRangeList(timeRangeList1, timeRangeList2):
    frontierList = []
    for (start, end) in timeRangeList1:
        frontierList += [start, end]
    for (start, end) in timeRangeList2:
        frontierList += [start, end]
    frontierList.sort()
    partsNum = len(frontierList)-1
    partsContained = [[False, False] for i in range(partsNum)]
    for (start, end) in timeRangeList1:
        startIndex = frontierList.index(start)
        endIndex = frontierList.index(end)
        for i in range(startIndex, endIndex):
            partsContained[i][0] = True
    for (start, end) in timeRangeList2:
        startIndex = frontierList.index(start)
        endIndex = frontierList.index(end)
        for i in range(startIndex, endIndex):
            partsContained[i][1] = True
    resultTimeRangeList = []
    for i in range(partsNum):
        if partsContained[i][0] and partsContained[i][1]:
            resultTimeRangeList.append((frontierList[i], frontierList[i+1]))
    #makeCleanTimeRangeList(resultTimeRangeList)## not need when both timeRangeList are clean!
    return resultTimeRangeList


class Occurrence:
    def __init__(self):
        self.event = None
    def isNull(self):
        raise NotImplementedError
    def getDaysJdList(self):
        return []
    def intersection(self):
        raise NotImplementedError
    def getTimeRangeList(self):
        return []
    def containsMoment(self, epoch):
        return False
    def getJsonStr(self):
        return ''

class JdListOccurrence(Occurrence):
    name = 'jdList'
    __repr__ = lambda self: 'JdListOccurrence(%r)'%list(self.jdSet)
    def __init__(self, jdList=None):
        Occurrence.__init__(self)
        if not jdList:
            jdList = []
        self.jdSet = set(jdList)
    isNull = lambda self: bool(self.jdSet)
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


class TimeRangeListOccurrence(Occurrence):
    name = 'timeRange'
    __repr__ = lambda self: 'TimeRangeListOccurrence(%r)'%self.epochRangeList
    def __init__(self, epochRangeList=None):
        Occurrence.__init__(self)
        if not epochRangeList:
            epochRangeList = []
        self.epochRangeList = epochRangeList
    isNull = lambda self: bool(self.epochRangeList)
    def intersection(self, occur):
        if isinstance(occur, (JdListOccurrence, TimeRangeListOccurrence)):
            return TimeRangeListOccurrence(intersectionOfTwoTimeRangeList(self.getTimeRangeList(), occur.getTimeRangeList()))
        elif isinstance(occur, TimeListOccurrence):
            return occur.intersection(self)
        else:
            raise TypeError('bad type %s (%r)'%(occur.__class__.__name__, occur))
    def getDaysJdList(self):
        jdList = []
        for (startEpoch, endEpoch) in self.epochRangeList:
            for jd in core.getJdListFromEpochRange(startEpoch, endEpoch):
                if not jd in jdList:
                    jdList.append(jd)
        return jdList
    getTimeRangeList = lambda self: self.epochRangeList
    def containsMoment(self, epoch):
        for (startEpoch, endEpoch) in self.epochRangeList:
            if startEpoch <= epoch < endEpoch:
                return True
        return False
    def getData(self):
        return self.epochRangeList
    def setData(self, epochRangeList):
        self.epochRangeList = epochRangeList


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
    #isNull = lambda self: self.startEpoch == self.endEpoch
    isNull = lambda self: bool(self.epochList)
    def setRange(self, startEpoch, endEpoch, stepSeconds):
        self.startEpoch = startEpoch
        self.endEpoch = endEpoch
        self.stepSeconds = stepSeconds
        self.epochList = set(arange(startEpoch, endEpoch, stepSeconds))
    def intersection(self, occur):
        if isinstance(occur, (JdListOccurrence, TimeRangeListOccurrence)):
            return TimeRangeListOccurrence([(e, e+0.01) for e in self.getMomentsInsideTimeRangeList(occur.getTimeRangeList())])
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
        epochBetween = []
        for epoch in self.epochList:
            for (startEpoch, endEpoch) in timeRangeList:
                if startEpoch < epoch <= endEpoch:
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
            'stepSeconds': self.stepSeconds
        }
    

class EventRule:
    name = 'custom'## FIXME
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
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict=None):
        raise NotImplementedError
    def getData(self):
        return dict([(param, getattr(self, param)) for param in self.params])
    def setData(self, data):
        if isinstance(data, dict):
            for (key, value) in data.items():
                if key in self.params:
                    setattr(self, key, value)


class YearEventRule(EventRule):
    name = 'year'
    desc = _('Year')
    def __init__(self, event):
        EventRule.__init__(self, event)
        self.year = core.getSysDate(self.getMode())[0] ## FIXME
    def getData(self):
        return self.year
    def setData(self, year):
        self.year = year
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict=None):## improve performance ## FIXME
        jdList = []
        for jd in core.getJdListFromEpochRange(startEpoch, endEpoch):
            if jd not in jdList and core.jd_to(jd, self.getMode())[0]==self.year:
                jdList.append(jd)
        return JdListOccurrence(jdList)





class MonthEventRule(EventRule):
    name = 'month'
    desc = _('Month')
    def __init__(self, event):
        EventRule.__init__(self, event)
        self.month = 1
    def getData(self):
        return self.month
    def setData(self, month):
        self.month = month
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict=None):## improve performance ## FIXME
        for jd in core.getJdListFromEpochRange(startEpoch, endEpoch):
            if jd not in jdList and core.jd_to(jd, self.getMode())[1]==self.year:
                jdList.append(jd)
        return JdListOccurrence(jdList)



class DayOfMonthEventRule(EventRule):
    name = 'day'
    desc = _('Day of Month')
    def __init__(self, event):
        EventRule.__init__(self, event)
        self.day = 1
    def getData(self):
        return self.day
    def setData(self, day):
        self.day = day
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict=None):## improve performance ## FIXME
        jdList = []
        for jd in core.getJdListFromEpochRange(startEpoch, endEpoch):
            if jd not in jdList and core.jd_to(jd, self.getMode())[2]==self.year:
                jdList.append(jd)
        return JdListOccurrence(jdList)




class WeekNumberModeEventRule(EventRule):
    name = 'weekNumMode'
    desc = _('Week Number')
    EVERY_WEEK = 0
    ODD_WEEKS = 1
    EVEN_WEEKS = 2
    weekNumModeNames = ('any', 'odd', 'even')
    def __init__(self, event):
        EventRule.__init__(self, event)
        self.weekNumMode = 0
    def getData(self):
        return self.weekNumModeNames[self.weekNumMode]
    def setData(self, modeName):
        if not modeName in self.weekNumModeNames:
            raise BadEventFile('bad rule weekNumMode=%r, the value for weekNumMode must be one of %r'\
                %(modeName, self.weekNumModeNames))
        self.weekNumMode = self.weekNumModeNames.index(modeName)
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict):## improve performance ## FIXME
        (y, m, d) = rulesDict['start'].date ## ruleStartDate
        startAbsWeekNum = core.getAbsWeekNumberFromJd(core.to_jd(y, m, d, self.getMode())) - 1 ## 1st week ## FIXME
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



class WeekDayEventRule(EventRule):
    name = 'weekDay'
    desc = _('Day of Week')
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
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict=None):## improve performance ## FIXME
        jdList = []
        for jd in core.getJdListFromEpochRange(startEpoch, endEpoch):
            if core.jwday(jd) in self.weekDayList and not jd in jdList:
                jdList.append(jd)
        return JdListOccurrence(jdList)


class CycleDaysEventRule(EventRule):
    name = 'cycleDays'
    desc = _('Cycle Days Number')
    need = ('start',)
    conflict = ('dayTime', 'cycleLen')
    def __init__(self, event):
        EventRule.__init__(self, event)
        self.cycleDays = 7
    def getData(self):
        return self.cycleDays
    def setData(self, cycleDays):
        self.cycleDays = cycleDays
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict):## improve performance ## FIXME
        (year, month, day) = rulesDict['start'].date
        startJd = max(core.to_jd(year, month, day, self.getMode()),
                      core.getJdFromEpoch(startEpoch))
        endJd = core.getJdFromEpoch(endEpoch-0.01)+1
        if rulesDict.has_key('end'):
            (year, month, day) = rulesDict['end'].date
            endJd = min(endJd, core.to_jd(year, month, day, self.getMode())+1) ## +1 FIXME
        return JdListOccurrence(range(startJd, endJd, self.cycleDays))



class DayTimeEventRule(EventRule):## Moment Event
    name = 'dayTime'
    desc = _('Time in Day')
    provide = ('time',)
    conflict = ('cycleLen',)
    def __init__(self, event):
        EventRule.__init__(self, event)
        self.dayTime = time.localtime()[3:6]
    def getData(self):
        return timeEncode(self.dayTime)
    def setData(self, data):
        self.dayTime = timeDecode(data)
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict=None):
        mySec = core.getSecondsFromHms(*self.dayTime)
        (startJd, startExtraSec) = core.getJdAndSecondsFromEpoch(startEpoch)
        (endJd, endExtraSec) = core.getJdAndSecondsFromEpoch(endEpoch)
        if startExtraSec > mySec:
            startJd += 1
        if endExtraSec < mySec:
            endJd -= 1
        return TimeListOccurrence(core.getEpochFromJd(startJd),
                                  core.getEpochFromJd(endJd)+1,
                                  24*3600)



class DateAndTimeEventRule(EventRule):
    sgroup = 1
    def __init__(self, event):
        EventRule.__init__(self, event)
        self.date = core.getSysDate(self.getMode())
        self.time = time.localtime()[3:6]
    def getEpoch(self):
        (year, month, day) = self.date
        return core.getEpochFromJhms(core.to_jd(year, month, day, self.getMode()), *tuple(self.time))
    def getData(self):
        return {
            'date': dateEncode(self.date),
            'time': timeEncode(self.time)
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

class StartEventRule(DateAndTimeEventRule):
    name = 'start'
    desc = _('Start')
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict=None):
        myEpoch = self.getEpoch()
        if endEpoch <= myEpoch:
            return []
        if startEpoch < myEpoch:
            startEpoch = myEpoch
        return TimeRangeListOccurrence([(startEpoch, endEpoch)])


class EndEventRule(DateAndTimeEventRule):
    name = 'end'
    desc = _('End')
    def calcOccurrence(self, startEpoch, endEpoch, rulesDict=None):
        myEpoch = self.getEpoch()
        if startEpoch >= myEpoch:
            return TimeRangeListOccurrence([])
        if endEpoch > myEpoch:
            endEpoch = myEpoch
        return TimeRangeListOccurrence([(startEpoch, endEpoch)])



class CycleLenEventRule(EventRule):
    name = 'cycleLen'
    desc = _('Cycle Length (Days & Time)')
    provide = ('time',)
    need = ('start',)
    conflict = ('dayTime', 'cycleDays')
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
        cycleSec = self.cycleDays*24*3600 + core.getSecondsFromHms(*self.cycleExtraTime)
        return TimeListOccurrence(startEpoch, endEpoch, cycleSec)




class EventNotifier:
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
        if isinstance(data, dict):
            for (key, value) in data.items():
                if key in self.params:
                    setattr(self, key, value)
    getCompactJson = lambda self: json.dumps(self.getData(), separators=(',', ':'))


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


    

"""
class ShowInMCalEventRule(EventRule):## FIXME
    name = 'show_cal'
    desc = _('Show in Calendar')
"""

class Event:
    name = 'custom'
    desc = _('Custom Event')
    requiredRules = ()
    requiredNotifiers = ()
    def __init__(self, eid=None):
        self.setEid(eid)
        self.enable = True
        self.mode = core.primaryMode
        self.icon = '' ## to show in calendar
        self.summary = ''
        self.description = ''
        self.tags = []
        self.showInTimeLine = False
        ######
        self.rules = []
        self.notifiers = []
        self.checkRequirements()
    def checkRequirements(self):
        ruleNames = (rule.name for rule in self.rules)
        for name in self.requiredRules:
            if not name in ruleNames:
                self.rules.append(eventRulesClassDict[name](self))
        notifierNames = (notifier.name for notifier in self.notifiers)
        for name in self.requiredNotifiers:
            if not name in notifierNames:
                self.notifiers.append(eventNotifiersClassDict[name](self))
    def copyFrom(self, event):
        self.enable = event.enable
        self.mode = event.mode
        self.icon = event.icon
        self.summary = event.summary
        self.description = event.description
        self.tags = event.tags[:]
        self.showInTimeLine = event.showInTimeLine
        ######
        self.rules = event.rules[:]## FIXME
        self.notifiers = event.notifiers[:]## FIXME
        self.checkRequirements()
    def setEid(self, eid=None):
        if eid is None or eid<0:
            eid = core.lastEventId + 1 ## FIXME
            core.lastEventId += 1
        elif eid > core.lastEventId:
            core.lastEventId = eid
        self.eid = eid
        self.eventDir = join(eventsDir, str(self.eid))
        self.eventFile = join(self.eventDir, 'event.json')
        self.occurrenceFile = join(self.eventDir, 'occurrence')## file or directory? FIXME
    getText = lambda self: self.summary if self.summary else self.description
    def getData(self):
        return {
            'id': self.eid,
            'enable': self.enable,
            'type': self.name,
            'calType': core.modules[self.mode].name,
            'rules': self.getRulesData(),
            'notifiers': self.getNotifiersData(),
            'icon': self.icon,
            'summary': self.summary,
            'description': self.description,
            'tags': self.tags,
        }
    def setData(self, data):
        self.setEid(data['id'])
        calType = data['calType']
        for (i, module) in enumerate(core.modules):
            if module.name == calType:
                self.mode = i
                break
        else:
            raise ValueError('Invalid calType: %r'%calType)
        self.rules = []
        for (rule_name, rule_data) in data['rules']:
            rule = eventRulesClassDict[rule_name](self)
            rule.setData(rule_data)
            self.rules.append(rule)
        self.notifiers = []
        for (notifier_name, notifier_data) in data['notifiers']:
            notifier = eventNotifiersClassDict[notifier_name](self)
            notifier.setData(notifier_data)
            self.notifiers.append(notifier)
        try:
            self.enable = data['enable']
        except KeyError:
            self.enable = True
        for attr in ('icon', 'summary', 'description', 'tags'):
            try:
                setattr(self, attr, data[attr])
            except KeyError:
                setattr(self, attr, '')
    def saveConfig(self):
        if not isdir(self.eventDir):
            os.makedirs(self.eventDir)
        open(self.eventFile, 'w').write(json.dumps(self.getData(), sort_keys=True, indent=4))
    def loadConfig(self):## skipRules arg for use in ui_gtk/event_notify.py ## FIXME
        if not isdir(self.eventDir):
            raise IOError('event dir %r is not a directory'%self.eventDir)
        if not isfile(self.eventFile):
            raise IOError('event file %r is not a directory'%self.eventFile)
        jsonStr = open(self.eventFile).read()
        if jsonStr:
            self.setData(json.loads(jsonStr))## FIXME
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
                        _(rulesDict[conflictName].desc)
                    ))
            for needName in rule.need:
                if not needName in provideList:
                    ## find which rule(s) provide(s) needName ## FIXME
                    return (False, '"%s" %s "%s"'%(
                        _(rule.desc),
                        _('needs'),
                        _(needName) #_(rulesDict[needName].desc)
                    ))
        return (True, '')
    getRulesData = lambda self: [(rule.name, rule.getData()) for rule in self.rules]
    getRulesDict = lambda self: dict([(rule.name, rule) for rule in self.rules])
    getNotifiersData = lambda self: [(notifier.name, notifier.getData()) for notifier in self.notifiers]
    getNotifiersDict = lambda self: dict(self.getNotifiersData())
    def calcOccurrenceForJdRange(self, startJd, endJd):## cache Occurrences ## FIXME
        if not self.rules:
            return []
        startEpoch = core.getEpochFromJd(startJd)
        endEpoch = core.getEpochFromJd(endJd)
        rulesDict = self.getRulesDict()
        occur = self.rules[0].calcOccurrence(startEpoch, endEpoch, rulesDict)
        for rule in self.rules[1:]:
            occur = occur.intersection(rule.calcOccurrence(startEpoch, endEpoch, rulesDict))
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
    desc = _('Yearly Event (Anniversary)')
    requiredRules = ('year', 'month')
    def setYear(self, year):
        self.getRulesDict()['year'].year = year
    def setMonth(self, month):
        self.getRulesDict()['month'].month = month
    def setIcon(self, icon):
        self.icon = icon
    def getYear(self):
        return self.getRulesDict()['year'].year
    def getMonth(self):
        return self.getRulesDict()['month'].month
    def getIcon(self):
        return self.icon

class DailyNoteEvent(YearlyEvent):
    name = 'dailyNote'
    desc = _('Daily Note')
    requiredRules = ('year', 'month', 'day')
    def setDay(self, day):
        self.getRulesDict()['day'].day = day
    def getDay(self):
        return self.getRulesDict()['day'].day

class TaskEvent(DailyNoteEvent):
    ## Y/m/d H:M for H:M           ==> start, end
    ## Y/m/d H:M until Y/m/d H:M   ==> start, end
    ## Y/m/d H:M none              ==> year, month, day, dayTime
    ## notifierName = alarm
    ## [x] showInTimeLine
    name = 'task'
    desc = _('Task')
    requiredRules = ('year', 'month', 'day', 'dayTime')
    def setTime(self, dayTime):
        self.getRulesDict()['dayTime'].dayTime = dayTime
    def getTime(self, dayTime):
        return self.getRulesDict()['dayTime'].dayTime



class UniversityClassEvent(Event):## FIXME
    ## start, end, weekDay, weekNumberMode, dayTime --- notifierName='alarm' --- showInTimeLine
    name = 'universityClass'
    desc = _('University Class')
    requiredRules = ()

## class UniversityTerm:## FIXME




'''
        if isinstance(occur, JdListOccurrence):
            return JdListOccurrence(self.jdSet.intersection(occur.jdSet))
        elif isinstance(occur, TimeRangeListOccurrence):
            return TimeRangeListOccurrence(intersectionOfTwoTimeRangeList(self.getTimeRangeList(), occur.getTimeRangeList()))
        elif isinstance(occur, TimeListOccurrence):
            return occur.intersection(self)
        else:
            raise TypeError
'''


class OccurrenceView:
    def __init__(self):
        self.updateData()
    def getJdRange(self):
        raise NotImplementedError
    def setJd(self, jd):
        raise NotImplementedError
    def updateData(self):
        raise NotImplementedError

## current AddCustomDay is something like DayOccurrenceView

class MonthOccurrenceView(OccurrenceView):
    def __init__(self, jd):
        (year, month, day) = core.jd_to(jd, core.primaryMode)
        self.year = year
        self.month = month
        OccurrenceView.__init__(self)
    getJdRange = lambda self: core.getJdRangeForMonth(self.year, self.month, core.primaryMode)
    def setJd(self, jd):
        (year, month, day) = core.jd_to(jd, core.primaryMode)
        if (year, month) != (self.year, self.month):
            self.year = year
            self.month = month
            self.updateData()
    def updateData(self):
        (startJd, endJd) = self.getJdRange()
        self.data = []
        for event in ui.events:
            occur = event.calcOccurrenceForJdRange(startJd, endJd)
            text = event.getText()
            icon = event.icon
            if isinstance(occur, JdListOccurrence):
                for jd in occur.getDaysJdList():
                    (year, month, day) = core.jd_to(jd, core.primaryMode)
                    if year==self.year and month==self.month:
                        self.data.append({'day':day, 'time':'', 'text':text, 'icon':icon})
            elif isinstance(occur, TimeRangeListOccurrence):
                for (startEpoch, endEpoch) in occur.getTimeRangeList():
                    (jd1, h1, min1, s1) = core.getJhmsFromEpoch(startEpoch)
                    (jd2, h2, min2, s2) = core.getJhmsFromEpoch(endEpoch)
                    (year, month, day) = core.jd_to(jd1, core.primaryMode)
                    if year==self.year and month==self.month:
                        if jd1==jd2:
                            self.data.append({
                                'day':day,
                                'time':hmsRangeToStr(h1, min1, s1, h2, min2, s2),
                                'text':text,
                                'icon':icon
                            })
                        else:## FIXME
                            self.data.append({
                                'day':day,
                                'time':hmsRangeToStr(h1, min1, s1, 24, 0, 0),
                                'text':text,
                                'icon':icon
                            })
                            for jd in range(jd1+1, jd2):
                                (year, month, day) = core.jd_to(jd, core.primaryMode)
                                if year==self.year and month==self.month:
                                    self.data.append({
                                        'day':day,
                                        'time':'',
                                        'text':text,
                                        'icon':icon
                                    })
                                else:
                                    break
                            (year, month, day) = core.jd_to(jd2, core.primaryMode)
                            if year==self.year and month==self.month:
                                self.data.append({
                                    'day':day,
                                    'time':hmsRangeToStr(0, 0, 0, h2, min2, s2),
                                    'text':text,
                                    'icon':icon
                                })
            elif isinstance(occur, TimeListOccurrence):
                for epoch in occur.epochList:
                    (jd, hour, minute, sec) = core.getJhmsFromEpoch(epoch)
                    (year, month, day) = core.jd_to(jd1, core.primaryMode)
                    if year==self.year and month==self.month:
                        self.data.append({
                            'day':day,
                            'time':timeEncode((hour, minute, sec), True),
                            'text':text,
                            'icon':icon
                        })
            else:
                raise TypeError
            

class WeekOccurrenceView(OccurrenceView):
    def __init__(self, jd):
        self.absWeekNumber = core.getAbsWeekNumberFromJd(jd)
        OccurrenceView.__init__(self)
    getJdRange = lambda self: core.getJdRangeOfAbsWeekNumber(self.absWeekNumber)
    def setJd(self, jd):
        absWeekNumber = core.getAbsWeekNumberFromJd(jd)
        if absWeekNumber != self.absWeekNumber:
            self.absWeekNumber = absWeekNumber
            self.updateData()
    def updateData(self):
        (startJd, endJd) = self.getJdRange()
        self.data = []
        for event in ui.events:
            occur = event.calcOccurrenceForJdRange(startJd, endJd)
            text = event.getText()
            icon = event.icon
            if isinstance(occur, JdListOccurrence):
                for jd in occur.getDaysJdList():
                    (absWeekNumber, weekDay) = core.getWeekDateFromJd(jd)
                    if absWeekNumber==self.absWeekNumber:
                        self.data.append({'weekDay':weekDay, 'time':'', 'text':text, 'icon':icon})
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
                                'icon':icon
                            })
                        else:## FIXME
                            self.data.append({
                                'weekDay':weekDay,
                                'time':hmsRangeToStr(h1, min1, s1, 24, 0, 0),
                                'text':text,
                                'icon':icon
                            })
                            for jd in range(jd1+1, jd2):
                                (absWeekNumber, weekDay) = core.getWeekDateFromJd(jd)
                                if absWeekNumber==self.absWeekNumber:
                                    self.data.append({
                                        'weekDay':weekDay,
                                        'time':'',
                                        'text':text,
                                        'icon':icon
                                    })
                                else:
                                    break
                            (absWeekNumber, weekDay) = core.getWeekDateFromJd(jd2)
                            if absWeekNumber==self.absWeekNumber:
                                self.data.append({
                                    'weekDay':weekDay,
                                    'time':hmsRangeToStr(0, 0, 0, h2, min2, s2),
                                    'text':text,
                                    'icon':icon
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
                            'icon':icon
                        })
            else:
                raise TypeError




class DayOccurrenceView:
    def __init__(self, jd):
        self.jd = jd
        OccurrenceView.__init__(self)
    getJdRange = lambda self: core.getJdRangeForMonth(self.year, self.month, core.primaryMode)
    def setJd(self, jd):
        if jd != self.jd:
            self.jd = jd
            self.updateData()
    def updateData(self):
        startJd = self.jd
        endJd = self.jd + 1
        self.data = []
        ## FIXME
        for event in ui.events:
            occur = event.calcOccurrenceForJdRange(startJd, endJd)
            text = event.getText()
            icon = event.icon
            if isinstance(occur, JdListOccurrence):
                for jd in occur.getDaysJdList():
                    if jd==self.jd:
                        self.data.append({'time':'', 'text':text, 'icon':icon})
            elif isinstance(occur, TimeRangeListOccurrence):
                for (startEpoch, endEpoch) in occur.getTimeRangeList():
                    (jd1, h1, min1, s1) = core.getJhmsFromEpoch(startEpoch)
                    (jd2, h2, min2, s2) = core.getJhmsFromEpoch(endEpoch)
                    if jd1==self.jd==jd2:
                        self.data.append({
                            'time':hmsRangeToStr(h1, min1, s1, h2, min2, s2),
                            'text':text,
                            'icon':icon
                        })
                    elif jd1==self.jd and self.jd < jd2:
                        self.data.append({
                            'time':hmsRangeToStr(h1, min1, s1, 24, 0, 0),
                            'text':text,
                            'icon':icon
                        })
                    elif jd1 < self.jd < jd2:
                        self.data.append({
                            'time':'',
                            'text':text,
                            'icon':icon
                        })
                    elif jd1 < self.jd and self.jd==jd2:
                        self.data.append({
                            'time':hmsRangeToStr(0, 0, 0, h2, min2, s2),
                            'text':text,
                            'icon':icon
                        })
            elif isinstance(occur, TimeListOccurrence):
                for epoch in occur.epochList:
                    (jd, hour, minute, sec) = core.getJhmsFromEpoch(epoch)
                    if jd == self.jd:
                        self.data.append({
                            'time':timeEncode((hour, minute, sec), True),
                            'text':text,
                            'icon':icon
                        })
            else:
                raise TypeError

def loadEvents():
    events = []
    for eid_s in listdir(eventsDir):
        try:
            eid = int(eid_s)
        except ValueError:
            continue
        event = Event(eid)
        try:
            event.loadConfig()
        except:
            myRaise()
            del event
            continue
        events.append(event)
    return events

########################################################################

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
    CycleLenEventRule
]
eventRulesClassDict = dict([(cls.name, cls) for cls in eventRulesClassList])

eventNotifiersClassList = [
    AlarmNotifier,
    FloatingMsgNotifier,
    WindowMsgNotifier
]
eventNotifiersClassDict = dict([(cls.name, cls) for cls in eventNotifiersClassList])

eventsClassList = [Event, YearlyEvent, DailyNoteEvent, TaskEvent]## UniversityClassEvent
eventsClassDict = dict([(cls.name, cls) for cls in eventsClassList])
defaultEventTypeIndex = 3 ## DailyNoteEvent



def testIntersection():
    import pprint
    pprint.pprint(intersectionOfTwoTimeRangeList(
        [(0,1.5), (3,5), (7,9)],
        [(1,3.5), (4,7.5), (8,10)]
    ))

def testEventDialog():
    pass


if __name__=='__main__':
    testIntersection()


