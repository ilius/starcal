#!/usr/bin/python
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

import time
from math import ceil, sqrt

from scal2 import core

from scal2.locale_man import tr as _
from scal2.locale_man import rtl, rtlSgn, cutText

from scal2.core import myRaise, getMonthName, getMonthLen, getNextMonth, getPrevMonth, pixDir,\
                       getJdFromEpoch, jd_to, to_jd, getJhmsFromEpoch, getEpochFromDate

from scal2 import ui

from scal2.ui_gtk.drawing import *
from scal2.ui_gtk import preferences

def show_event(widget, event):
    print type(widget), event.type.value_name, event.get_time()#, event.send_event



#sunLightH = 10## FIXME
majorStepMin = 20 ## with label
minorStepMin = 2 ## with or without label
maxLabelWidth = 15 ## or the same majorStepMin
maxTickHeightRatio = 0.5
baseTickH = 2
baseFont = ('Sans', False, False, 5)
tickWperH = 0.2
bgColor = (50, 50, 50)
fgColor = (255, 255, 255)

unitSteps = (
    (1, (1, 5, 15, 30)),
    (60, (1, 5, 15, 30)),
    (3600, (1, 3, 6, 12)),
    (24*3600, (1, 5, 10)),
)

unitStepsPlain = []
for unit, values in unitSteps:
    for value in values:
        unitStepsPlain.append((unit, value))

minYearLenSec = 365*24*3600
avgMonthLen = 30*24*3600

class Tick:
    def __init__(self, epoch, pos, size, label='', truncateLabel=False):
        self.epoch = epoch
        self.pos = pos ## pixel position
        self.size = size
        self.label

def formatEpochTime(epoch):
    (jd, h, m, s) = getJhmsFromEpoch(epoch)
    return '%d:%.2d:%.2d'%(h, m, s)

def getYearRangeTickValues(y0, y1, minStepYear):
    data = []
    numList = []
    for n in (1000, 500, 100, 50, 10, 1):
        if n<minStepYear:
            break
        numList.append(n)
    for y in range(y0, y1):
        for n in numList:
            if y%n == 0:
                data.append((n, y))
                break
    return data

def splitTime(timeStart, timeWidth, width):
    timeEnd = timeStart + timeWidth
    pixelPerSec = float(width)/timeWidth ## pixel/second
    minStep = minorStepMin/pixelPerSec
    ticks = []
    tickEpochList = []
    #################
    (y0, m0, d0) = getPrimaryDateFromEpoch(timeStart)
    (y1, m1, d1) = getPrimaryDateFromEpoch(timeEnd)
    ############ Year
    minStepYear = int(minStep/minYearLenSec)
    for (size, year) in getYearRangeTickValues(y0, y1, minStepYear):## boundaries FIXME
        tmEpoch = getEpochFromDate(year, 1, 1, core.primaryMode)
        if tmEpoch in tickEpochList:
            continue
        ticks.append(Tick(
            tmEpoch,
            (tmEpoch-timeStart)*pixelPerSec,
            size,
            _(year) if minYearLenSec*pixelPerSec >= minorStepMin else '',
        ))
        tickEpochList.append(tmEpoch)
    ############ Month
    ym0 = y0*12 + m0-1
    ym1 = y1*12 + m1-1
    for ym in range(ym0, ym1):
        stepSec = avgMonthLen
        if ym%3==0:
            stepSec *= 3
        if stepSec < minStep:
            continue
        (y, m) = divmod(ym, 12) ; m+=1
        tmEpoch = getEpochFromDate(y, m, 1, core.primaryMode)
        if tmEpoch in tickEpochList:
            continue
        ticks.append(Tick(
            tmEpoch,
            (tmEpoch-timeStart)*pixelPerSec,
            stepSec,
            getMonthName(core.primaryMode, m) if stepSec*pixelPerSec >= minorStepMin else '',
            True,
        ))
        tickEpochList.append(tmEpoch)
    ############ Day, Hour, Minute, Second
    for stepUnit, stepValue in reversed(unitStepsPlain):
        stepSec = stepUnit*stepValue
        if stepSec < minStep:
            break
        hasLabel = stepSec*pixelPerSec >= minorStepMin
        firstEpoch = int(ceil(timeStart/stepSec))*stepSec
        for tmEpoch in range(firstEpoch, timeEnd, stepSec):
            if tmEpoch in tickEpochList:
                continue
            #tmValue = tmEpoch*stepValue//stepSec
            ticks.append(Tick(
                tmEpoch,
                (tmEpoch-timeStart)*pixelPerSec,
                stepSec,
                formatEpochTime(tmEpoch) if hasLabel else '',
            ))
            tickEpochList.append(tmEpoch)
    for tick in ticks:
        tick.size = sqrt(tick.size)*pixelPerSec*baseTickH
    return ticks




class TimeLine(gtk.Widget):
    def __init__(self):
        gtk.Widget.__init__(self)
        #self.connect('button-press-event', self.buttonPress)
        self.connect('expose-event', self.onExposeEvent)
        #self.connect('destroy', self.quit)
        #self.connect('event', show_event)
        self.timeWidth = 24*3600
        self.timeStart = time.time()
    def do_realize(self):
        self.set_flags(self.flags() | gtk.REALIZED)
        self.window = gdk.Window(
            self.get_parent_window(), 
            width=self.allocation.width, 
            height=self.allocation.height, 
            window_type=gdk.WINDOW_CHILD, 
            wclass=gdk.INPUT_OUTPUT, 
            event_mask=self.get_events() | gdk.EXPOSURE_MASK
            | gdk.BUTTON1_MOTION_MASK | gdk.BUTTON_PRESS_MASK
            | gdk.POINTER_MOTION_MASK | gdk.POINTER_MOTION_HINT_MASK)
            #colormap=self.get_screen().get_rgba_colormap())
        #self.window.set_composited(True)
        self.window.set_user_data(self)
        self.style.attach(self.window)#?????? Needed??
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.window.move_resize(*self.allocation)
        #self.onExposeEvent()
    def onExposeEvent(self, widget=None, event=None):
        t0 = time.time()
        w = self.allocation.width
        h = self.allocation.height
        maxTickHeight = maxTickHeightRatio*h
        cr = self.window.cairo_create()
        cr.rectangle(0, 0, w, h)
        fillColor(cr, bgColor)
        setColor(cr, fgColor)
        for tick in splitTime(self.timeStart, self.timeWidth, w):
            tickH = tick.size
            tickW = tickH*tickWperH
            tickH = min(tickH, maxTickHeight)
            ###
            cr.rectangle(tick.pos-tickW/2.0, 0, tickW, tickH)
            cr.fill()
            ###
            layout = self.create_pango_layout(tick.label) ## a pango.Layout object
            layout.set_font_description(pfontEncode((
                baseFont[0],
                baseFont[1],
                baseFont[2],
                int(tickH*baseFont[3]/baseTickH),
            )))
            layoutW, layoutH = layout.get_pixel_size()
            ## maxLabelWidth
            






