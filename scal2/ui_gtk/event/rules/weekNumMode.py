#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_lib
import gtk
from gtk import gdk

class RuleWidget(gtk.ComboBox):
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
        self.append_text(_('Every Week'))
        self.append_text(_('Odd Weeks'))
        self.append_text(_('Even Weeks'))
        self.set_active(0)
    def updateWidget(self):
        self.set_active(self.rule.weekNumMode)
    def updateVars(self):
        self.rule.weekNumMode = self.get_active()


