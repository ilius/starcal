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

from scal3.cal_types import calTypes, convert
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import event_lib

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.month_combo import MonthComboBox
from scal3.ui_gtk.mywidgets.multi_spin.year import YearSpinButton
from scal3.ui_gtk.mywidgets.multi_spin.day import DaySpinButton
from scal3.ui_gtk.event import common


class WidgetClass(common.WidgetClass):
	def __init__(self, event):## FIXME
		common.WidgetClass.__init__(self, event)
		################
		hbox = HBox()
		pack(hbox, gtk.Label(label=_("Month")))
		self.monthCombo = MonthComboBox()
		self.monthCombo.build(event.calType)
		pack(hbox, self.monthCombo)
		pack(hbox, gtk.Label(), 1, 1)
		#pack(self, hbox)
		###
		#hbox = HBox()
		pack(hbox, gtk.Label(label=_("Day")))
		self.daySpin = DaySpinButton()
		pack(hbox, self.daySpin)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		###
		hbox = HBox()
		self.startYearCheck = gtk.CheckButton(label=_("Start Year"))
		pack(hbox, self.startYearCheck)
		self.startYearSpin = YearSpinButton()
		pack(hbox, self.startYearSpin)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		self.startYearCheck.connect("clicked", self.onStartYearCheckClick)
		####
		self.notificationBox = common.NotificationBox(event)
		pack(self, self.notificationBox)
		####
		#self.filesBox = common.FilesBox(self.event)
		#pack(self, self.filesBox)

	def onStartYearCheckClick(self, obj=None):
		return self.startYearSpin.set_sensitive(
			self.startYearCheck.get_active()
		)

	def updateWidget(self):## FIXME
		common.WidgetClass.updateWidget(self)
		self.monthCombo.setValue(self.event.getMonth())
		self.daySpin.set_value(self.event.getDay())
		startRule, ok = self.event["start"]
		if ok:
			self.startYearCheck.set_active(True)
			self.startYearSpin.set_value(startRule.date[0])
		else:
			self.startYearCheck.set_active(False)
			self.startYearSpin.set_value(self.event.getSuggestedStartYear())
		self.onStartYearCheckClick()

	def updateVars(self):## FIXME
		common.WidgetClass.updateVars(self)
		self.event.setMonth(self.monthCombo.getValue())
		self.event.setDay(int(self.daySpin.get_value()))
		if self.startYearCheck.get_active():
			startRule = self.event.getAddRule("start")
			startRule.date = (self.startYearSpin.get_value(), 1, 1)
		else:
			if "start" in self.event:
				del self.event["start"]

	def calTypeComboChanged(self, obj=None):
		# overwrite method from common.WidgetClass
		newCalType = self.calTypeCombo.get_active()
		module, ok = calTypes[newCalType]
		if not ok:
			raise RuntimeError(f"cal type '{calType}' not found")
		monthCombo = self.monthCombo
		month = monthCombo.getValue()
		monthCombo.build(newCalType)
		y2, m2, d2 = convert(
			int(self.startYearSpin.get_value()),
			month,
			int(self.daySpin.get_value()),
			self.event.calType,
			newCalType,
		)
		self.startYearSpin.set_value(y2)
		monthCombo.setValue(m2)
		self.daySpin.set_value(d2)
		self.event.calType = newCalType
