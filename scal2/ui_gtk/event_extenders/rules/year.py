#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_man
import gtk
from gtk import gdk

class RuleWidget(gtk.SpinButton):
    def __init__(self, rule):
        self.rule = rule
        ###
        gtk.SpinButton.__init__(self)
        self.set_increments(1, 10)
        self.set_range(0, 9999)
        self.set_width_chars(4)
        ###
        self.updateWidget()
    def updateWidget(self):
        self.set_value(self.rule.year)
    getYear = lambda self: int(self.get_value())
    def updateVars(self):
        self.rule.year = self.getYear()
    def changeMode(self, mode):
        curMode = self.rule.getMode()
        if mode!=curMode:
            self.set_value(core.convert(self.getYear(), 7, 1, curMode, mode)[0])
            self.updateVars()

