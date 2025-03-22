#!/usr/bin/env python3
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.multi_spin.time_b import TimeButton


class WidgetClass(TimeButton):
	def __init__(self, rule):
		self.rule = rule
		TimeButton.__init__(self)

	def updateWidget(self):
		self.set_value(self.rule.dayTime)

	def updateVars(self):
		self.rule.dayTime = self.get_value()
