#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import event_lib

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.mywidgets.multi_spin.time_b import TimeButton


class WidgetClass(gtk.HBox):
	def __init__(self, rule):
		self.rule = rule
		###
		gtk.HBox.__init__(self)
		###
		self.startTbox = TimeButton()
		self.endTbox = TimeButton()
		pack(self, self.startTbox)
		pack(self, gtk.Label(' ' + _('to') + ' '))
		pack(self, self.endTbox)

	def updateWidget(self):
		self.startTbox.set_value(self.rule.dayTimeStart)
		self.endTbox.set_value(self.rule.dayTimeEnd)

	def updateVars(self):
		self.rule.dayTimeStart = self.startTbox.get_value()
		self.rule.dayTimeEnd = self.endTbox.get_value()
