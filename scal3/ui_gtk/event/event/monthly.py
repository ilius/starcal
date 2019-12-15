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

from scal3.cal_types import jd_to
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.multi_spin.day import DaySpinButton
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.mywidgets.multi_spin.hour_minute import HourMinuteButton
from scal3.ui_gtk.event import common


class WidgetClass(common.WidgetClass):
	def __init__(self, event):## FIXME
		event.setJd(ui.cell.jd)
		common.WidgetClass.__init__(self, event)
		######
		sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		######
		hbox = HBox()
		label = gtk.Label(label=_("Start"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.startDateInput = DateButton()
		pack(hbox, self.startDateInput)
		###
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		######
		hbox = HBox()
		label = gtk.Label(label=_("End"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.endDateInput = DateButton()
		pack(hbox, self.endDateInput)
		###
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		######
		hbox = HBox()
		label = gtk.Label(label=_("Day of Month"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.daySpin = DaySpinButton()
		pack(hbox, self.daySpin)
		###
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		#########
		hbox = HBox()
		label = gtk.Label(label=_("Time"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		##
		self.dayTimeStartInput = HourMinuteButton()
		self.dayTimeEndInput = HourMinuteButton()
		##
		pack(hbox, self.dayTimeStartInput)
		pack(hbox, gtk.Label(label=" " + _("to") + " "))
		pack(hbox, self.dayTimeEndInput)
		pack(self, hbox)
		#############
		#self.notificationBox = common.NotificationBox(event)
		#pack(self, self.notificationBox)
		#############
		#self.filesBox = common.FilesBox(self.event)
		#pack(self, self.filesBox)

	def updateWidget(self):## FIXME
		common.WidgetClass.updateWidget(self)
		calType = self.event.calType
		###
		self.startDateInput.set_value(jd_to(self.event.getStartJd(), calType))
		self.endDateInput.set_value(jd_to(self.event.getEndJd(), calType))
		###
		self.daySpin.set_value(self.event.getDay())
		###
		dayTimeRange, ok = self.event["dayTimeRange"]
		if not ok:
			raise RuntimeError("no dayTimeRange rule")
		self.dayTimeStartInput.set_value(dayTimeRange.dayTimeStart)
		self.dayTimeEndInput.set_value(dayTimeRange.dayTimeEnd)

	def updateVars(self):## FIXME
		common.WidgetClass.updateVars(self)
		##
		start, ok = self.event["start"]
		if not ok:
			raise RuntimeError("no start rule")
		start.setDate(self.startDateInput.get_value())
		##
		end, ok = self.event["end"]
		if not ok:
			raise RuntimeError("no end rule")
		end.setDate(self.endDateInput.get_value())
		##
		self.event.setDay(self.daySpin.get_value())
		###
		dayTimeRange, ok = self.event["dayTimeRange"]
		if not ok:
			raise RuntimeError("no dayTimeRange rule")
		dayTimeRange.setRange(
			self.dayTimeStartInput.get_value(),
			self.dayTimeEndInput.get_value(),
		)

	def calTypeComboChanged(self, obj=None):
		# overwrite method from common.WidgetClass
		newCalType = self.calTypeCombo.get_active()
		self.startDateInput.changeCalType(self.event.calType, newCalType)
		self.endDateInput.changeCalType(self.event.calType, newCalType)
		self.event.calType = newCalType
