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
        gtk.SpinButton.__init__(self)
        self.set_increments(1, 10)
        self.set_range(0, 100000)
        self.updateWidget()
    def updateWidget(self):
        self.set_value(self.rule.cycleDays)
    def updateVars(self):
        self.rule.cycleDays = self.get_value()
    
