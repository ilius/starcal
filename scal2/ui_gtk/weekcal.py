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


from scal2.ui_gtk.drawing import *
from scal2.ui_gtk.utils import pixbufFromFile, DirectionComboBox
from scal2.ui_gtk.mywidgets.multi_spin_button import IntSpinButton
from scal2.ui_gtk import listener
from scal2.ui_gtk import gtk_ud as ud
from scal2.ui_gtk.customize import CustomizableCalObj, CustomizableCalBox
from scal2.ui_gtk.toolbar import ToolbarItem, CustomizableToolbar





def show_event(widget, event):
    print type(widget), event.type.value_name#, event.get_value()#, event.send_event





class Column(gtk.Widget, CustomizableCalObj):
    colorizeHolidayText = False
    showCursor = False
    def __init__(self, wcal):
        gtk.Widget.__init__(self)
        self.initVars()
        #self.connect('button-press-event', self.buttonPress)
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
    def drawBg(self, cr):
        w = self.allocation.width
        h = self.allocation.height
        cr.rectangle(0, 0, w, h)
        fillColor(cr, ui.bgColor)
        rowH = h/7.0
        for i in range(7):
            c = self.wcal.status[i]
            y0 = i*rowH
            if c.jd == ui.todayCell.jd:
                cr.rectangle(0, i*rowH, w, rowH)
                fillColor(cr, ui.todayCellColor)
            if self.showCursor and c.jd == ui.cell.jd:
                drawRoundedRect(cr, 0, y0, w, rowH, ui.cursorR)
                fillColor(cr, ui.cursorBgColor)
    def drawCursorFg(self, cr):
        w = self.allocation.width
        h = self.allocation.height
        rowH = h/7.0
        for i in range(7):
            c = self.wcal.status[i]
            y0 = i*rowH
            if self.showCursor and c.jd == ui.cell.jd:
                drawOutlineRoundedRect(cr, 0, y0, w, rowH, ui.cursorR, ui.cursorD)
                fillColor(cr, ui.cursorOutColor)
    def drawTextList(self, cr, textList):
        w = self.allocation.width
        h = self.allocation.height
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
                if self.colorizeHolidayText and self.wcal.status[i].holiday:
                    setColor(cr, ui.holidayColor)
                else:
                    setColor(cr, ui.wcalTextColor)
                cr.show_layout(layout)
    def buttonPress(self, widget, event):
        return False
    def onDateChange(self, *a, **kw):
        CustomizableCalObj.onDateChange(self, *a, **kw)
        self.queue_draw()



class ToolbarColumn(CustomizableToolbar):
    params = ('ud.wcalToolbarData',)
    defaultItems = [
        ToolbarItem('backward4', 'goto_top', 'goBackward4', 'Backward 4 Weeks'),
        ToolbarItem('backward', 'go_up', 'goBackward', 'Backward'),
        ToolbarItem('today', 'home', 'goToday', 'Today'),
        ToolbarItem('forward', 'go_down', 'goForward', 'Forward'),
        ToolbarItem('forward4', 'goto_bottom', 'goForward4', 'Forward 4 Weeks'),
    ]
    defaultItemsDict = dict([(item._name, item) for item in defaultItems])
    params = ('ud.wcalToolbarData',)
    def __init__(self, wcal):
        CustomizableToolbar.__init__(self, wcal, vertical=True)
        if not ud.wcalToolbarData['items']:
            ud.wcalToolbarData['items'] = [(item._name, True) for item in self.defaultItems]
        self.setData(ud.wcalToolbarData)
    def updateVars(self):
        CustomizableToolbar.updateVars(self)
        ud.wcalToolbarData = self.getData()



class WeekDaysColumn(Column):
    _name = 'weekDays'
    desc = _('Week Days')
    colorizeHolidayText = True
    showCursor = True
    params = ('ui.wcalWeekDaysWidth',)
    def __init__(self, wcal):
        Column.__init__(self, wcal)
        self.set_property('width-request', ui.wcalWeekDaysWidth)
        self.connect('expose-event', self.onExposeEvent)
        #####
        optionsWidget = gtk.VBox()
        ##
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Width')), 0, 0)
        spin = IntSpinButton(0, 99)
        hbox.pack_start(spin, 0, 0)
        spin.set_value(ui.wcalWeekDaysWidth)
        spin.connect('changed', self.widthSpinChanged)
        optionsWidget.pack_start(hbox, 0, 0)
        ##
        optionsWidget.show_all()
        self.optionsWidget = optionsWidget
    def widthSpinChanged(self, spin):
        value = spin.get_value()
        ui.wcalWeekDaysWidth = value
        self.set_property('width-request', value)
    def onExposeEvent(self, widget=None, event=None):
        cr = self.window.cairo_create()
        self.drawBg(cr)
        self.drawTextList(cr, [core.getWeekDayN(i) for i in range(7)])
        self.drawCursorFg(cr)
        
        
class PluginsTextColumn(Column):
    _name = 'pluginsText'
    desc = _('Plugins Text')
    expand = True
    def __init__(self, wcal):
        Column.__init__(self, wcal)
        self.connect('expose-event', self.onExposeEvent)
    def onExposeEvent(self, widget=None, event=None):
        cr = self.window.cairo_create()
        self.drawBg(cr)
        self.drawTextList(cr, [self.wcal.status[i].pluginsText for i in range(7)])


class EventsTextColumn(Column):
    _name = 'eventsText'
    desc = _('Events Text')
    expand = True
    def __init__(self, wcal):
        Column.__init__(self, wcal)
        self.connect('expose-event', self.onExposeEvent)
    def onExposeEvent(self, widget=None, event=None):
        cr = self.window.cairo_create()
        self.drawBg(cr)
        self.drawTextList(cr, [self.wcal.status[i].getEventText() for i in range(7)])

class EventsIconColumn(Column):
    _name = 'eventsIcon'
    desc = _('Events Icon')
    maxPixH = 26.0
    maxPixW = 26.0
    params = ('ui.wcalEventsIconColWidth',)
    def __init__(self, wcal):
        Column.__init__(self, wcal)
        self.set_property('width-request', ui.wcalEventsIconColWidth)
        self.connect('expose-event', self.onExposeEvent)
        #####
        optionsWidget = gtk.VBox()
        ##
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Width')), 0, 0)
        spin = IntSpinButton(0, 99)
        hbox.pack_start(spin, 0, 0)
        spin.set_value(ui.wcalEventsIconColWidth)
        spin.connect('changed', self.widthSpinChanged)
        optionsWidget.pack_start(hbox, 0, 0)
        ##
        optionsWidget.show_all()
        self.optionsWidget = optionsWidget
    def widthSpinChanged(self, spin):
        value = spin.get_value()
        ui.wcalEventsIconColWidth = value
        self.set_property('width-request', value)
    def onExposeEvent(self, widget=None, event=None):
        cr = self.window.cairo_create()
        self.drawBg(cr)
        ###
        w = self.allocation.width
        h = self.allocation.height
        ###
        rowH = h/7.0
        itemW = w - ui.wcalPadding
        for i in range(7):
            c = self.wcal.status[i]
            iconList = c.getEventIcons()
            if iconList:
                n = len(iconList)
                scaleFact = min(
                    1.0,
                    h/self.maxPixH,
                    w/(n*self.maxPixW),
                )
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
        

class DaysOfMonthColumn(Column):
    colorizeHolidayText = True
    showCursor = True
    def updateWidth(self):
        self.set_property('width-request', ui.wcalDaysOfMonthColWidth)
    def __init__(self, wcal, mode):
        Column.__init__(self, wcal)
        self.mode = mode
        self.updateWidth()
        ###
        self.connect('expose-event', self.onExposeEvent)
    def onExposeEvent(self, widget=None, event=None):
        cr = self.window.cairo_create()
        self.drawBg(cr)
        self.drawTextList(cr, [_(self.wcal.status[i].dates[self.mode][2], self.mode) for i in range(7)])
        self.drawCursorFg(cr)

class DaysOfMonthColumnGroup(gtk.HBox, CustomizableCalBox):
    _name = 'daysOfMonth'
    desc = _('Days of Month')
    params = ('ui.wcalDaysOfMonthColWidth', 'ui.wcalDaysOfMonthColDir')
    updateDir = lambda self: self.set_direction(ud.textDirDict[ui.wcalDaysOfMonthColDir])
    def __init__(self, wcal):
        gtk.HBox.__init__(self)
        self.initVars()
        self.wcal = wcal
        self.updateCols()
        self.updateDir()
        self.show()
        #####
        optionsWidget = gtk.VBox()
        ##
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Width')), 0, 0)
        spin = IntSpinButton(0, 99)
        hbox.pack_start(spin, 0, 0)
        spin.set_value(ui.wcalDaysOfMonthColWidth)
        spin.connect('changed', self.widthSpinChanged)
        optionsWidget.pack_start(hbox, 0, 0)
        ##
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Direction')), 0, 0)
        combo = DirectionComboBox()
        hbox.pack_start(combo, 0, 0)
        combo.setValue(ui.wcalDaysOfMonthColDir)
        combo.connect('changed', self.dirComboChanged)
        optionsWidget.pack_start(hbox, 0, 0)
        ##
        optionsWidget.show_all()
        self.optionsWidget = optionsWidget
    def widthSpinChanged(self, spin):
        ui.wcalDaysOfMonthColWidth = spin.get_value()
        for child in self.get_children():
            child.updateWidth()
    def dirComboChanged(self, combo):
        ui.wcalDaysOfMonthColDir = combo.getValue()
        self.updateDir()
    def updateCols(self):
        for child in self.get_children():
            child.destroy()
        for cal in ui.shownCals:
            if cal['enable']:
                col = DaysOfMonthColumn(self.wcal, cal['mode'])
                col.show()
                self.pack_start(col, 0, 0)
    def onConfigChange(self, *a, **ka):
        CustomizableCalBox.onConfigChange(self, *a, **ka)
        self.updateCols()

class WeekCal(gtk.HBox, CustomizableCalBox):
    _name = 'weekCal'
    desc = _('Week Calendar')
    def __init__(self):
        gtk.HBox.__init__(self)
        self.set_property('height-request', ui.wcalHeight)
        self.initVars()
        self.myKeys = (
            'up', 'down', 'page_up', 'page_down',
            'space', 'home', 'end',
            #'menu', 'f10', 'm',
        )
        self.connect('key-press-event', self.keyPress)
        self.connect('scroll-event', self.scroll)
        ###
        self.connect('button-press-event', self.buttonPress)
        #####
        defaultItems = [
            ToolbarColumn(self),
            WeekDaysColumn(self),
            PluginsTextColumn(self),
            EventsIconColumn(self),
            EventsTextColumn(self),
            DaysOfMonthColumnGroup(self),
        ]
        defaultItemsDict = dict([(item._name, item) for item in defaultItems])
        for name, enable in ui.wcalItems:
            try:
                item = defaultItemsDict[name]
            except KeyError:
                print 'weekCal item %s does not exist'%name
            else:
                item.enable = enable
                self.appendItem(item)
        #####
        optionsWidget = gtk.VBox()
        ##
        hbox = gtk.HBox()
        spin = IntSpinButton(1, 9999)
        spin.set_value(ui.wcalHeight)
        spin.connect('changed', self.heightSpinChanged)
        hbox.pack_start(gtk.Label(_('Height')), 0, 0)
        hbox.pack_start(spin, 0, 0)
        optionsWidget.pack_start(hbox, 0, 0)
        ###
        optionsWidget.show_all()
        self.optionsWidget = optionsWidget
        #####
        self.updateStatus()
        listener.dateChange.add(self)
    def heightSpinChanged(self, spin):
        v = spin.get_value()
        self.set_property('height-request', v)
        ui.wcalHeight = v
    def updateVars(self):
        CustomizableCalBox.updateVars(self)
        ui.wcalItems = self.getItemsData()
    def confStr(self):
        text = CustomizableCalBox.confStr(self)
        text += 'ui.wcalHeight=%s\n'%repr(ui.wcalHeight)
        text += 'ui.wcalItems=%s\n'%repr(ui.wcalItems)
        return text
    def updateStatus(self):
        self.status = getCurrentWeekStatus()
    def onDateChange(self, *a, **kw):
        CustomizableCalBox.onDateChange(self, *a, **kw)
        self.updateStatus()
        self.queue_draw()
        for item in self.items:
            item.queue_draw()
    def gotoJd(self, jd):
        ui.gotoJd(jd)
        self.onDateChange()
    def jdPlus(self, p):
        ui.jdPlus(p)
        self.onDateChange()
    def goBackward4(self, obj=None):
        self.jdPlus(-28)
    def goBackward(self, obj=None):
        self.jdPlus(-7)
    goToday = lambda self, obj=None: self.gotoJd(core.getCurrentJd())
    def goForward(self, obj=None):
        self.jdPlus(7)
    def goForward4(self, obj=None):
        self.jdPlus(28)
    def buttonPress(self, widget, event):
        b = event.button
        #(x, y, mask) = event.window.get_pointer()
        (x, y) = self.get_pointer()
        #y += 10
        i = int(event.y * 7.0 / self.allocation.height)
        cell = self.status[i]
        self.gotoJd(cell.jd)
        if event.type==gdk._2BUTTON_PRESS:
            self.emit('2button-press')
        if b == 3:
            self.emit('popup-menu-cell', event.time, x, y)
        return True
    def keyPress(self, arg, event):
        kname = gdk.keyval_name(event.keyval).lower()
        if kname=='up':
            self.jdPlus(-1)
        elif kname=='down':
            self.jdPlus(1)
        elif kname in ('space', 'home'):
            self.goToday()
        elif kname=='end':
            self.gotoJd(self.status[-1].jd)
        elif kname=='page_up':
            self.jdPlus(-7)
        elif kname=='page_down':
            self.jdPlus(7)
        #elif kname=='menu':
        #    self.emit('popup-menu-cell', event.time, *self.getCellPos())
        #elif kname in ('f10', 'm'):
        #    if event.state & gdk.SHIFT_MASK:
        #        # Simulate right click (key beside Right-Ctrl)
        #        self.emit('popup-menu-cell', event.time, *self.getCellPos())
        #    else:
        #        self.emit('popup-menu-main', event.time, *self.getMainMenuPos())
        else:
            return False
        return True
    def scroll(self, widget, event):
        d = event.direction.value_nick
        if d=='up':
            self.jdPlus(-1)
        elif d=='down':
            self.jdPlus(1)
        else:
            return False
    def onCurrentDateChange(self, gdate):
        self.queue_draw()

    


for cls in (
    Column,
    DaysOfMonthColumnGroup,
    WeekCal,
):
    gobject.type_register(cls)
    cls.registerSignals()
    





cls = WeekCal
gobject.signal_new('popup-menu-cell', cls, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [int, int, int])
gobject.signal_new('2button-press', cls, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])



if __name__=='__main__':
    win = gtk.Dialog()
    cal = WeekCal()
    win.add_events(
        gdk.POINTER_MOTION_MASK | gdk.FOCUS_CHANGE_MASK | gdk.BUTTON_MOTION_MASK |
        gdk.BUTTON_PRESS_MASK | gdk.BUTTON_RELEASE_MASK | gdk.SCROLL_MASK |
        gdk.KEY_PRESS_MASK | gdk.VISIBILITY_NOTIFY_MASK | gdk.EXPOSURE_MASK
    )
    win.vbox.pack_start(cal, 1, 1)
    win.vbox.show()
    win.resize(600, 400)
    win.run()











