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

from math import ceil, sqrt
import random

from scal2 import core
from scal2.locale_man import tr as _
from scal2.core import myRaise, getMonthName, getJdFromEpoch, getEpochFromJd, jd_to, to_jd, getJhmsFromEpoch,\
                       getEpochFromDate

from scal2 import ui

#sunLightH = 10## FIXME
majorStepMin = 50 ## with label
minorStepMin = 5 ## with or without label
maxLabelWidth = 60 ## or the same majorStepMin
baseTickHeight = 1
baseTickWidth = 0.5
maxTickWidth = 20
maxTickHeightRatio = 0.3
currentTimeMarkerHeightRatio = 0.3
currentTimeMarkerWidth = 2
fontFamily = ui.getFont()[0]
baseFontSize = 8
labelYRatio = 1.1
bgColor = (50, 50, 50)
fgColor = (255, 255, 255)
currenTimeMarkerColor = (255, 100, 100)

boxRandomColorRange = (
    (0, 50),
    (0, 50),
    (0, 50),
    (255, 255),
)

scrollZoomStep = 1.2


unitSteps = (
    (3600, 12),
    (3600, 6),
    (3600, 3),
    (3600, 1),
    (60, 30),
    (60, 15),
    (60, 5),
    (60, 1),
    (1, 30),
    (1, 15),
    (1, 5),
    (1, 1),
)

minYearLenSec = 365*24*3600
avgMonthLen = 30*24*3600

enableAnimation = True

staticMoveStep = 20

movingUpdateTime = 10 ## milisecons
movingV0 = 30
movingAccel = 300
movingSurfaceForce = 600 ## px / (sec**2)
movingHandForce = movingSurfaceForce + movingAccel ## px / (sec**2)
movingMaxSpeed = (movingHandForce-movingSurfaceForce)*4 ## px / sec ## reach to maximum speed in 3 seconds
movingKeyTimeoutFirst = 0.5
movingKeyTimeout = 0.1 ## seconds ## continiouse keyPress delay is about 0.05 sec

minEventBoxWidthSec = 1 ## seconds


class Tick:
    def __init__(self, epoch, pos, unitSize, label='', truncateLabel=False):
        self.epoch = epoch
        self.pos = pos ## pixel position
        self.height = unitSize ** 0.5 * baseTickHeight
        self.width = min(unitSize ** 0.2 * baseTickWidth, maxTickWidth)
        self.fontSize = unitSize ** 0.1 * baseFontSize
        self.maxLabelWidth = min(unitSize*0.5, maxLabelWidth) ## FIXME
        self.label = label
        self.truncateLabel = truncateLabel

class Box:
    def __init__(self, t0, t1, y0, y1, text, color):
        self.t0 = t0
        self.t1 = t1
        self.y0 = y0
        self.y1 = y1
        self.text = text
        ###
        self.color = color
    def conflicts(self, other):
        return self.t0 < other.t0 < self.t1 or self.t0 < other.t1 < self.t1
    getWidth = lambda self: self.t1 - self.t0
    __cmp__ = lambda self, other: cmp(self.getWidth(), other.getWidth())

class Range:
    def __init__(self, start, end):
        self.start = start
        self.end = end
    __len__ = lambda self: self.end - self.start
    __cmp__ = lambda self, other: cmp(len(self), len(other))


def realRangeListsDiff(r1, r2):
    boundary = set()
    for (a, b) in r1+r2:
        boundary.add(a)
        boundary.add(b)
    boundaryList = sorted(boundary)
    ###
    ri1 = [] ## range1 indexes
    for (a, b) in r1:
        ri1 += range(boundaryList.index(a), boundaryList.index(b))
    ###
    ri2 = [] ## range2 indexes
    for (a, b) in r2:
        ri2 += range(boundaryList.index(a), boundaryList.index(b))
    ###
    ri3 = sorted(set(ri1).difference(set(ri2)))
    r3 = []
    pending = []
    for i in ri3:
        if pending:
            i2 = pending[-1] + 1
            if i2 < i:
                i1 = pending[0]
                r3.append((boundaryList[i1], boundaryList[i2]))
                pending = []
        pending.append(i)
    if pending:
        i1 = pending[0]
        i2 = pending[-1] + 1
        r3.append((boundaryList[i1], boundaryList[i2]))  
    return r3


def formatEpochTime(epoch):
    (jd, h, m, s) = getJhmsFromEpoch(epoch)
    if s==0:
        return '%s:%s'%(_(h), _(m))
    else:
        return '%s:%s:%s'%(_(h), _(m), _(s))

def getYearRangeTickValues(y0, y1, minStepYear):
    data = []
    numList = []
    #for n in (1000, 500, 100, 50, 10, 1):
    for n in (1000, 100, 10, 1):
        if n<minStepYear:
            break
        numList.append(n)
    for y in range(y0, y1):
        for n in numList:
            if y%n == 0:
                data.append((n, y))
                break
    return data

def setRandomColorsToEvents():
    for event in ui.events:
        event.color = tuple(random.uniform(ch[0], ch[1]) for ch in boxRandomColorRange)

def calcTimeLineData(timeStart, timeWidth, width):
    timeEnd = timeStart + timeWidth
    pixelPerSec = float(width)/timeWidth ## pixel/second
    minStep = minorStepMin/pixelPerSec ## second
    ticks = []
    tickEpochList = []
    #################
    jd0 = getJdFromEpoch(timeStart)
    jd1 = getJdFromEpoch(timeEnd)
    (y0, m0, d0) = jd_to(jd0, core.primaryMode)
    (y1, m1, d1) = jd_to(jd1, core.primaryMode)
    ############ Year
    minStepYear = int(minStep/minYearLenSec) ## year
    yearPixel = minYearLenSec*pixelPerSec ## pixel
    for (size, year) in getYearRangeTickValues(y0, y1+1, minStepYear):
        tmEpoch = getEpochFromDate(year, 1, 1, core.primaryMode)
        if tmEpoch in tickEpochList:
            continue
        unitSize = size*yearPixel
        ticks.append(Tick(
            tmEpoch,
            (tmEpoch-timeStart)*pixelPerSec,
            unitSize,
            _(year) if unitSize >= majorStepMin else '',
        ))
        tickEpochList.append(tmEpoch)
    ############ Month
    ym0 = y0*12 + m0-1
    ym1 = y1*12 + m1-1
    monthPixel = avgMonthLen*pixelPerSec ## pixel
    minMonthUnit = float(minStep)/avgMonthLen ## month
    #print 'minMonthUnit =', minMonthUnit
    if minMonthUnit <= 3:
        for ym in range(ym0, ym1+1):
            if ym%3==0:
                monthUnit = 3
            else:
                monthUnit = 1
            if monthUnit < minMonthUnit:
                continue
            (y, m) = divmod(ym, 12) ; m+=1
            tmEpoch = getEpochFromDate(y, m, 1, core.primaryMode)
            if tmEpoch in tickEpochList:
                continue
            unitSize = monthPixel*monthUnit
            ticks.append(Tick(
                tmEpoch,
                (tmEpoch-timeStart)*pixelPerSec,
                unitSize,
                getMonthName(core.primaryMode, m) if unitSize >= majorStepMin else '',
            ))
            tickEpochList.append(tmEpoch)
    ############ Day of Month
    hasMonthName = timeWidth < 5*24*3600
    dayPixel = 24*3600*pixelPerSec ## pixel
    minDayUnit = float(minStep)/(24*3600) ## day
    if minDayUnit <= 15:
        for jd in range(jd0, jd1+1):
            tmEpoch = getEpochFromJd(jd)
            if tmEpoch in tickEpochList:
                continue
            (year, month, day) = jd_to(jd, core.primaryMode)
            if day==15:
                dayUnit = 15
            #elif day in (5, 10, 20, 25):
            #    dayUnit = 5
            else:
                dayUnit = 1
            if dayUnit < minDayUnit:
                continue
            unitSize = dayPixel*dayUnit
            if unitSize < majorStepMin:
                label = ''
            elif hasMonthName:
                label = _(day) + ' ' + getMonthName(core.primaryMode, month)
            else:
                label = _(day)
            ticks.append(Tick(
                tmEpoch,
                (tmEpoch-timeStart)*pixelPerSec,
                unitSize,
                label,
            ))
            tickEpochList.append(tmEpoch)
    ############ Hour, Minute, Second
    for stepUnit, stepValue in unitSteps:
        stepSec = stepUnit*stepValue
        if stepSec < minStep:
            break
        unitSize = stepSec*pixelPerSec
        firstEpoch = int(ceil(timeStart/stepSec))*stepSec
        for tmEpoch in range(firstEpoch, int(ceil(timeEnd)), stepSec):
            if tmEpoch in tickEpochList:
                continue
            ticks.append(Tick(
                tmEpoch,
                (tmEpoch-timeStart)*pixelPerSec,
                unitSize,
                formatEpochTime(tmEpoch) if unitSize >= majorStepMin else '',
            ))
            tickEpochList.append(tmEpoch)
    ################################################
    boxes = []
    jd1 = int(ceil(jd1))
    for event in ui.events:
        #print 'event %s'%event.summary
        if not event.showInTimeLine:## FIXME
            continue
        if not event:
            continue
        occur = event.calcOccurrenceForJdRange(jd0, jd1)
        if not occur:
            continue
        #if isinstance(occur, TimeListOccurrence):
        #    occur.epochList
        for (t0, t1) in occur.getTimeRangeList():
            if t0 <= timeStart and timeEnd <= t1:
                continue
            tw = t1 - t0
            if tw < minEventBoxWidthSec:
                twd = (minEventBoxWidthSec - tw)/2.0
                t1 += twd
                t0 -= twd
            boxes.append(Box(t0, t1, 0, 1, event.summary, event.color))
    boxes.sort(reverse=True)
    placedBoxes = []
    for box in boxes:
        conflictBoxes = []
        conflictRanges = []
        minConflictH = 1
        for box1 in placedBoxes:
            if box1.conflict(box):
                conflictBoxes.append(box1)
                conflictRanges.append((box1.y0, box1.y1))
                minConflictH = min(minConflictH, box1.y1 - box1.y0)
        freeRanges = realRangeListsDiff([(0, 1)], conflictRanges)
        if freeRanges:
            bigestFree = max([Range(a, b) for (a, b) in freeRanges])
            bigestFreeH = len(bigestFree)## biggest free range height
            if bigestFreeH==1 or bigestFreeH/(1.0-bigestFreeH) >= minConflictH:
                box.y0 = bigestFree.start
                box.y1 = bigestFree.end
                continue
        ## now we should compress all conflicting boxes and place the new box on top of them
        h = 1 - 1.0/(minConflictH+1)
        box.y0 = 1 - h
        box.y1 = 1
        for box1 in conflictBoxes:
            box1.y0 *= (1-h)
            box1.y1 *= (1-h)
    return ticks, boxes


if __name__ == '__main__':
    r1 = [
        (0, 3),
        (4, 6),
        (8, 11)
    ]
    r2 = [
        (1, 5),
        (6, 7),
        (10, 12),
    ]
    print realRangeListsDiff(r1, r2)



