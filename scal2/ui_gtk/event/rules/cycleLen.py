#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_lib
from scal2.ui_gtk.mywidgets.multi_spin_button import IntSpinButton, TimeButton
import gtk
from gtk import gdk

class RuleWidget(gtk.HBox):
    def __init__(self, rule):
        self.rule = rule
        ###
        gtk.HBox.__init__(self)
        spin = IntSpinButton(0, 9999)
        self.pack_start(spin, 0, 0)
        self.spin = spin
        ##
        self.pack_start(gtk.Label(' '+_('days and')+' '), 0, 0)
        tbox = TimeButton()
        self.pack_start(tbox, 0, 0)
        self.tbox = tbox
    def updateWidget(self):
        self.spin.set_value(self.rule.days)
        self.tbox.set_value(self.rule.extraTime)
    def updateVars(self):
        self.rule.days = self.spin.get_value()
        self.rule.extraTime = self.tbox.get_value()

