#!/usr/bin/env python
# -*- coding: utf-8 -*-

from scal3 import core
from scal3.locale_man import tr as _
from scal3 import event_lib

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
from scal3.ui_gtk.mywidgets.multi_spin.time_b import TimeButton


class WidgetClass(gtk.HBox):
	def __init__(self, rule):
		self.rule = rule
		###
		gtk.HBox.__init__(self)
		spin = IntSpinButton(0, 9999)
		pack(self, spin)
		self.spin = spin
		##
		pack(self, gtk.Label(" " + _("days and") + " "))
		tbox = TimeButton()
		pack(self, tbox)
		self.tbox = tbox

	def updateWidget(self):
		self.spin.set_value(self.rule.days)
		self.tbox.set_value(self.rule.extraTime)

	def updateVars(self):
		self.rule.days = self.spin.get_value()
		self.rule.extraTime = self.tbox.get_value()
