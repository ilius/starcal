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

from scal3.event_lib.rules import WeekMonthEventRule
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.event.event.weekdayBase import WidgetBase
from scal3.ui_gtk.mywidgets.month_combo import MonthComboBox
from scal3.ui_gtk.mywidgets.weekday_combo import WeekDayComboBox

if TYPE_CHECKING:
	from scal3.event_lib.weekday import MonthlyWeekdayEvent

__all__ = ["WidgetClass"]


class WidgetClass(WidgetBase):
	_event: MonthlyWeekdayEvent

	def makePatternRow(self, sizeGroup: gtk.SizeGroup) -> None:
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Nth Weekday of Month"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		# ---
		self.nthCombo = gtk.ComboBoxText()
		for item in WeekMonthEventRule.wmIndexNames:
			self.nthCombo.append_text(item)
		pack(hbox, self.nthCombo)
		self.weekDayCombo = WeekDayComboBox()
		pack(hbox, self.weekDayCombo)
		pack(hbox, gtk.Label(label=_(" of ")))
		self.monthCombo = MonthComboBox(True)
		pack(hbox, self.monthCombo)
		# ---
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)

	def updatePatternWidget(self) -> None:
		self.monthCombo.build(self._event.calType)
		weekMonth = WeekMonthEventRule.getFrom(self._event)
		if weekMonth is None:
			raise RuntimeError("no weekMonth rule")
		self.nthCombo.set_active(weekMonth.wmIndex)
		self.weekDayCombo.setValue(weekMonth.weekDay)
		self.monthCombo.setValue(weekMonth.month)

	def updatePatternVars(self) -> None:
		weekMonth = WeekMonthEventRule.getFrom(self._event)
		if weekMonth is None:
			raise RuntimeError("no weekMonth rule")
		weekMonth.month = self.monthCombo.getValue()
		weekMonth.wmIndex = self.nthCombo.get_active()
		weekMonth.weekDay = self.weekDayCombo.getValue()

	def updatePatternCalType(self, newCalType: int) -> None:
		self.monthCombo.build(newCalType)
