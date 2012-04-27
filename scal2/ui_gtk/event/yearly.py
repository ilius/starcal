#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.core import convert
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
        ###
        hbox = gtk.HBox()
        self.startYearCheck = gtk.CheckButton(_('Start Year'))
        hbox.pack_start(self.startYearCheck, 0, 0)
        spin = gtk.SpinButton()
        spin.set_increments(1, 10)
        spin.set_range(1, 9999)
        spin.set_digits(0)
        spin.set_direction(gtk.TEXT_DIR_LTR)
        self.startYearSpin = spin
        hbox.pack_start(spin, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.pack_start(hbox, 0, 0)
        self.startYearCheck.connect('clicked', self.startYearCheckClicked)
        ####
        #self.filesBox = common.FilesBox(self.event)
        #self.pack_start(self.filesBox, 0, 0)
    startYearCheckClicked = lambda self, obj=None: self.startYearSpin.set_sensitive(self.startYearCheck.get_active())
    def updateWidget(self):## FIXME
        common.EventWidget.updateWidget(self)
        self.monthCombo.set_active(self.event.getMonth()-1)
        self.daySpin.set_value(self.event.getDay())
        try:
            startRule = self.event['start']
        except:
            self.startYearCheck.set_active(False)
            self.startYearSpin.set_value(core.getSysDate(self.event.mode)[0])
        else:
            self.startYearCheck.set_active(True)
            self.startYearSpin.set_value(startRule.date[0])
        self.startYearCheckClicked()
    def updateVars(self):## FIXME
        common.EventWidget.updateVars(self)
        self.event.setMonth(self.monthCombo.get_active()+1)
        self.event.setDay(int(self.daySpin.get_value()))
        if self.startYearCheck.get_active():
            startRule = self.event.getAddRule('start')
            startRule.date = (self.startYearSpin.get_value(), 1, 1)
        else:
            try:
                del self.event['start']
            except KeyError:
                pass
    def modeComboChanged(self, obj=None):## overwrite method from common.EventWidget
        newMode = self.modeCombo.get_active()
        module = core.modules[newMode]
        monthCombo = self.monthCombo
        active = monthCombo.get_active()
        for i in range(len(monthCombo.get_model())):
            monthCombo.remove_text(0)
        for i in range(12):
            monthCombo.append_text(_(module.getMonthName(i+1)))
        #monthCombo.set_active(active)
        y2, m2, d2 = convert(
            int(self.startYearSpin.get_value()),
            active + 1,
            int(self.daySpin.get_value()),
            self.event.mode,
            newMode,
        )
        self.startYearSpin.set_value(y2)
        monthCombo.set_active(m2-1)
        self.daySpin.set_value(d2)
        self.event.mode = newMode
        


