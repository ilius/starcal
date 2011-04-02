# -*- coding: utf-8 -*-
#        
# Copyright (C) 2009    Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

#import time
#print time.time(), __file__

import os, sys

from scal2.locale import tr as _

from scal2 import core
from scal2.core import convert, getMonthName, getMonthLen

from scal2 import ui
from scal2.ui_gtk.mywidgets.multi_spin_box import DateBox

import gtk, gobject
from gtk import gdk

class SelectDateDialog(gtk.Dialog):
    def __init__(self):
        gtk.Dialog.__init__(self, title=_('Select Date...'))
        self.set_has_separator(False)
        #self.set_skip_taskbar_hint(True)
        self.connect('delete-event', self.hideMe)
        ###### Reciving dropped day!
        self.drag_dest_set(gdk.MODIFIER_MASK,\
            (('a', 0, 0),), gdk.ACTION_COPY)
        self.drag_dest_add_text_targets()
        self.connect('drag-data-received', self.dragRec)
        ######
        hb0 = gtk.HBox(spacing=4)
        hb0.pack_start(gtk.Label(_('Date Mode')), 0, 0)
        combo = gtk.combo_box_new_text()
        for m in core.modules:
            combo.append_text(_(m.desc))
        self.mode = core.primaryMode
        combo.set_active(core.primaryMode)
        hb0.pack_start(combo, 0, 0)
        self.vbox.pack_start(hb0, 0, 0)
        #######################
        hb1 = gtk.HBox(spacing=4)
        hb1.pack_start(gtk.Label(_('Year')), 0, 0)
        spinY = gtk.SpinButton()
        spinY.set_increments(1, 10)
        spinY.set_range(0, 10000)
        spinY.set_width_chars(5)
        spinY.set_direction(gtk.TEXT_DIR_LTR)
        hb1.pack_start(spinY, 0, 0)
        hb1.pack_start(gtk.Label(_('Month')), 0, 0)
        combo2 = gtk.combo_box_new_text()
        module = core.modules[core.primaryMode]
        for i in xrange(12):
            combo2.append_text(_(module.getMonthName(i+1, None)))## year=None means all months
        combo2.set_active(0)
        hb1.pack_start(combo2, 0, 0)
        hb1.pack_start(gtk.Label(_('Day')), 0, 0)
        spinD = gtk.SpinButton()
        spinD.set_increments(1, 5)
        spinD.set_range(1, 31)
        spinD.set_width_chars(3)
        spinD.set_direction(gtk.TEXT_DIR_LTR)
        hb1.pack_start(spinD, 0, 0)
        rb1 = gtk.RadioButton()
        rb1.num = 1
        hb1i = gtk.HBox(spacing=5)
        hb1i.pack_start(rb1, 0, 0)
        hb1i.pack_start(hb1, 0, 0)
        self.vbox.pack_start(hb1i, 0, 0)
        ########
        hb2 = gtk.HBox(spacing=4)
        hb2.pack_start(gtk.Label('yyyy/mm/dd'), 0, 0)
        dbox = DateBox(lang=core.langSh, hist_size=16) ## lang='fa' | 'fa_IR.UTF-8' ????????
        hb2.pack_start(dbox, 0, 0)
        rb2 = gtk.RadioButton()
        rb2.num = 2
        rb2.set_group(rb1)
        hb2i = gtk.HBox(spacing=5)
        hb2i.pack_start(rb2, 0, 0)
        hb2i.pack_start(hb2, 0, 0)
        self.vbox.pack_start(hb2i, 0, 0)
        #######
        canB = self.add_button(gtk.STOCK_CANCEL, 2)
        okB = self.add_button(gtk.STOCK_OK, 1)
        if ui.autoLocale:
            okB.set_label(_('_OK'))
            okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK,gtk.ICON_SIZE_BUTTON))
            canB.set_label(_('_Cancel'))
            canB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL,gtk.ICON_SIZE_BUTTON))
        #######
        self.comboMode = combo
        self.spinY = spinY
        self.comboMonth = combo2
        self.spinD = spinD
        self.dbox = dbox
        self.radio1 = rb1
        self.radio2 = rb2
        self.hbox1 = hb1
        self.hbox2 = hb2
        #######
        combo.connect ('changed', self.comboModeChanged)
        self.comboMonthConn = combo2.connect('changed', self.comboMonthChanged)
        spinY.connect ('changed', self.comboMonthChanged)
        rb1.connect_after('clicked', self.radioChanged)
        rb2.connect_after('clicked', self.radioChanged)
        dbox.connect('activate', self.ok)
        okB.connect('clicked', self.ok)
        canB.connect('clicked', self.hideMe)
        self.radioChanged()
        #######
        self.vbox.show_all()
    def dragRec(self, obj, context, x, y, selection, target_id, etime):
        text = selection.get_text()
        if text==None:
            return
        date = core.parseDroppedDate(text)
        if date==None:
            print 'selectDateDialog: dropped text "%s"'%text
            return
        print 'selectDateDialog: dropped date: %d/%d/%d'%date
        mode = self.comboMode.get_active()
        if mode!=ui.dragGetMode:
            date = convert(date[0], date[1], date[2], ui.dragGetMode, mode)
        (y, m, d) = date
        self.spinY.set_value(y)
        self.comboMonth.set_active(m-1)
        self.spinD.set_value(d)
        self.dbox.set_date((y, m, d))
        self.dbox.add_history()
        return True
    def show(self):
        ## Show a window that ask the date and set on the calendar
        mode = core.primaryMode
        (y, m, d) = ui.cell.dates[mode]
        self.setMode(mode)
        self.set(y, m, d)
        self.present()
    def hideMe(self, widget, event=None):
        self.hide()
        return True
    def set(self, y, m, d):
        self.spinY.set_value(y)
        self.comboMonth.set_active(m-1)
        self.spinD.set_value(d)
        self.dbox.set_date((y, m, d))
        self.dbox.add_history()
    def setMode(self, mode):
        self.mode = mode
        module = core.modules[mode]
        combo = self.comboMonth
        for i in xrange(len(combo.get_model())):
            combo.remove_text(0)
        for i in xrange(12):
            combo.append_text(_(module.getMonthName(i+1)))
        self.comboMode.set_active(mode)
        self.spinD.set_range(1, core.modules[mode].maxMonthLen)
        self.dbox.maxs = (9999, 12, module.maxMonthLen)
    def comboModeChanged(self, widget=None):
        pMode = self.mode
        pDate = self.get()
        mode = self.comboMode.get_active()
        module = core.modules[mode]
        if pDate==None:
            (y, m, d) = ui.cell.dates[mode]
        else:
            (y0, m0, d0) = pDate
            (y, m, d) = convert(y0, m0, d0, pMode, mode)
        combo = self.comboMonth
        self.comboMonth.disconnect(self.comboMonthConn)
        for i in xrange(len(combo.get_model())):
            combo.remove_text(0)
        for i in xrange(12):
            combo.append_text(_(module.getMonthName(i+1)))
        self.comboMonthConn = self.comboMonth.connect('changed', self.comboMonthChanged)
        self.spinD.set_range(1, module.maxMonthLen)
        self.dbox.maxs = (9999, 12, module.maxMonthLen)
        self.set(y, m, d)
        self.mode = mode
    def comboMonthChanged(self, widget=None):
        self.spinD.set_range(1, getMonthLen(
            int(self.spinY.get_value()),
            self.comboMonth.get_active() + 1,
            self.mode,
        ))
    def get(self):
        mode = self.comboMode.get_active()
        if self.radio1.get_active():
            y0 = int(self.spinY.get_value())
            m0 = self.comboMonth.get_active() + 1
            d0 = int(self.spinD.get_value())
        elif self.radio2.get_active():
            (y0, m0, d0) = self.dbox.get_date()
        return (y0, m0, d0)
    def ok(self, widget):
        mode = self.comboMode.get_active()
        if mode==None:
            return
        get = self.get()
        if get==None:
            return
        (y0, m0, d0) = get
        if mode==core.primaryMode:
            (y, m, d) = (y0, m0, d0)
        else:
            (y, m, d) = convert(y0, m0, d0, mode, core.primaryMode)
        if not core.validDate(mode, y, m, d):
            print 'bad date: %s'%dateStr(mode, y, m, d)
            return
        self.emit('response-date', y, m, d)
        self.hide()
        self.dbox.add_history((y0, m0, d0))
        #self.dbox.add_history((y, m, d))
    def radioChanged(self, widget=None):
        if self.radio1.get_active():
            self.hbox1.set_sensitive(True)
            self.hbox2.set_sensitive(False)
        else:
            self.hbox1.set_sensitive(False)
            self.hbox2.set_sensitive(True)




gobject.type_register(SelectDateDialog)
gobject.signal_new('response-date', SelectDateDialog, gobject.SIGNAL_RUN_LAST, 
    gobject.TYPE_NONE, [int, int, int])



