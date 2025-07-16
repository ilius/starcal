#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.


from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.cal_types import calTypes, convert
from scal3.event_lib.rules import StartEventRule
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.event import common
from scal3.ui_gtk.mywidgets.month_combo import MonthComboBox
from scal3.ui_gtk.mywidgets.multi_spin.day import DaySpinButton
from scal3.ui_gtk.mywidgets.multi_spin.year import YearSpinButton

if TYPE_CHECKING:
	from scal3.event_lib.yearly import YearlyEvent

__all__ = ["WidgetClass"]


class WidgetClass(common.WidgetClass):
	_event: YearlyEvent

	def __init__(self, event: YearlyEvent) -> None:  # FIXME
		common.WidgetClass.__init__(self, event)
		# ----------------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Month")))
		self.monthCombo = MonthComboBox()
		self.monthCombo.build(event.calType)
		pack(hbox, self.monthCombo)
		pack(hbox, gtk.Label(), 1, 1)
		# pack(self, hbox)
		# ---
		# hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Day")))
		self.daySpin = DaySpinButton()
		pack(hbox, self.daySpin)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.startYearCheck = gtk.CheckButton(label=_("Start Year"))
		pack(hbox, self.startYearCheck)
		self.startYearSpin = YearSpinButton()
		pack(hbox, self.startYearSpin)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		self.startYearCheck.connect("clicked", self.onStartYearCheckClick)
		# ----
		self.notificationBox = common.NotificationBox(event)
		pack(self, self.notificationBox)
		# ----
		# self.filesBox = common.FilesBox(self._event)
		# pack(self, self.filesBox)

	def onStartYearCheckClick(self, _w: gtk.Widget | None = None) -> None:
		self.startYearSpin.set_sensitive(
			self.startYearCheck.get_active(),
		)

	def updateWidget(self) -> None:  # FIXME
		common.WidgetClass.updateWidget(self)
		month = self._event.getMonth()
		assert month is not None
		self.monthCombo.setValue(month)
		self.daySpin.setValue(self._event.getDay())
		startRule = StartEventRule.getFrom(self._event)
		if startRule is not None:
			self.startYearCheck.set_active(True)
			self.startYearSpin.set_value(startRule.date[0])
		else:
			self.startYearCheck.set_active(False)
			self.startYearSpin.set_value(self._event.getSuggestedStartYear())
		self.onStartYearCheckClick()

	def updateVars(self) -> None:  # FIXME
		common.WidgetClass.updateVars(self)
		self._event.setMonth(self.monthCombo.getValue())
		self._event.setDay(self.daySpin.getValue())
		startRule = StartEventRule.getFrom(self._event)
		if self.startYearCheck.get_active():
			if startRule is None:
				startRule = StartEventRule.addOrGetFrom(self._event)
			startRule.date = (self.startYearSpin.get_value(), 1, 1)
		elif startRule is not None:
			del self._event["start"]

	def calTypeComboChanged(self, _w: gtk.Widget | None = None) -> None:
		# overwrite method from common.WidgetClass
		newCalType = self.calTypeCombo.getActive()
		assert newCalType is not None
		module = calTypes[newCalType]
		if module is None:
			raise RuntimeError(f"cal type '{newCalType}' not found")
		yearStr = self.startYearSpin.get_text()
		if not yearStr:
			return
		year = int(yearStr)
		monthCombo = self.monthCombo
		month = monthCombo.getValue()
		monthCombo.build(newCalType)
		y2, m2, d2 = convert(
			year,
			month,
			self.daySpin.getValue(),
			self._event.calType,
			newCalType,
		)
		self.startYearSpin.setValue(y2)
		monthCombo.setValue(m2)
		self.daySpin.setValue(d2)
		self._event.calType = newCalType
