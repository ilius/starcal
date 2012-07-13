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

from math import sqrt, floor, ceil, log10
#import random

from scal2.time_utils import overlaps
from scal2 import core
from scal2.locale_man import tr as _
from scal2.locale_man import rtl, numEncode, textNumEncode, LRM

from scal2.core import myRaise, getMonthName, getJdFromEpoch, getFloatJdFromEpoch, getEpochFromJd, jd_to, to_jd, \
                       getJhmsFromEpoch, getEpochFromDate, jwday

from scal2.color_utils import hslToRgb
from scal2.utils import ifloor, iceil
from scal2 import ui
from scal2.ui import getHolidaysJdList

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
bgColor = (40, 40, 40)
fgColor = (255, 255, 255)
currenTimeMarkerColor = (255, 100, 100)

showWeekStart = True
weekStartTickColor = (0, 200, 0)
showWeekStartMinDays = 1
showWeekStartMaxDays = 60

changeHolidayBg = True
holidayBgBolor = (60, 35, 35)
changeHolidayBgMinDays = 1
changeHolidayBgMaxDays = 60

boxLineWidth = 2
boxInnerAlpha = 0.1

boxMoveBorder = 10
boxMoveLineW = 0.5

movableEventTypes = ('task',)

#boxColorSaturation = 1.0
#boxColorLightness = 0.3 ## for random colors


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

skipEventPixelLimit = 0.1 ## pixels

truncateTickLabel = False

rotateBoxLabel = -1
## 0: no rotation
## 1: 90 deg CCW (if needed)
## -1: 90 deg CW (if needed)


class Tick:
    def __init__(self, epoch, pos, unitSize, label, color=None):
        self.epoch = epoch
        self.pos = pos ## pixel position
        self.height = unitSize ** 0.5 * baseTickHeight
        self.width = min(unitSize ** 0.2 * baseTickWidth, maxTickWidth)
        self.fontSize = unitSize ** 0.1 * baseFontSize
        self.maxLabelWidth = min(unitSize*0.5, maxLabelWidth) ## FIXME
        self.label = label
        if color is None:
            color = fgColor
        self.color = color

class Box:
    def __init__(self, t0, t1, odt, u0, u1, text, color, ids, order):
        self.t0 = t0
        self.t1 = t1
        self.odt = odt ## original delta t
        #if t1-t0 != odt:
        #    print 'Box, dt=%s, odt=%s'%(t1-t0, odt)
        self.u0 = u0
        self.u1 = u1
        ####
        self.x = None
        self.w = None
        self.y = None
        self.h = None
        ####
        self.text = text
        self.color = color
        self.ids = ids ## (groupId, eventId)
        self.order = order ## (groupIndex, eventIndex)
        self.tConflictBefore = []
        self.lineW = boxLineWidth
        self.hasBorder = False
    tOverlaps = lambda self, other: overlaps(self.t0, self.t1, other.t0, other.t1)
    yOverlaps = lambda self, other: overlaps(self.u0, self.u1, other.u0, other.u1)
    dt = lambda self: self.t1 - self.t0
    du = lambda self: self.u1 - self.u0
    def __cmp__(self, other):## FIXME
        c = -cmp(self.odt, other.odt)
        if c != 0: return c
        return cmp(self.order, other.order)
    def setPixelValues(self, timeStart, pixelPerSec, beforeBoxH, maxBoxH):
        self.x = (self.t0-timeStart)*pixelPerSec
        self.w = (self.t1 - self.t0)*pixelPerSec
        self.y = beforeBoxH + maxBoxH * self.u0
        self.h = maxBoxH * (self.u1 - self.u0)
    contains = lambda self, px, py: 0 <= px-self.x < self.w and 0 <= py-self.y < self.h
        

def yResizeBox(box1, rat):
    box1.u0 *= rat
    box1.u1 *= rat
    for box2 in box1.tConflictBefore:
        if box1.yOverlaps(box2):
            yResizeBox(box2, rat)

class Range:
    def __init__(self, start, end):
        self.start = start
        self.end = end
    dt = lambda self: self.end - self.start
    __cmp__ = lambda self, other: cmp(self.dt(), other.dt())


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
        return '%s:%s'%(_(h), _(m, fillZero=2))
    else:
        return '%s:%s:%s'%(_(h), _(m, fillZero=2), _(s, fillZero=2))

def getNum10FactPow(n):
    if n == 0:
        return 0, 1
    n = str(int(n))
    nozero = n.rstrip('0')
    return int(nozero), len(n) - len(nozero)

getNum10Pow = lambda n: getNum10FactPow(n)[1]

def getYearRangeTickValues(u0, y1, minStepYear):
    data = {}
    step = 10 ** max(0, ifloor(log10(y1 - u0)) - 1)
    u0 = step * (u0//step)
    for y in range(u0, y1, step):
        n = 10 ** getNum10Pow(y)
        if n >= minStepYear:
            data[y] = n
    if u0 <= 0 <= y1:
        data[0] = max(data.values())
    return sorted(data.items())

def formatYear(y, prettyPower=False):
    if abs(y) < 10 ** 4:## FIXME
        y_st = _(y)
    else:
        #y_st = textNumEncode('%.0E'%y, changeDot=True)## FIXME
        fac, pw = getNum10FactPow(y)
        if not prettyPower or abs(fac) >= 100:## FIXME
            y_e = '%E'%y
            for i in range(10):
                y_e = y_e.replace('0E', 'E')
            y_e = y_e.replace('.E', 'E')
            y_st = textNumEncode(y_e, changeDot=True)
        else:
            sign = (u'-' if fac < 0 else '')
            fac = abs(fac)
            if fac == 1:
                fac_s = u''
            else:
                fac_s = u'%s×'%_(fac)
            pw_s = _(10) + u'ˆ' + _(pw)
            ## pw_s = _(10) + '<span rise="5" size="small">' + _(pw) + '</span>'## Pango Markup Language
            y_st = sign + fac_s + pw_s
    return LRM + y_st

#def setRandomColorsToEvents():
#    events = ui.events[:]
#    random.shuffle(events)
#    dh = 360.0/len(events)
#    hue = 0
#    for event in events:
#        event.color = hslToRgb(hue, boxColorSaturation, boxColorLightness)
#        hue += dh

def calcTimeLineData(timeStart, timeWidth, width):
    timeEnd = timeStart + timeWidth
    jd0 = getJdFromEpoch(timeStart)
    jd1 = getJdFromEpoch(timeEnd)
    widthDays = timeWidth / (24.0*3600)
    pixelPerSec = float(width)/timeWidth ## pixel/second
    dayPixel = 24*3600*pixelPerSec ## pixel
    #print 'dayPixel = %s px'%dayPixel
    getEPos = lambda epoch: (epoch-timeStart)*pixelPerSec
    getJPos = lambda jd: (getEpochFromJd(jd)-timeStart)*pixelPerSec
    ######################## Holidays
    holidays = []
    if changeHolidayBg and changeHolidayBgMinDays < widthDays < changeHolidayBgMaxDays:
        for jd in getHolidaysJdList(jd0, jd1+1):
            holidays.append(getJPos(jd))
    ######################## Ticks
    ticks = []
    tickEpochList = []
    minStep = minorStepMin/pixelPerSec ## second
    #################
    (year0, month0, day0) = jd_to(jd0, core.primaryMode)
    (year1, month1, day1) = jd_to(jd1, core.primaryMode)
    ############ Year
    minStepYear = minStep//minYearLenSec ## years ## int or iceil?
    yearPixel = minYearLenSec*pixelPerSec ## pixels
    for (year, size) in getYearRangeTickValues(year0, year1+1, minStepYear):
        tmEpoch = getEpochFromDate(year, 1, 1, core.primaryMode)
        if tmEpoch in tickEpochList:
            continue
        unitSize = size*yearPixel
        label = formatYear(year) if unitSize >= majorStepMin else ''
        ticks.append(Tick(
            tmEpoch,
            getEPos(tmEpoch),
            unitSize,
            label,
        ))
        tickEpochList.append(tmEpoch)
    ############ Month
    monthPixel = avgMonthLen*pixelPerSec ## pixel
    minMonthUnit = float(minStep)/avgMonthLen ## month
    if minMonthUnit <= 3:
        for ym in range(year0*12+month0-1, year1*12+month1-1+1):## +1 FIXME
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
                getEPos(tmEpoch),
                unitSize,
                getMonthName(core.primaryMode, m) if unitSize >= majorStepMin else '',
            ))
            tickEpochList.append(tmEpoch)
    ################
    if showWeekStart and showWeekStartMinDays < widthDays < showWeekStartMaxDays:
        wd0 = jwday(jd0)
        jdw0 = jd0 + (core.firstWeekDay-wd0)%7
        unitSize = dayPixel*7
        if unitSize < majorStepMin:
            label = ''
        else:
            label = core.weekDayNameAb[core.firstWeekDay]
        for jd in range(jdw0, jd1+1, 7):
            tmEpoch = getEpochFromJd(jd)
            ticks.append(Tick(
                tmEpoch,
                getEPos(tmEpoch),
                unitSize,
                label,
                color=weekStartTickColor,
            ))
            #tickEpochList.append(tmEpoch)
    ############ Day of Month
    hasMonthName = timeWidth < 5*24*3600
    minDayUnit = float(minStep)/(24*3600) ## day
    if minDayUnit <= 15:
        for jd in range(jd0, jd1+1):
            tmEpoch = getEpochFromJd(jd)
            if tmEpoch in tickEpochList:
                continue
            (year, month, day) = jd_to(jd, core.primaryMode)
            if day==16:
                dayUnit = 15
            elif day in (6, 11, 21, 26):
                dayUnit = 5
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
                getEPos(tmEpoch),
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
        firstEpoch = iceil(timeStart/stepSec)*stepSec
        for tmEpoch in range(firstEpoch, iceil(timeEnd), stepSec):
            if tmEpoch in tickEpochList:
                continue
            ticks.append(Tick(
                tmEpoch,
                getEPos(tmEpoch),
                unitSize,
                formatEpochTime(tmEpoch) if unitSize >= majorStepMin else '',
            ))
            tickEpochList.append(tmEpoch)
    ######################## Event Boxes
    boxesDict = {}
    for groupIndex in range(len(ui.eventGroups)):
        group = ui.eventGroups.byIndex(groupIndex)
        if not group.enable:
            continue
        borderTm = (boxMoveBorder+boxMoveLineW)/pixelPerSec
        for t0, t1, eid, odt in group.node.getEvents(timeStart-borderTm, timeEnd+borderTm):
            pixBoxW = (t1-t0)*pixelPerSec
            if pixBoxW < skipEventPixelLimit:
                continue
            if not isinstance(eid, int):
                print '----- bad eid from getEvents: %r'%eid
                continue
            event = group[eid]
            eventIndex = group.index(eid)
            if t0 <= timeStart and timeEnd <= t1:## Fills Range ## FIXME
                continue
            box = Box(
                t0,
                t1,
                odt,
                0,
                1,
                event.summary,
                group.color,
                (group.id, event.id) if pixBoxW > 0.5 else None,
                (groupIndex, eventIndex),
            )## or event.color FIXME
            if pixBoxW <= 2*boxLineWidth:
                box.lineW = 0
            box.hasBorder = (event.name in movableEventTypes)
            boxValue = (group.id, t0, t1)
            try:
                boxesDict[boxValue].append(box)
            except KeyError:
                boxesDict[boxValue] = [box]
    ###
    boxes = []
    for bvalue, blist in boxesDict.iteritems():
        if len(blist) < 4:
            boxes += blist
        else:
            box = blist[0]
            box.text = _('%s events')%_(len(blist))
            box.ids = None
            #print 'len(blist)', len(blist)
            #print (box.t1 - box.t0), 'secs'
            boxes.append(box)
    del boxesDict
    ###
    boxes.sort() ## FIXME
    placedBoxes = []
    for box in boxes:
        conflictRanges = []
        minConflictH = 1
        for box1 in placedBoxes:
            if box1.tOverlaps(box):
                box.tConflictBefore.append(box1)
                conflictRanges.append((box1.u0, box1.u1))
                minConflictH = min(minConflictH, box1.du())
        placedBoxes.append(box)
        freeRanges = realRangeListsDiff([(0, 1)], conflictRanges)
        if freeRanges:
            bigestFree = max([Range(a, b) for (a, b) in freeRanges])
            bigestFreeH = bigestFree.dt() ## biggest free range height
            #if bigestFreeH==1 or bigestFreeH/(1.0-bigestFreeH) >= minConflictH:
            if bigestFreeH >= minConflictH:
                box.u0 = bigestFree.start
                box.u1 = bigestFree.end
                continue
        ## now we should compress all conflicting boxes and place the new box on top of them
        h = 1 - 1.0/(minConflictH+1)
        box.u0 = 1 - h
        box.u1 = 1
        for box1 in box.tConflictBefore:## FIXME
            if box.yOverlaps(box1):
                yResizeBox(box1, 1-h)
    return {
        'holidays': holidays,
        'ticks': ticks,
        'boxes': boxes,
    }



