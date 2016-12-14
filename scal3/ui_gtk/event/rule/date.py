#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import event_lib

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton

class WidgetClass(DateButton):
	def __init__(self, rule):
		self.rule = rule
		DateButton.__init__(self)
	def updateWidget(self):
		self.set_value(self.rule.date)
	def updateVars(self):
		self.rule.date = self.get_value()
	def changeMode(self, mode):
		curMode = self.rule.getMode()
		if mode!=curMode:
			y, m, d = self.get_value()
			self.set_value(core.convert(y, m, d, curMode, mode))
