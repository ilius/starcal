#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_lib
from scal2.ui_gtk.mywidgets.multi_spin_button import DateButton, TimeButton
import gtk
from gtk import gdk

class RuleWidget(gtk.HBox):
    def __init__(self, rule):
        self.rule = rule
        ###
        gtk.HBox.__init__(self)
        ###
        self.dateInput = DateButton()
        self.pack_start(self.dateInput, 0, 0)
        ###
        self.pack_start(gtk.Label('   '+_('Time')), 0, 0)
        self.timeInput = TimeButton()
        self.pack_start(self.timeInput, 0, 0)
    def updateWidget(self):
        self.dateInput.set_value(self.rule.date)
        self.timeInput.set_value(self.rule.time)
    def updateVars(self):
        self.rule.date = self.dateInput.get_value()
        self.rule.time = self.timeInput.get_value()
    def changeMode(self, mode):
        curMode = self.rule.getMode()
        if mode!=curMode:
            y, m, d = self.dateInput.get_value()
            self.dateInput.set_value(core.convert(y, m, d, curMode, mode))
