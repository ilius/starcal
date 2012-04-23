#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_man
import gtk
from gtk import gdk

from scal2.ui_gtk.event import common


class EventWidget(common.EventWidget):
    def __init__(self, event):## FIXME
        common.EventWidget.__init__(self, event)
        ################
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Month')), 0, 0)
        self.monthCombo = gtk.combo_box_new_text()
        hbox.pack_start(self.monthCombo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        #self.pack_start(hbox, 0, 0)
        ###
        #hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Day')), 0, 0)
        spin = gtk.SpinButton()
        spin.set_increments(1, 10)
        spin.set_range(1, 31)
        spin.set_digits(0)
        spin.set_direction(gtk.TEXT_DIR_LTR)
        self.daySpin = spin
        hbox.pack_start(spin, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.pack_start(hbox, 0, 0)
        ####
        #self.filesBox = common.FilesBox(self.event)
        #self.pack_start(self.filesBox, 0, 0)
    def updateWidget(self):## FIXME
        common.EventWidget.updateWidget(self)
        self.monthCombo.set_active(self.event.getMonth()-1)
        self.daySpin.set_value(self.event.getDay())
    def updateVars(self):## FIXME
        common.EventWidget.updateVars(self)
        self.event.setMonth(self.monthCombo.get_active()+1)
        self.event.setDay(int(self.daySpin.get_value()))
    def modeComboChanged(self, obj=None):## overwrite method from common.EventWidget
        module = core.modules[self.modeCombo.get_active()]
        monthCombo = self.monthCombo
        active = monthCombo.get_active()
        for i in range(len(monthCombo.get_model())):
            monthCombo.remove_text(0)
        for i in range(12):
            monthCombo.append_text(_(module.getMonthName(i+1)))
        monthCombo.set_active(active)


