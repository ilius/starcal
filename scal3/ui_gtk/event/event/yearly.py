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
		hbox = gtk.HBox()
		pack(hbox, gtk.Label(_('Month')))
		self.monthCombo = MonthComboBox()
		self.monthCombo.build(event.mode)
		pack(hbox, self.monthCombo)
		pack(hbox, gtk.Label(''), 1, 1)
		#pack(self, hbox)
		###
		#hbox = gtk.HBox()
		pack(hbox, gtk.Label(_('Day')))
		self.daySpin = DaySpinButton()
		pack(hbox, self.daySpin)
		pack(hbox, gtk.Label(''), 1, 1)
		pack(self, hbox)
		###
		hbox = gtk.HBox()
		self.startYearCheck = gtk.CheckButton(_('Start Year'))
		pack(hbox, self.startYearCheck)
		self.startYearSpin = YearSpinButton()
		pack(hbox, self.startYearSpin)
		pack(hbox, gtk.Label(''), 1, 1)
		pack(self, hbox)
		self.startYearCheck.connect('clicked', self.startYearCheckClicked)
		####
		self.notificationBox = common.NotificationBox(event)
		pack(self, self.notificationBox)
		####
		#self.filesBox = common.FilesBox(self.event)
		#pack(self, self.filesBox)

	def startYearCheckClicked(self, obj=None):
		return self.startYearSpin.set_sensitive(
			self.startYearCheck.get_active()
		)

	def updateWidget(self):## FIXME
		common.WidgetClass.updateWidget(self)
		self.monthCombo.setValue(self.event.getMonth())
		self.daySpin.set_value(self.event.getDay())
		try:
			startRule = self.event['start']
		except:
			self.startYearCheck.set_active(False)
			self.startYearSpin.set_value(self.event.getSuggestedStartYear())
		else:
			self.startYearCheck.set_active(True)
			self.startYearSpin.set_value(startRule.date[0])
		self.startYearCheckClicked()

	def updateVars(self):## FIXME
		common.WidgetClass.updateVars(self)
		self.event.setMonth(self.monthCombo.getValue())
		self.event.setDay(int(self.daySpin.get_value()))
		if self.startYearCheck.get_active():
			startRule = self.event.getAddRule('start')
			startRule.date = (self.startYearSpin.get_value(), 1, 1)
		else:
			try:
				del self.event['start']
			except KeyError:
				pass

	def modeComboChanged(self, obj=None):
		# overwrite method from common.WidgetClass
		newMode = self.modeCombo.get_active()
		module = calTypes[newMode]
		monthCombo = self.monthCombo
		month = monthCombo.getValue()
		monthCombo.build(newMode)
		y2, m2, d2 = convert(
			int(self.startYearSpin.get_value()),
			month,
			int(self.daySpin.get_value()),
			self.event.mode,
			newMode,
		)
		self.startYearSpin.set_value(y2)
		monthCombo.setValue(m2)
		self.daySpin.set_value(d2)
		self.event.mode = newMode
