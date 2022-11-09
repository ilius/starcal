#!/usr/bin/env python3
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import event_lib

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.num_ranges_entry import NumRangesEntry


class WidgetClass(NumRangesEntry):
	def __init__(self, rule):
		self.rule = rule
		NumRangesEntry.__init__(self, 0, 9999, 10)

	def updateWidget(self):
		self.setValues(self.rule.values)

	def updateVars(self):
		self.rule.values = self.getValues()

	def changeCalType(self, calType):
		if calType == self.rule.getCalType():
			return
		self.updateVars()
		self.rule.changeCalType(calType)
		self.updateWidget()
