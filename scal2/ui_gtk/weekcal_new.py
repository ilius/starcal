# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

import sys, os
from math import pi

from scal2 import core

from scal2.locale_man import tr as _
from scal2.locale_man import rtl, rtlSgn

from scal2.core import myRaise, getMonthName, getMonthLen, getNextMonth, getPrevMonth, pixDir

from scal2 import ui
from scal2.weekcal import getCurrentWeekStatus

import gobject
import gtk
from gtk import gdk

from scal2.ui_gtk.drawing import setColor, fillColor, newTextLayout, Button
from scal2.ui_gtk.utils import pixbufFromFile
from scal2.ui_gtk import gtk_ud as ud
from scal2.ui_gtk.customize import CustomizableCalObj





def show_event(widget, event):
    print type(widget), event.type.value_name#, event.get_value()#, event.send_event





class Column(gtk.Widget, CustomizableCalObj):
    holidayColorize = False
    def __init__(self, wcal):
        gtk.Widget.__init__(self)
        self.initVars()
        self.connect('expose-event', self.onExposeEvent)
        self.connect('button-press-event', self.buttonPress)
        #self.connect('event', show_event)
        self.wcal = wcal
    def do_realize(self):
        self.set_flags(self.flags() | gtk.REALIZED)
        self.window = gdk.Window(
            self.get_parent_window(),
            width=self.allocation.width,
            height=self.allocation.height,
            window_type=gdk.WINDOW_CHILD,
            wclass=gdk.INPUT_OUTPUT,
            event_mask=self.get_events() \
                | gdk.EXPOSURE_MASK | gdk.BUTTON1_MOTION_MASK
                | gdk.BUTTON_PRESS_MASK | gdk.POINTER_MOTION_MASK | gdk.POINTER_MOTION_HINT_MASK,
        )
        self.window.set_user_data(self)
        self.style.attach(self.window)#?????? Needed??
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.window.move_resize(*self.allocation)
    def onExposeEvent(self, widget=None, event=None):
        pass
    def drawTextList(self, textList):
        w = self.allocation.width
        h = self.allocation.height
        cr = self.window.cairo_create()
        ###
        cr.rectangle(0, 0, w, h)
        fillColor(cr, ui.bgColor)
        ###
        rowH = h/7.0
        itemW = w - ui.wcalPadding
        for i in range(7):
            layout = newTextLayout(
                self,
                textList[i],
                maxSize=(itemW, rowH),
            )
            if layout:
                layoutW, layoutH = layout.get_pixel_size()
                layoutX = (w-layoutW)/2.0
                layoutY = (i+0.5)*rowH - layoutH/2.0
                cr.move_to(layoutX, layoutY)
                if self.holidayColorize and self.wcal.status[i].holiday:
                    setColor(cr, ui.holidayColor)
                else:
                    setColor(cr, ui.wcalTextColor)
                cr.show_layout(layout)
    def buttonPress(self, obj, event):
        return False


class CButton(Button, CustomizableCalObj):
    def __init__(self, imageName, func):
        Button.__init__(self, imageName, func, 0, 0, False)
        self.initVars()

class PrevButton(CButton):
    _name = 'previous'
    desc = _('Previous')
    def __init__(self, func):
        CButton.__init__(self, 'arrow-up.png', func)


class TodayButton(CButton):
    _name = 'today'
    desc = _('Today')
    def __init__(self, func):
        CButton.__init__(self, 'home.png', func)

class NextButton(CButton):
    _name = 'next'
    desc = _('Next')
    def __init__(self, func):
        CButton.__init__(self, 'arrow-down.png', func)


class ButtonsColumn(Column):
    _name = 'buttons'
    desc = _('Buttons')
    def __init__(self, wcal):
        Column.__init__(self, wcal)
        #self.connect('button-press-event', self.buttonPress)
    def jdPlus(self, plus):
        ui.jdPlus(plus)
        self.onDateChange()
    def changeDate(self, year, month, day, mode=None):
        ui.changeDate(year, month, day, mode)
        self.onDateChange()
    goToday = lambda self, widget=None: self.changeDate(*core.getSysDate())
    def __init__(self, wcal):
        Column.__init__(self, wcal)
        self.bsize = 22
        self.set_property('width-request', ui.wcalButtonsWidth)
        for item in [
            PrevButton(lambda: self.jdPlus(-1)),
            TodayButton(self.goToday),
            NextButton(lambda: self.jdPlus(1)),
        ]:
            self.appendItem(item)
    def arrangeButtons(self):
        w = self.allocation.width
        h = self.allocation.height
        s = self.bsize
        n = len(self.items)
        x = (w-s)/2.0
        hs = self.bsize + ui.wcalButtonsSpacing
        y0 = (h - hs*n)/2.0
        for i in range(n):
            b = self.items[i]
            b.x = x
            b.y = y0 + i*hs
    def onExposeEvent(self, widget=None, event=None):
        w = self.allocation.width
        h = self.allocation.height
        cr = self.window.cairo_create()
        self.arrangeButtons()
        ###
        cr.rectangle(0, 0, w, h)
        fillColor(cr, ui.bgColor)
        ###
        s = self.bsize
        for b in self.items:
            b.draw(cr, s, s)
    def buildWidget(self):
        self.show()
    def onDateChange(self, *a, **kw):
        print 'ButtonsColumn.onDateChange'
        CustomizableCalObj.onDateChange(self, *a, **kw)
        self.queue_draw()
    def buttonPress(self, obj, event):
        b = event.button
        #print 'buttonPress', b
        x = event.x
        y = event.y
        w = self.allocation.width
        h = self.allocation.height
        if b==1:
            for button in self.items:
                if button.contains(x, y, w, h):
                    button.func()
                    return True
        return False


class WeekDaysColumn(Column):
    _name = 'weekDays'
    desc = _('Week Days')
    def __init__(self, wcal):
        Column.__init__(self, wcal)
        self.set_property('width-request', ui.wcalWeekDaysWidth)
    def onExposeEvent(self, widget=None, event=None):
        self.drawTextList([core.getWeekDayN(i) for i in range(7)])
        
        
class PluginsTextColumn(Column):
    _name = 'pluginsText'
    desc = _('Plugins Text')
    expand = True
    def onExposeEvent(self, widget=None, event=None):
        self.drawTextList([self.wcal.status[i].pluginsText for i in range(7)])


class EventsTextColumn(Column):
    _name = 'eventsText'
    desc = _('Events Text')
    expand = True
    def onExposeEvent(self, widget=None, event=None):
        self.drawTextList([self.wcal.status[i].getEventText() for i in range(7)])

class EventsIconColumn(Column):
    _name = 'eventsIcon'
    desc = _('Events Icon')
    maxPixH = 26.0
    maxPixW = 26.0
    def __init__(self, wcal):
        Column.__init__(self, wcal)
        self.set_property('width-request', ui.wcalEventsIconColWidth)
    def onExposeEvent(self, widget=None, event=None):
        self.drawTextList([core.getWeekDayN(i) for i in range(7)])
        w = self.allocation.width
        h = self.allocation.height
        cr = self.window.cairo_create()
        ###
        cr.rectangle(0, 0, w, h)
        fillColor(cr, ui.bgColor)
        ###
        rowH = h/7.0
        itemW = w - ui.wcalPadding
        #print
        for i in range(7):
            c = self.wcal.status[i]
            iconList = c.getEventIcons()
            #print i, iconList
            if iconList:
                n = len(iconList)
                scaleFact = min(
                    1.0,
                    h/self.maxPixH,
                    w/(n*self.maxPixW),
                )
                #print 'scaleFact', h/self.maxPixH, w/(n*self.maxPixW)
                x0 = (w/scaleFact - (n-1)*self.maxPixW)/2.0
                y0 = (2*i+1) * h / (14.0*scaleFact)
                if rtl:
                    iconList.reverse()## FIXME
                for iconIndex, icon in enumerate(iconList):
                    try:
                        pix = gdk.pixbuf_new_from_file(icon)
                    except:
                        myRaise(__file__)
                        continue
                    pix_w = pix.get_width()
                    pix_h = pix.get_height()
                    x1 = x0 + iconIndex*self.maxPixW - pix_w/2.0
                    y1 = y0 - pix_h/2.0
                    cr.scale(scaleFact, scaleFact)
                    cr.set_source_pixbuf(pix, x1, y1)
                    cr.rectangle(x1, y1, pix_w, pix_h)
                    cr.fill()
                    cr.scale(1.0/scaleFact, 1.0/scaleFact)
        


class WeekCal(gtk.HBox, CustomizableCalObj):
    _name = 'weekCal'
    desc = _('Week Calendar')
    def __init__(self):
        gtk.HBox.__init__(self)
        self.set_property('height-request', ui.wcalHeight)
        self.initVars()
        ###
        #self.connect('button-press-event', self.buttonPress)
        ###
        for item in [
            #ButtonsColumn(self),
            WeekDaysColumn(self),
            EventsIconColumn(self),
        ]:
            self.appendItem(item)
        ###
        self.buildWidget()
        ###
        self.updateStatus()
    def updateStatus(self):
        self.status = getCurrentWeekStatus()
    def onDateChange(self, *a, **kw):
        CustomizableCalObj.onDateChange(self, *a, **kw)
        self.updateStatus()
        self.queue_draw()


#gobject.type_register(WeekCal)
#gobject.type_register(CButton)

for cls in (
    Column,
    #CButton,
    #PrevButton,
    #TodayButton,
    #NextButton,
    WeekCal,
):
    gobject.type_register(cls)
    cls.registerSignals()
    


#for cls in (
#    Column,
#    CButton,
#    WeekCal,
#):
#    cls.registerSignals()



cls = WeekCal
gobject.signal_new('popup-menu-cell', cls, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [int, int, int])
gobject.signal_new('popup-menu-main', cls, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [int, int, int])
gobject.signal_new('2button-press', cls, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
gobject.signal_new('pref-update-bg-color', cls, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])



if __name__=='__main__':
    win = gtk.Dialog()
    cal = WeekCal()
    #print cal.items
    win.add_events(
        gdk.POINTER_MOTION_MASK | gdk.FOCUS_CHANGE_MASK | gdk.BUTTON_MOTION_MASK |
        gdk.BUTTON_PRESS_MASK | gdk.BUTTON_RELEASE_MASK | gdk.SCROLL_MASK |
        gdk.KEY_PRESS_MASK | gdk.VISIBILITY_NOTIFY_MASK | gdk.EXPOSURE_MASK
    )
    win.vbox.pack_start(cal, 1, 1)
    win.vbox.show()
    win.resize(600, 400)
    win.run()











