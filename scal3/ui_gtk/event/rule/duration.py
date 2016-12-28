#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import event_lib

from scal3.ui_gtk import *
from scal3.ui_gtk.event import common


class WidgetClass(common.DurationInputBox):
	def __init__(self, rule):
		self.rule = rule
		common.DurationInputBox.__init__(self)

	def updateWidget(self):
		self.setDuration(self.rule.value, self.rule.unit)

	def updateVars(self):
		self.rule.value, self.rule.unit = self.getDuration()
