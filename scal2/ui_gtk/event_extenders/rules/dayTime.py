#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale import tr as _

from scal2 import event_man
from scal2.ui_gtk.mywidgets.multi_spin_box import DateBox, TimeBox
import gtk
from gtk import gdk

class DayTimeEventRuleWidget(TimeBox):
    def __init__(self, rule):
        self.rule = rule
        TimeBox.__init__(self)
        self.updateWidget()
    def updateWidget(self):
        self.set_time(self.rule.dayTime)
    def updateVars(self):
        (self.rule.hour, self.rule.minute, self.rule.second) = tbox.get_time()


event_man.DayTimeEventRule.WidgetClass = DayTimeEventRuleWidget


