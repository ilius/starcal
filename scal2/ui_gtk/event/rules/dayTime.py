#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_lib
from scal2.ui_gtk.mywidgets.multi_spin_button import TimeButton
import gtk
from gtk import gdk

class RuleWidget(TimeButton):
    def __init__(self, rule):
        self.rule = rule
        TimeButton.__init__(self)
    def updateWidget(self):
        self.set_value(self.rule.dayTime)
    def updateVars(self):
        self.rule.dayTime = self.get_value()


