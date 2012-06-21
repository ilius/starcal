# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
#print time.time(), __file__

import sys, os, struct
from math import pi
from os.path import join, isfile
from xml.dom.minidom import parse

from scal2 import core

from scal2.locale_man import tr as _
from scal2.locale_man import rtl, rtlSgn

from scal2.core import myRaise, getMonthName, getMonthLen, getNextMonth, getPrevMonth, pixDir

from scal2 import ui
from scal2.weekcal import getCurrentWeekStatus

import gobject
import gtk
from gtk import gdk

from scal2.ui_gtk.drawing import setColor, fillColor, newLimitedWidthTextLayout, Button
from scal2.ui_gtk import gcommon
from scal2.ui_gtk.gcommon import IntegratedCalWidget
from scal2.ui_gtk import preferences
#from scal2.ui_gtk import desktop
#from scal2.ui_gtk import wallpaper

rootWindow = gdk.get_default_root_window() ## Good Place?????

prevImage = 'week-previous.png'
nextImage = 'week-next.png'
if rtl:
    (prevImage, nextImage) = (nextImage, prevImage)



def show_event(widget, event):
    print type(widget), event.type.value_name, event.get_value()#, event.send_event


class WeekDayRowItem:
    getText = lambda self, row: core.getWeekDayN(row.weekDayIndex)
    def __init__(self, width=70, textAlign=0.5, expand=False):
        self.width = width
        self.textAlign = textAlign
        self.holidayColorize = True
        self.expand = expand

class DayNumRowItem:
    getText = lambda self, row: _(row.dates[self.mode][2], self.mode)
    def __init__(self, mode, width=30, textAlign=0.5, expand=False):
        self.mode = mode
        self.width = width
        self.textAlign = textAlign
        self.holidayColorize = True
        self.expand = expand

class PluginsTextRowItem:
    getText = lambda self, row: row.pluginsText.replace('\n', ' | ')
    def __init__(self, width=200, textAlign=0.5, expand=True):
        self.width = width
        self.textAlign = textAlign
        self.holidayColorize = False
        self.expand = expand

#class Widget:


class Button:
    def __init__(self, imageName, func, x, y, autoDir=True):
        self.imageName = imageName
        if imageName.startswith('gtk-'):
            self.pixbuf = gdk.pixbuf_new_from_stock(imageName)
        else:
            self.pixbuf = gdk.pixbuf_new_from_file(join(pixDir, imageName))
        self.func = func
        self.width = self.pixbuf.get_width()
        self.height = self.pixbuf.get_height()
        self.x = x
        self.y = y
        self.autoDir = autoDir
    __repr__ = lambda self: 'Button(%r, %r, %r, %r, %r)'%(
        self.imageName,
        self.func.__name__,
        self.x,
        self.y,
        self.autoDir,
    )
    def getAbsPos(self, w, h):
        x = self.x
        y = self.y
        if self.autoDir and rtl:
            x = -x
        if x<0:
            x = w - self.width + x
        if y<0:
            y = h - self.height + y
        return (x, y)
    def draw(self, cr, w, h):
        (x, y) = self.getAbsPos(w, h)
        cr.set_source_pixbuf(self.pixbuf, x, y)
        cr.rectangle(x, y, self.width, self.height)
        cr.fill()
    def contains(self, px, py, w, h):
        (x, y) = self.getAbsPos(w, h)
        return (x <= px < x+self.width and y <= py < y+self.height)



class WeekCal(gtk.Widget, IntegratedCalWidget):
    topMargin = 30
    widthSpacing = 20
    def __init__(self, closeFunc):
        gtk.Widget.__init__(self)
        self.initVars('weekCal', _('Week Calendar'))
        ###
        self.closeFunc = closeFunc
        self.connect('button-press-event', self.buttonPress)
        self.connect('expose-event', self.onExposeEvent)
        #self.connect('event', show_event)
        self.buttons = [
            Button(prevImage, self.goBack, 5, 5, True),
            Button('home.png', self.goToday, 35, 5, True),
            Button(nextImage, self.goNext, 65, 5, True),
            Button('resize-small.png', self.startResize, -1, -1, False),
            Button('exit.png', closeFunc, -5, 5, True),
        ]
        self.rowItems = [WeekDayRowItem(), PluginsTextRowItem()]
        for cal in ui.shownCals:
            self.rowItems.append(DayNumRowItem(cal['mode']))
    #def onConfigChange(self, *a, **kw):
    #    IntegratedCalWidget.onConfigChange(self, *a, **kw)
    #    self.onDateChange()
    def onDateChange(self, *a, **kw):
        IntegratedCalWidget.onDateChange(self, *a, **kw)
        self.queue_draw()
    def changeDate(self, year, month, day):
        ui.changeDate(year, month, day)
        self.onDateChange()
    def jdPlus(self, plus):
        ui.jdPlus(plus)
        self.onDateChange()
    goToday = lambda self, event=None: self.changeDate(*core.getSysDate())
    goBack = lambda self, event=None: self.jdPlus(-7)
    goNext = lambda self, event=None: self.jdPlus(7)
    def startResize(self, event):
        self.parent.begin_resize_drag(
            gdk.WINDOW_EDGE_SOUTH_EAST,
            event.button,
            int(event.x_root),
            int(event.y_root),
            event.time,
        )
    def quit(self, *args):
        if ui.mainWin:
            self.hide()
        else:
            gtk.main_quit()## FIXME
    def buttonPress(self, obj, event):
        b = event.button
        #print 'buttonPress', b
        x = event.x
        y = event.y
        w = self.allocation.width
        h = self.allocation.height
        if b==1:
            for button in self.buttons:
                if button.contains(x, y, w, h):
                    button.func(event)
                    return True
        return False
    def do_realize(self):
        self.set_flags(self.flags() | gtk.REALIZED)
        self.window = gdk.Window(
            self.get_parent_window(),
            width=self.allocation.width,
            height=self.allocation.height,
            window_type=gdk.WINDOW_CHILD,
            wclass=gdk.INPUT_OUTPUT,
            event_mask=self.get_events() | gdk.EXPOSURE_MASK | gdk.BUTTON1_MOTION_MASK
                | gdk.BUTTON_PRESS_MASK | gdk.POINTER_MOTION_MASK | gdk.POINTER_MOTION_HINT_MASK,
            #colormap=self.get_screen().get_rgba_colormap(),
        )
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
        cr = self.window.cairo_create()
        cr.rectangle(0, 0, w, h)
        fillColor(cr, ui.bgColor)
        setColor(cr, ui.weekCalTextColor)
        status = getCurrentWeekStatus()
        rowH = (h-self.topMargin)/7
        widthList = []
        expandIndex = []
        for (i, item) in enumerate(self.rowItems):
            widthList.append(item.width + self.widthSpacing)
            if item.expand:
                expandIndex.append(i)
        extraWidth = float(w - sum(widthList)) / len(expandIndex)
        for i in expandIndex:
            widthList[i] += extraWidth
        del expandIndex
        for (i, row) in enumerate(status):
            y = self.topMargin + i*rowH
            cr.rectangle(0, 0, w, h)
            #fillColor(cr, bgColor)
            if rtl:
                x = w
            else:
                x = 0
            for (j, item) in enumerate(self.rowItems):
                itemW = widthList[j]
                text = item.getText(row).decode('utf8')
                if text:
                    layout = newLimitedWidthTextLayout(self, text, itemW)
                    if layout:
                        layoutW, layoutH = layout.get_pixel_size()
                        layoutX = x + item.textAlign * (itemW-layoutW)
                        if rtl:
                            layoutX -= itemW
                        cr.move_to(layoutX, y+(rowH - layoutH)/2)
                        if row.holiday and item.holidayColorize:
                            setColor(cr, ui.holidayColor)
                        else:
                            setColor(cr, ui.weekCalTextColor)
                        cr.show_layout(layout)
                x = x - rtlSgn() * itemW
        for button in self.buttons:
            button.draw(cr, w, h)
        #print time.time()-t0
        return False



class WeekCalWindow(gtk.Window, IntegratedCalWidget):
    def __init__(self):
        gtk.Window.__init__(self)
        self.initVars('weekCalWin', _('Week Calendar'))
        gcommon.windowList.appendItem(self)
        ####
        self.set_decorated(False)
        self.set_title('Week Calendar')
        ######
        self.wcal = WeekCal(self.closeClicked)
        self.add(self.wcal)
        ######
        self.connect('delete-event', self.wcal.quit)
        self.connect('button-press-event', self.buttonPress)
        ######
        self.resize(600, 300)
        self.wcal.show()
        self.appendItem(self.wcal)
    def closeClicked(self, arg=None, event=None):
        if ui.mainWin:
            self.hide()
        else:
            gtk.main_quit()## FIXME
        return True
    def buttonPress(self, obj, event):
        b = event.button
        #print 'buttonPress', b
        if b==1:
            (x, y, mask) = rootWindow.get_pointer()
            self.begin_move_drag(event.button, x, y, event.time)
        return False



gobject.type_register(WeekCal)
WeekCal.registerSignals()
WeekCalWindow.registerSignals()


if __name__=='__main__':
    win = WeekCalWindow()
    win.show_all()
    gtk.main()


