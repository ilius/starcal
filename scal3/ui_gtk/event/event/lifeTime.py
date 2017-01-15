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
		sizeGroup = gtk.SizeGroup(gtk.SizeGroupMode.HORIZONTAL)
		######
		try:
			seperated = event.parent.showSeperatedYmdInputs
		except AttributeError:
			seperated = False
		if seperated:
			self.startDateInput = YearMonthDayBox()
			self.endDateInput = YearMonthDayBox()
		else:
			self.startDateInput = DateButton()
			self.endDateInput = DateButton()
		######
		hbox = gtk.HBox()
		label = gtk.Label(_("Start") + ": ")
		label.set_alignment(0, 0.5)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		pack(hbox, self.startDateInput)
		pack(self, hbox)
		######
		hbox = gtk.HBox()
		label = gtk.Label(_("End") + ": ")
		label.set_alignment(0, 0.5)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		pack(hbox, self.endDateInput)
		pack(self, hbox)
		#############
		#self.filesBox = common.FilesBox(self.event)
		#pack(self, self.filesBox)

	def updateWidget(self):
		common.WidgetClass.updateWidget(self)
		self.startDateInput.set_value(self.event["start"].date)
		self.endDateInput.set_value(self.event["end"].date)

	def updateVars(self):## FIXME
		common.WidgetClass.updateVars(self)
		self.event["start"].setDate(self.startDateInput.get_value())
		self.event["end"].setDate(self.endDateInput.get_value())

	def modeComboChanged(self, obj=None):
		# overwrite method from common.WidgetClass
		newMode = self.modeCombo.get_active()
		self.startDateInput.changeMode(self.event.mode, newMode)
		self.endDateInput.changeMode(self.event.mode, newMode)
		self.event.mode = newMode
