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
                       getJdFromEpoch, getEpochFromJd, jd_to, to_jd, getJhmsFromEpoch, getEpochFromDate,\
                       getCurrentTimeZone
                       

from scal2 import ui

from scal2.ui_gtk.drawing import *
from scal2.ui_gtk import preferences

import gobject
import gtk
from gtk import gdk

def show_event(widget, event):
    print type(widget), event.type.value_name, event.get_time()#, event.send_event



#sunLightH = 10## FIXME
majorStepMin = 50 ## with label
minorStepMin = 5 ## with or without label
maxLabelWidth = 50 ## or the same majorStepMin
maxTickHeightRatio = 0.5
baseTickH = 2
baseTickW = 1
fontFamily = 'Sans'
baseFontSize = 8
labelYRatio = 1.2
bgColor = (50, 50, 50)
fgColor = (255, 255, 255)

scrollZoomStep = 1.2
scrollMoveStep = 20

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

class Tick:
    def __init__(self, epoch, pos, unitSize, label='', truncateLabel=False):
        self.epoch = epoch
        self.pos = pos ## pixel position
        self.height = unitSize ** 0.5 * baseTickH
        self.width = unitSize ** 0.1 * baseTickW
        self.fontSize = unitSize ** 0.2 * baseFontSize
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
    for (size, year) in getYearRangeTickValues(y0, y1, minStepYear):## boundaries FIXME
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
    if minMonthUnit < 3:
        for ym in range(ym0, ym1):
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
    if minDayUnit < 15:
        for jd in range(jd0, jd1):
            tmEpoch = getEpochFromJd(jd)
            if tmEpoch in tickEpochList:
                continue
            (year, month, day) = jd_to(jd, core.primaryMode)
            unitSize = 24*3600
            if day in (1, 16):
                dayUnit = 15
            #elif day in (5, 10, 20, 25):
            #    dayUnit = 5
            else:
                dayUnit = 1
            if dayUnit < minDayUnit:
                continue
            unitSize = dayPixel*dayUnit
            if hasMonthName:
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




class TimeLine(gtk.Widget):
    def __init__(self):
        gtk.Widget.__init__(self)
        #self.connect('button-press-event', self.buttonPress)
        self.connect('expose-event', self.onExposeEvent)
        self.connect('scroll-event', self.onScroll)
        #self.connect('destroy', self.quit)
        #self.connect('event', show_event)
        self.timeWidth = 24*3600
        self.timeStart = time.time() + getCurrentTimeZone() - self.timeWidth/2
        #print formatEpochTime(time.time() + getCurrentTimeZone())
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
        w = self.allocation.width
        h = self.allocation.height
        maxTickHeight = maxTickHeightRatio*h
        cr = self.window.cairo_create()
        cr.rectangle(0, 0, w, h)
        fillColor(cr, bgColor)
        setColor(cr, fgColor)
        for tick in splitTime(self.timeStart, self.timeWidth, w):
            tickH = tick.height
            tickW = tick.width
            tickH = min(tickH, maxTickHeight)
            ###
            tickX = tick.pos-tickW/2.0
            tickY = 1
            cr.rectangle(tickX, tickY, tickW, tickH)
            try:
                cr.fill()
            except:
                print 'fill, x=%.2f, y=%.2f, w=%.2f, h=%.2f'%(tickX, tickY, tickW, tickH)
            ###
            font = (
                fontFamily,
                False,
                False,
                tick.fontSize,
            )
            layout = newLimitedWidthTextLayout(self, tick.label, tick.maxLabelWidth, font=font, truncate=tick.truncateLabel)## FIXME
            if layout:
                layoutW, layoutH = layout.get_pixel_size()
                layoutX = tick.pos - layoutW/2.0
                layoutY = tickH*labelYRatio
                try:
                    cr.move_to(layoutX, layoutY)
                except:
                    print 'move_to, x=%.2f, y=%.2f'%(layoutX, layoutY)
                else:
                    cr.show_layout(layout)
    def onScroll(self, widget, event):
        isUp = event.direction.value_nick=='up'
        if event.state & gdk.CONTROL_MASK:
            timeLeft = event.x*self.timeWidth/self.allocation.width
            zoomTime = self.timeStart + timeLeft
            zoomValue = 1.0/scrollZoomStep if isUp else scrollZoomStep
            self.timeStart = zoomTime - timeLeft*zoomValue
            self.timeWidth = self.timeWidth*zoomValue
        else:
            self.timeStart += (1 if isUp else -1)*scrollMoveStep*self.timeWidth/float(self.allocation.width)
        self.queue_draw()
        return True            



gobject.type_register(TimeLine)

if __name__=='__main__':
    tline = TimeLine()
    win = gtk.Window()
    win.add(tline)
    win.resize(1366, 150)
    win.connect('delete-event', gtk.main_quit)
    win.show_all()
    gtk.main()




