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
fontFamily = ui.getFont()[0]
baseFontSize = 8
labelYRatio = 1.1
bgColor = (50, 50, 50)
fgColor = (255, 255, 255)

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

def splitTime(timeStart, timeWidth, width):## independent to gtk
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
    return ticks


