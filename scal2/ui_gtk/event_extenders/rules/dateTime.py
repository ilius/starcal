#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale import tr as _

from scal2 import event_man
from scal2.ui_gtk.mywidgets.multi_spin_button import DateButton, TimeButton
import gtk
from gtk import gdk

class DateTimeEventRuleWidget(gtk.HBox):
    def __init__(self, rule):
        self.rule = rule
        ###
        gtk.HBox.__init__(self)
        ###
        dbox = DateButton()
        self.pack_start(dbox, 0, 0)
        ###
        self.pack_start(gtk.Label('   '+_('Time')), 0, 0)
        tbox = TimeButton()
        self.pack_start(tbox, 0, 0)
        ###
        self.dbox = dbox
        self.tbox = tbox
        self.updateWidget()
    def updateWidget(self):
        self.dbox.set_date(self.rule.date)
        self.tbox.set_time(self.rule.time)
    def updateVars(self):
        self.rule.date = self.dbox.get_date()
        self.rule.time = self.tbox.get_time()
    def changeMode(self, mode):
        curMode = self.rule.getMode()
        if mode!=curMode:
            (y, m, d) = self.dbox.get_date()
            self.dbox.set_date(core.convert(y, m, d, curMode, mode))
            self.updateVars()


event_man.StartEventRule.WidgetClass = DateTimeEventRuleWidget
event_man.EndEventRule.WidgetClass = DateTimeEventRuleWidget



