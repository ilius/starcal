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
        self.set_range(1, 31)## FIXME
        self.set_width_chars(2)
        self.updateWidget()
    def updateWidget(self):
        self.set_value(self.rule.day)
    def updateVars(self):
        self.rule.day = int(self.get_value())


