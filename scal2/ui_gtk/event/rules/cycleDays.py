#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_man
import gtk
from gtk import gdk

from scal2.ui_gtk.mywidgets.multi_spin_button import IntSpinButton

class RuleWidget(IntSpinButton):
    def __init__(self, rule):
        self.rule = rule
        IntSpinButton.__init__(self, 0, 999999)
    def updateWidget(self):
        self.set_value(self.rule.cycleDays)
    def updateVars(self):
        self.rule.cycleDays = self.get_value()

