#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.mywidgets.ymd import YearMonthDayBox
from scal3.ui_gtk.event import common


class WidgetClass(common.WidgetClass):
	def __init__(self, event):## FIXME
		common.WidgetClass.__init__(self, event)
		######
		sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		######
		try:
			separated = event.parent.showSeparatedYmdInputs
		except AttributeError:
			separated = False
		if separated:
			self.startDateInput = YearMonthDayBox()
			self.endDateInput = YearMonthDayBox()
		else:
			self.startDateInput = DateButton()
			self.endDateInput = DateButton()
		######
		hbox = HBox()
		label = gtk.Label(label=_("Start") + ": ")
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		pack(hbox, self.startDateInput)
		pack(self, hbox)
		######
		hbox = HBox()
		label = gtk.Label(label=_("End") + ": ")
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		pack(hbox, self.endDateInput)
		pack(self, hbox)
		#############
		#self.filesBox = common.FilesBox(self.event)
		#pack(self, self.filesBox)

	def updateWidget(self):
		common.WidgetClass.updateWidget(self)
		start, ok = self.event["start"]
		if not ok:
			raise KeyError("rule \"start\" not found")
		end, ok = self.event["end"]
		if not ok:
			raise KeyError("rule \"end\" not found")
		self.startDateInput.set_value(start.date)
		self.endDateInput.set_value(end.date)

	def updateVars(self):## FIXME
		common.WidgetClass.updateVars(self)
		start, ok = self.event["start"]
		if not ok:
			raise KeyError("rule \"start\" not found")
		end, ok = self.event["end"]
		if not ok:
			raise KeyError("rule \"end\" not found")
		start.setDate(self.startDateInput.get_value())
		end.setDate(self.endDateInput.get_value())

	def calTypeComboChanged(self, obj=None):
		# overwrite method from common.WidgetClass
		newCalType = self.calTypeCombo.get_active()
		self.startDateInput.changeCalType(self.event.calType, newCalType)
		self.endDateInput.changeCalType(self.event.calType, newCalType)
		self.event.calType = newCalType
