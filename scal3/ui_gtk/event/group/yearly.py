#!/usr/bin/env python
# -*- coding: utf-8 -*-

from scal3 import core
from scal3.locale_man import tr as _

from scal3.ui_gtk import *
from scal3.ui_gtk.event import common
from scal3.ui_gtk.event.group.group import WidgetClass as NormalWidgetClass


class WidgetClass(NormalWidgetClass):
	def __init__(self, group):
		NormalWidgetClass.__init__(self, group)
		###
		hbox = gtk.HBox()
		label = gtk.Label(_("Show Date in Event Summary"))
		label.set_alignment(0, 0.5)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.showDateCheck = gtk.CheckButton()
		pack(hbox, self.showDateCheck)
		pack(self, hbox)

	def updateWidget(self):  # FIXME
		NormalWidgetClass.updateWidget(self)
		self.showDateCheck.set_active(self.group.showDate)

	def updateVars(self):
		NormalWidgetClass.updateVars(self)
		self.group.showDate = self.showDateCheck.get_active()
