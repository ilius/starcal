# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Saeed Rasooli <saeed.gnu@gmail.com>
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

import os, sys

from scal2.locale_man import tr as _

from scal2.cal_types import calTypes
from scal2 import core
from scal2.core import convert, getMonthName

from scal2 import ui

import gtk, gobject
from gtk import gdk

from scal2.ui_gtk.decorators import *
from scal2.ui_gtk.mywidgets.multi_spin_button import DateButtonOption
from scal2.ui_gtk.mywidgets.ymd import YearMonthDayBox
from scal2.ui_gtk.utils import openWindow, dialog_add_button, DateTypeCombo



@registerSignals
class SelectDateDialog(gtk.Dialog):
    signals = [
        ('response-date', [int, int, int]),
    ]
    def __init__(self):
        gtk.Dialog.__init__(self, title=_('Select Date...'))
        self.set_has_separator(False)
        #self.set_skip_taskbar_hint(True)
        self.connect('delete-event', self.hideMe)
        self.mode = core.primaryMode
        ###### Reciving dropped day!
        self.drag_dest_set(gdk.MODIFIER_MASK,\
            (('a', 0, 0),), gdk.ACTION_COPY)
        self.drag_dest_add_text_targets()
        self.connect('drag-data-received', self.dragRec)
        ######
        hb0 = gtk.HBox(spacing=4)
        hb0.pack_start(gtk.Label(_('Date Mode')), 0, 0)
        combo = DateTypeCombo()
        combo.set_active(self.mode)
        hb0.pack_start(combo, 0, 0)
        self.vbox.pack_start(hb0, 0, 0)
        #######################
        hbox = gtk.HBox(spacing=5)
        rb1 = gtk.RadioButton()
        rb1.num = 1
        hbox.pack_start(rb1, 0, 0)
        self.ymdBox = YearMonthDayBox()
        hbox.pack_start(self.ymdBox, 0, 0)
        self.vbox.pack_start(hbox, 0, 0)
        ########
        hb2 = gtk.HBox(spacing=4)
        hb2.pack_start(gtk.Label('yyyy/mm/dd'), 0, 0)
        dateInput = DateButtonOption(hist_size=16)
        hb2.pack_start(dateInput, 0, 0)
        rb2 = gtk.RadioButton()
        rb2.num = 2
        rb2.set_group(rb1)
        hb2i = gtk.HBox(spacing=5)
        hb2i.pack_start(rb2, 0, 0)
        hb2i.pack_start(hb2, 0, 0)
        self.vbox.pack_start(hb2i, 0, 0)
        #######
        dialog_add_button(self, gtk.STOCK_CANCEL, _('_Cancel'), 2, self.hideMe)
        dialog_add_button(self, gtk.STOCK_OK, _('_OK'), 1, self.ok)
        #######
        self.comboMode = combo
        self.dateInput = dateInput
        self.radio1 = rb1
        self.radio2 = rb2
        self.hbox2 = hb2
        #######
        combo.connect ('changed', self.comboModeChanged)
        rb1.connect_after('clicked', self.radioChanged)
        rb2.connect_after('clicked', self.radioChanged)
        dateInput.connect('activate', self.ok)
        self.radioChanged()
        #######
        self.vbox.show_all()
    def dragRec(self, obj, context, x, y, selection, target_id, etime):
        text = selection.get_text()
        if text==None:
            return
        date = ui.parseDroppedDate(text)
        if date==None:
            print 'selectDateDialog: dropped text "%s"'%text
            return
        print 'selectDateDialog: dropped date: %d/%d/%d'%date
        mode = self.comboMode.get_active()
        if mode!=ui.dragGetMode:
            date = convert(date[0], date[1], date[2], ui.dragGetMode, mode)
        self.dateInput.set_value(date)
        self.dateInput.add_history()
        return True
    def show(self):
        ## Show a window that ask the date and set on the calendar
        mode = core.primaryMode
        y, m, d = ui.cell.dates[mode]
        self.set_mode(mode)
        self.set(y, m, d)
        openWindow(self)
    def hideMe(self, widget, event=None):
        self.hide()
        return True
    def set(self, y, m, d):
        self.ymdBox.set_value((y, m, d))
        self.dateInput.set_value((y, m, d))
        self.dateInput.add_history()
    def set_mode(self, mode):
        self.mode = mode
        module = calTypes[mode]
        self.comboMode.set_active(mode)
        self.ymdBox.set_mode(mode)
        self.dateInput.setMaxDay(module.maxMonthLen)
    def comboModeChanged(self, widget=None):
        pMode = self.mode
        pDate = self.get()
        mode = self.comboMode.get_active()
        module = calTypes[mode]
        if pDate==None:
            y, m, d = ui.cell.dates[mode]
        else:
            y0, m0, d0 = pDate
            y, m, d = convert(y0, m0, d0, pMode, mode)
        self.ymdBox.set_mode(mode)
        self.dateInput.setMaxDay(module.maxMonthLen)
        self.set(y, m, d)
        self.mode = mode
    def get(self):
        mode = self.comboMode.get_active()
        if self.radio1.get_active():
            y0, m0, d0 = self.ymdBox.get_value()
        elif self.radio2.get_active():
            y0, m0, d0 = self.dateInput.get_value()
        return (y0, m0, d0)
    def ok(self, widget):
        mode = self.comboMode.get_active()
        if mode==None:
            return
        get = self.get()
        if get==None:
            return
        y0, m0, d0 = get
        if mode==core.primaryMode:
            y, m, d = (y0, m0, d0)
        else:
            y, m, d = convert(y0, m0, d0, mode, core.primaryMode)
        if not core.validDate(mode, y, m, d):
            print 'bad date: %s'%dateStr(mode, y, m, d)
            return
        self.emit('response-date', y, m, d)
        self.hide()
        self.dateInput.set_value((y0, m0, d0))
        self.dateInput.add_history()
    def radioChanged(self, widget=None):
        if self.radio1.get_active():
            self.ymdBox.set_sensitive(True)
            self.hbox2.set_sensitive(False)
        else:
            self.ymdBox.set_sensitive(False)
            self.hbox2.set_sensitive(True)




