#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_man
from scal2.ui_gtk.mywidgets.multi_spin_button import TimeButton
import gtk
from gtk import gdk

class RuleWidget(gtk.HBox):
    def __init__(self, rule):
        self.rule = rule
        ###
        gtk.HBox.__init__(self)
        spin = gtk.SpinButton()
        spin.set_increments(1, 10)
        spin.set_range(0, 999)
        spin.set_direction(gtk.TEXT_DIR_LTR)
        self.pack_start(spin, 0, 0)
        self.spin = spin
        ##
        self.pack_start(gtk.Label(' '+_('days and')+' '), 0, 0)
        tbox = TimeButton()
        self.pack_start(tbox, 0, 0)
        self.tbox = tbox
        ##
        self.updateWidget()
    def updateWidget(self):
        self.spin.set_value(self.rule.cycleDays)   
        self.tbox.set_time(self.rule.cycleExtraTime)
    def updateVars(self):
        self.rule.cycleDays = self.spin.get_value()
        self.rule.cycleExtraTime = self.tbox.get_time()

