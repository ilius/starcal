#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import event_lib

from scal3.ui_gtk import *


class WidgetClass(gtk.ComboBoxText):
	def __init__(self, rule):
		self.rule = rule
		###
		gtk.ComboBoxText.__init__(self)
		###
		self.append_text(_('Every Week'))
		self.append_text(_('Odd Weeks'))
		self.append_text(_('Even Weeks'))
		self.set_active(0)

	def updateWidget(self):
		self.set_active(self.rule.weekNumMode)

	def updateVars(self):
		self.rule.weekNumMode = self.get_active()
