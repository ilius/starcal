#!/usr/bin/env python
# -*- coding: utf-8 -*-

from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_man
import gtk
from gtk import gdk

class MonthEventRuleWidget(gtk.ComboBox):
    def __init__(self, rule):
        self.rule = rule
        ###
        ls = gtk.ListStore(str)
        gtk.ComboBox.__init__(self, ls)
        ###
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 0)
        ###
        for m in core.modules[rule.getMode()].monthName:
            self.append_text(_(m))
        ###
        self.updateWidget()
    def updateWidget(self):
        self.set_active(self.rule.month-1)
    def updateVars(self):
        self.rule.month = self.get_active() + 1


event_man.MonthEventRule.WidgetClass = MonthEventRuleWidget


