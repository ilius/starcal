#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_man
from scal2.ui_gtk.mywidgets.multi_spin_button import DateButton, TimeButton
import gtk
from gtk import gdk

class RuleWidget(gtk.HBox):
    def __init__(self, rule):
        self.rule = rule
        ###
        gtk.HBox.__init__(self)
        ###
        self.startTbox = TimeButton()
        self.endTbox = TimeButton()
        self.pack_start(self.startTbox, 0, 0)
        self.pack_start(gtk.Label(' ' + _('to') + ' '), 0, 0)
        self.pack_start(self.endTbox, 0, 0)
    def updateWidget(self):
        self.startTbox.set_time(self.rule.dayTimeStart)
        self.endTbox.set_time(self.rule.dayTimeEnd)
    def updateVars(self):
        self.rule.dayTimeStart = self.startTbox.get_time()
        self.rule.dayTimeEnd = self.endTbox.get_time()


