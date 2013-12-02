# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2012 Saeed Rasooli <saeed.gnu@gmail.com>
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

from time import time as now

from scal2.cal_types import calTypes
from scal2 import core

from scal2 import locale_man
from scal2.locale_man import getMonthName, rtl
from scal2.locale_man import tr as _


from scal2 import ui

import gobject
from gobject import timeout_add

import gtk
from gtk import gdk

from scal2.ui_gtk.decorators import *
from scal2.ui_gtk.utils import set_tooltip
from scal2.ui_gtk.drawing import newTextLayout
from scal2.ui_gtk.mywidgets.button import ConButton
from scal2.ui_gtk import gtk_ud as ud
from scal2.ui_gtk.customize import CustomizableCalObj


@registerSignals
class MonthLabel(gtk.EventBox, ud.IntegratedCalObj):
    highlightColor = gdk.Color(45000, 45000, 45000)
    getItemStr = lambda self, i: _(i+1, fillZero=2)
    getActiveStr = lambda self, s: '<span color="%s">%s</span>'%(ui.menuActiveLabelColor, s)
    #getActiveStr = lambda self, s: '<b>%s</b>'%s
    def __init__(self, mode, active=0):
        gtk.EventBox.__init__(self)
        #self.set_border_width(1)#???????????
        self.initVars()
        self.mode = mode
        s = _(getMonthName(self.mode, active+1))
        if ui.boldYmLabel:
            s = '<b>%s</b>'%s
        self.label = gtk.Label(s)
        self.label.set_use_markup(True)
        self.add(self.label)
        menu = gtk.Menu()
        menu.set_border_width(0)
        menuLabels = []
        for i in range(12):
            if ui.monthRMenuNum:
                text = '%s: %s'%(self.getItemStr(i), _(getMonthName(self.mode, i+1)))
            else:
                text = _(getMonthName(self.mode, i+1))
            if i==active:
                text = self.getActiveStr(text)
            label = gtk.Label(text)
            #label.set_justify(gtk.JUSTIFY_LEFT)
            label.set_alignment(0, 0.5)
            label.set_use_markup(True)
            item = gtk.MenuItem()
            item.set_right_justified(True) ##?????????
            item.add(label)
            item.connect('activate', self.itemActivate, i)
            menu.append(item)
            menuLabels.append(label)
        menu.show_all()
        self.menu = menu
        self.menuLabels = menuLabels
        self.connect('button-press-event', self.buttonPress)
        self.active = active
        self.setActive(active)
        ##########
        #self.menu.connect('map', lambda obj: self.drag_highlight())
        #self.menu.connect('unmap', lambda obj: self.drag_unhighlight())
        #########
        self.connect('enter-notify-event', self.highlight)
        self.connect('leave-notify-event', self.unhighlight)
        ####### update menu width
        if rtl:
            get_menu_pos = lambda widget: (ud.screenW, 0, True)
            menu.popup(None, None, get_menu_pos, 3, 0)
            menu.hide()
    def setActive(self, active):
    ## (Performance) update menu here, or make menu entirly before popup ????????????????
        s = getMonthName(self.mode, active+1)
        s2 = getMonthName(self.mode, self.active+1)
        if ui.monthRMenuNum:
            self.menuLabels[self.active].set_label(
                '%s: %s'%(
                    self.getItemStr(self.active),
                    s2,
                )
            )
            self.menuLabels[active].set_label(self.getActiveStr('%s: %s'%(self.getItemStr(active), s)))
        else:
            self.menuLabels[self.active].set_label(s2)
            self.menuLabels[active].set_label(self.getActiveStr(s))
        if ui.boldYmLabel:
            self.label.set_label('<b>%s</b>'%s)
        else:
            self.label.set_label(s)
        self.active = active
    def changeMode(self, mode):
        self.mode = mode
        if ui.boldYmLabel:
            self.label.set_label('<b>%s</b>'%getMonthName(self.mode, self.active+1))
        else:
            self.label.set_label(getMonthName(self.mode, self.active+1))
        for i in range(12):
            if ui.monthRMenuNum:
                s = '%s: %s'%(self.getItemStr(i), getMonthName(self.mode, i+1))
            else:
                s = getMonthName(self.mode, i+1)
            if i==self.active:
                s = self.getActiveStr(s)
            self.menuLabels[i].set_label(s)
    def itemActivate(self, item, index):
        y, m, d = ui.cell.dates[self.mode]
        m = index + 1
        ui.changeDate(y, m, d, self.mode)
        self.onDateChange()
    def buttonPress(self, widget, event):
        if event.button==3:
            x, y = self.get_window().get_origin()
            y += self.allocation.height
            if rtl:
                mw = self.menu.allocation.width
                #print('menu.allocation.width', mw)
                if mw>1:
                    x -= (mw - self.allocation.width)
            #x -= 7 ## ????????? because of menu padding
            self.menu.popup(None, None, lambda widget: (x, y, True), event.button, event.time)
            ui.updateFocusTime()
            return True
        else:
            return False
    def highlight(self, widget=None, event=None):
        #self.drag_highlight()
        if self.window==None:
            return
        cr = self.get_window().cairo_create()
        cr.set_source_color(self.highlightColor)
        #print(tuple(self.allocation), tuple(self.label.allocation))
        x, y, w, h = self.allocation
        cr.rectangle(0, 0, w, 1)
        cr.fill()
        cr.rectangle(0, h-1, w, 1)
        cr.fill()
        cr.rectangle(0, 0, 1, h)
        cr.fill()
        cr.rectangle(w-1, 0, 1, h)
        cr.fill()
        cr.clip()
    def unhighlight(self, widget=None, event=None):
        #self.drag_unhighlight()
        if self.window==None:
            return
        x, y, w, h = self.allocation
        self.get_window().clear_area(0, 0, w, 1)
        self.get_window().clear_area(0, h-1, w, 1)
        self.get_window().clear_area(0, 0, 1, h)
        self.get_window().clear_area(w-1, 0, 1, h)
    def onDateChange(self, *a, **ka):
        ud.IntegratedCalObj.onDateChange(self, *a, **ka)
        self.setActive(ui.cell.dates[self.mode][1]-1)



@registerSignals
class IntLabel(gtk.EventBox):
    highlightColor = gdk.Color(45000, 45000, 45000)
    #getActiveStr = lambda self, s: '<b>%s</b>'%s
    getActiveStr = lambda self, s: '<span color="%s">%s</span>'%(ui.menuActiveLabelColor, s)
    signals = [
        ('changed', [int]),
    ]
    def __init__(self, height=9, active=0):
        gtk.EventBox.__init__(self)
        #self.set_border_width(1)#???????????
        self.height = height
        #self.delay = delay
        if ui.boldYmLabel:
            s = '<b>%s</b>'%_(active)
        else:
            s = _(active)
        self.label = gtk.Label(s)
        self.label.set_use_markup(True)
        self.add(self.label)
        menu = gtk.Menu()
        ##########
        item = gtk.MenuItem()
        arrow = gtk.Arrow(gtk.ARROW_UP, gtk.SHADOW_IN)
        item.add(arrow)
        arrow.set_property('height-request', 10)
        #item.set_border_width(0)
        #item.set_property('height-request', 10)
        #print(item.style_get_property('horizontal-padding') ## OK)
        ###???????????????????????????????????
        #item.config('horizontal-padding'=0)
        #style = item.get_style()
        #style.set_property('horizontal-padding', 0)
        #item.set_style(style)
        menu.append(item)
        item.connect('select', self.arrowSelect, -1)
        item.connect('deselect', self.arrowDeselect)
        item.connect('activate', lambda wid: False)
        ##########
        menuLabels = []
        for i in range(height):
            label = gtk.Label()
            label.set_use_markup(True)
            item = gtk.MenuItem()
            item.add(label)
            item.connect('activate', self.itemActivate, i)
            menu.append(item)
            menuLabels.append(label)
        menu.connect('scroll-event', self.menuScroll)
        ##########
        item = gtk.MenuItem()
        arrow = gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_IN)
        arrow.set_property('height-request', 10)
        item.add(arrow)
        menu.append(item)
        item.connect('select', self.arrowSelect, 1)
        item.connect('deselect', self.arrowDeselect)
        ##########
        menu.show_all()
        self.menu = menu
        self.menuLabels = menuLabels
        self.connect('button-press-event', self.buttonPress)
        self.active = active
        self.setActive(active)
        self.start = 0
        self.remain = 0
        self.ymPressTime = 0
        self.etime = 0
        self.step = 0
        ##########
        #self.menu.connect('map', lambda obj: self.drag_highlight())
        #self.menu.connect('unmap', lambda obj: self.drag_unhighlight())
        #########
        #self.modify_base(gtk.STATE_NORMAL, gdk.Color(-1, 0, 0))#??????????
        self.connect('enter-notify-event', self.highlight)
        self.connect('leave-notify-event', self.unhighlight)
    def setActive(self, active):
        if ui.boldYmLabel:
            self.label.set_label('<b>%s</b>'%_(active))
        else:
            self.label.set_label(_(active))
        self.active = active
    def updateMenu(self, start=None):
        if start==None:
            start = self.active - self.height/2
        self.start = start
        for i in range(self.height):
            if start+i==self.active:
                self.menuLabels[i].set_label(self.getActiveStr(_(start+i)))
            else:
                self.menuLabels[i].set_label(_(start+i))
    def itemActivate(self, widget, item):
        self.setActive(self.start+item)
        self.emit('changed', self.start+item)
    def buttonPress(self, widget, event):
        if event.button==3:
            self.updateMenu()
            x, y = self.get_window().get_origin()
            y += self.allocation.height
            x -= 7 ## ????????? because of menu padding
            self.menu.popup(None, None, lambda widget: (x, y, True), event.button, event.time)
            ui.updateFocusTime()
            return True
        else:
            return False
    def arrowSelect(self, item, plus):
        self.remain = plus
        timeout_add(int(ui.labelMenuDelay*1000), self.arrowRemain, plus)
    def arrowDeselect(self, item):
        self.remain = 0
    def arrowRemain(self, plus):
        t = now()
        #print(t-self.etime)
        if self.remain==plus:
            if t-self.etime<ui.labelMenuDelay-0.02:
                if self.step>1:
                    self.step = 0
                    return False
                else:
                    self.step += 1
                    self.etime = t #??????????
                    return True
            else:
                self.updateMenu(self.start+plus)
                self.etime = t
                return True
        else:
            return False
    def menuScroll(self, widget, event):
        d = event.direction.value_nick
        if d=='up':
            self.updateMenu(self.start-1)
        elif d=='down':
            self.updateMenu(self.start+1)
        else:
            return False
    def highlight(self, widget=None, event=None):
        #self.drag_highlight()
        if self.window==None:
            return
        cr = self.get_window().cairo_create()
        cr.set_source_color(self.highlightColor)
        x, y, w, h = self.allocation
        cr.rectangle(0, 0, w, 1)
        cr.fill()
        cr.rectangle(0, h-1, w, 1)
        cr.fill()
        cr.rectangle(0, 0, 1, h)
        cr.fill()
        cr.rectangle(w-1, 0, 1, h)
        cr.fill()
        cr.clip()
    def unhighlight(self, widget=None, event=None):
        #self.drag_unhighlight()
        if self.window==None:
            return
        x, y, w, h = self.allocation
        self.get_window().clear_area(0, 0, w, 1)
        self.get_window().clear_area(0, h-1, w, 1)
        self.get_window().clear_area(0, 0, 1, h)
        self.get_window().clear_area(w-1, 0, 1, h)


@registerSignals
class YearLabel(IntLabel, ud.IntegratedCalObj):
    signals = ud.IntegratedCalObj.signals
    def __init__(self, mode, **kwargs):
        IntLabel.__init__(self, **kwargs)
        self.initVars()
        self.mode = mode
        self.connect('changed', self.onChanged)
    def onChanged(self, label, item):
        mode = self.mode
        y, m, d = ui.cell.dates[mode]
        ui.changeDate(item, m, d, mode)
        self.onDateChange()
    def changeMode(self, mode):
        self.mode = mode
        #self.onDateChange()
    def onDateChange(self, *a, **ka):
        ud.IntegratedCalObj.onDateChange(self, *a, **ka)
        self.setActive(ui.cell.dates[self.mode][0])


def newSmallNoFocusButton(stock, func, tooltip=''):
    arrow = ConButton()
    arrow.set_relief(2)
    arrow.set_can_focus(False)
    arrow.set_image(gtk.image_new_from_stock(stock, gtk.ICON_SIZE_SMALL_TOOLBAR))
    arrow.connect('con-clicked', func)
    if tooltip:
        set_tooltip(arrow, tooltip)
    return arrow

class YearLabelButtonBox(gtk.HBox):
    def __init__(self, mode, **kwargs):
        gtk.HBox.__init__(self)
        ###
        self.pack_start(
            newSmallNoFocusButton(gtk.STOCK_REMOVE, self.prevClicked, _('Previous Year')),
            0,
            0,
        )
        ###
        self.label = YearLabel(mode, **kwargs)
        self.pack_start(self.label, 0, 0)
        ###
        self.pack_start(
            newSmallNoFocusButton(gtk.STOCK_ADD, self.nextClicked, _('Next Year')),
            0,
            0,
        )
    def prevClicked(self, button):
        ui.yearPlus(-1)
        self.label.onDateChange()
    def nextClicked(self, button):
        ui.yearPlus(1)
        self.label.onDateChange()
    changeMode = lambda self, mode: self.label.changeMode(mode)

class MonthLabelButtonBox(gtk.HBox):
    def __init__(self, mode, **kwargs):
        gtk.HBox.__init__(self)
        ###
        self.pack_start(
            newSmallNoFocusButton(gtk.STOCK_REMOVE, self.prevClicked, _('Previous Month')),
            0,
            0,
        )
        ###
        self.label = MonthLabel(mode, **kwargs)
        self.pack_start(self.label, 0, 0)
        ###
        self.pack_start(
            newSmallNoFocusButton(gtk.STOCK_ADD, self.nextClicked, _('Next Month')),
            0,
            0,
        )
    def prevClicked(self, button):
        ui.monthPlus(-1)
        self.label.onDateChange()
    def nextClicked(self, button):
        ui.monthPlus(1)
        self.label.onDateChange()
    changeMode = lambda self, mode: self.label.changeMode(mode)


@registerSignals
class YearMonthLabelBox(gtk.HBox, CustomizableCalObj):
    _name = 'labelBox'
    desc = _('Year & Month Labels')
    def __init__(self):
        gtk.HBox.__init__(self)
        self.initVars()
        #self.set_border_width(2)
    def onConfigChange(self, *a, **kw):
        CustomizableCalObj.onConfigChange(self, *a, **kw)
        #####
        for child in self.get_children():
            child.destroy()
        ###
        monthLabels = []
        mode = core.primaryMode
        ##
        box = YearLabelButtonBox(mode)
        self.pack_start(box, 0, 0)
        self.appendItem(box.label)
        ##
        self.pack_start(gtk.VSeparator(), 1, 1)
        ##
        box = MonthLabelButtonBox(mode)
        self.pack_start(box, 0, 0)
        self.appendItem(box.label)
        monthLabels.append(box.label)
        ####
        for i, mode in list(enumerate(calTypes.active))[1:]:
            self.pack_start(gtk.VSeparator(), 1, 1)
            label = YearLabel(mode)
            self.pack_start(label, 0, 0)
            self.appendItem(label)
            ###############
            label = gtk.Label('')
            label.set_property('width-request', 5)
            self.pack_start(label, 0, 0)
            ###############
            label = MonthLabel(mode)
            self.pack_start(label, 0, 0)
            monthLabels.append(label)
            self.appendItem(label)
        ####
        ## updateTextWidth
        lay = newTextLayout(self)
        for label in monthLabels:
            wm = 0
            for m in range(12):
                name = getMonthName(label.mode, m)
                if ui.boldYmLabel:
                    lay.set_markup('<b>%s</b>'%name)
                else:
                    lay.set_text(name) ## OR lay.set_markup
                w = lay.get_pixel_size()[0]
                if w > wm:
                    wm = w
            label.set_property('width-request', wm)
        #####
        self.show_all()
        #####
        self.onDateChange()


if __name__=='__main__':
    win = gtk.Dialog()
    box = YearMonthLabelBox()
    win.add_events(
        gdk.POINTER_MOTION_MASK | gdk.FOCUS_CHANGE_MASK | gdk.BUTTON_MOTION_MASK |
        gdk.BUTTON_PRESS_MASK | gdk.BUTTON_RELEASE_MASK | gdk.SCROLL_MASK |
        gdk.KEY_PRESS_MASK | gdk.VISIBILITY_NOTIFY_MASK | gdk.EXPOSURE_MASK
    )
    win.vbox.pack_start(box, 1, 1)
    win.vbox.show_all()
    win.resize(600, 400)
    box.onConfigChange()
    win.run()


