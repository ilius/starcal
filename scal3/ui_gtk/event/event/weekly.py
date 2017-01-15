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
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.mywidgets.multi_spin.hour_minute import HourMinuteButton
from scal3.ui_gtk.event import common


class WidgetClass(common.WidgetClass):
	def __init__(self, event):## FIXME
		common.WidgetClass.__init__(self, event)
		######
		sizeGroup = gtk.SizeGroup(gtk.SizeGroupMode.HORIZONTAL)
		######
		hbox = gtk.HBox()
		label = gtk.Label(_("Start"))
		label.set_alignment(0, 0.5)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.startDateInput = DateButton()
		pack(hbox, self.startDateInput)
		###
		pack(hbox, gtk.Label(""), 1, 1)
		pack(self, hbox)
		######
		hbox = gtk.HBox()
		label = gtk.Label(_("Repeat Every "))
		label.set_alignment(0, 0.5)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.weeksSpin = IntSpinButton(1, 99999)
		pack(hbox, self.weeksSpin)
		pack(hbox, gtk.Label("  " + _(" Weeks")))
		###
		pack(hbox, gtk.Label(""), 1, 1)
		pack(self, hbox)
		######
		hbox = gtk.HBox()
		label = gtk.Label(_("End"))
		label.set_alignment(0, 0.5)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.endDateInput = DateButton()
		pack(hbox, self.endDateInput)
		###
		pack(hbox, gtk.Label(""), 1, 1)
		pack(self, hbox)
		#########
		hbox = gtk.HBox()
		label = gtk.Label(_("Time"))
		label.set_alignment(0, 0.5)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		##
		self.dayTimeStartInput = HourMinuteButton()
		self.dayTimeEndInput = HourMinuteButton()
		##
		pack(hbox, self.dayTimeStartInput)
		pack(hbox, gtk.Label(" " + _("to") + " "))
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
		mode = self.event.mode
		###
		self.startDateInput.set_value(jd_to(self.event.getStartJd(), mode))
		self.weeksSpin.set_value(self.event["cycleWeeks"].weeks)
		self.endDateInput.set_value(jd_to(self.event.getEndJd(), mode))
		###
		timeRangeRule = self.event["dayTimeRange"]
		self.dayTimeStartInput.set_value(timeRangeRule.dayTimeStart)
		self.dayTimeEndInput.set_value(timeRangeRule.dayTimeEnd)

	def updateVars(self):## FIXME
		common.WidgetClass.updateVars(self)
		self.event["start"].setDate(self.startDateInput.get_value())
		self.event["end"].setDate(self.endDateInput.get_value())
		self.event["cycleWeeks"].setData(self.weeksSpin.get_value())
		###
		self.event["dayTimeRange"].setRange(
			self.dayTimeStartInput.get_value(),
			self.dayTimeEndInput.get_value(),
		)

	def modeComboChanged(self, obj=None):
		# overwrite method from common.WidgetClass
		newMode = self.modeCombo.get_active()
		self.startDateInput.changeMode(self.event.mode, newMode)
		self.endDateInput.changeMode(self.event.mode, newMode)
		self.event.mode = newMode
