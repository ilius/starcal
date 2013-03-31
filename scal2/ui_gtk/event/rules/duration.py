#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_lib
from scal2.ui_gtk.mywidgets.multi_spin_button import DateButton, TimeButton
from scal2.ui_gtk.event import common
import gtk
from gtk import gdk

class RuleWidget(common.DurationInputBox):
    def __init__(self, rule):
        self.rule = rule
        common.DurationInputBox.__init__(self)
    def updateWidget(self):
        self.setDuration(self.rule.value, self.rule.unit)
    def updateVars(self):
        (self.rule.value, self.rule.unit) = self.getDuration()

