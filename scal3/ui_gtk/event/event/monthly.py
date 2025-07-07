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

from scal3 import ui
from scal3.cal_types import jd_to
from scal3.event_lib.rules import DayTimeRangeEventRule, EndEventRule, StartEventRule
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.event import common
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.mywidgets.multi_spin.day import DaySpinButton
from scal3.ui_gtk.mywidgets.multi_spin.hour_minute import HourMinuteButton

if TYPE_CHECKING:
	from scal3.event_lib.events import MonthlyEvent

__all__ = ["WidgetClass"]


class WidgetClass(common.WidgetClass):
	_event: MonthlyEvent

	def __init__(self, event: MonthlyEvent) -> None:  # FIXME
		event.setJd(ui.cells.current.jd)
		common.WidgetClass.__init__(self, event)
		# ------
		sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# ------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Start"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.startDateInput = DateButton()
		pack(hbox, self.startDateInput)
		# ---
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		# ------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("End"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.endDateInput = DateButton()
		pack(hbox, self.endDateInput)
		# ---
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		# ------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Day of Month"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.daySpin = DaySpinButton()
		pack(hbox, self.daySpin)
		# ---
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		# ---------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Time"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		# --
		self.dayTimeStartInput = HourMinuteButton()
		self.dayTimeEndInput = HourMinuteButton()
		# --
		pack(hbox, self.dayTimeStartInput)
		pack(hbox, gtk.Label(label=" " + _("To", ctx="time range") + " "))
		pack(hbox, self.dayTimeEndInput)
		pack(self, hbox)
		# -------------
		# self.notificationBox = common.NotificationBox(event)
		# pack(self, self.notificationBox)
		# -------------
		# self.filesBox = common.FilesBox(self._event)
		# pack(self, self.filesBox)

	def updateWidget(self) -> None:  # FIXME
		common.WidgetClass.updateWidget(self)
		calType = self._event.calType
		# ---
		self.startDateInput.set_value(jd_to(self._event.getStartJd(), calType))
		self.endDateInput.set_value(jd_to(self._event.getEndJd(), calType))
		# ---
		self.daySpin.set_value(self._event.getDay())
		# ---
		dayTimeRange = DayTimeRangeEventRule.getFrom(self._event)
		if dayTimeRange is None:
			raise RuntimeError("no dayTimeRange rule")
		self.dayTimeStartInput.set_value(dayTimeRange.dayTimeStart)
		self.dayTimeEndInput.set_value(dayTimeRange.dayTimeEnd)

	def updateVars(self) -> None:  # FIXME
		common.WidgetClass.updateVars(self)
		# --
		start = StartEventRule.getFrom(self._event)
		if start is None:
			raise RuntimeError("no start rule")
		start.setDate(self.startDateInput.getDate())
		# --
		end = EndEventRule.getFrom(self._event)
		if end is None:
			raise RuntimeError("no end rule")
		end.setDate(self.endDateInput.getDate())
		# --
		self._event.setDay(self.daySpin.get_value())
		# ---
		dayTimeRange = DayTimeRangeEventRule.getFrom(self._event)
		if dayTimeRange is None:
			raise RuntimeError("no dayTimeRange rule")
		h1, m1 = self.dayTimeStartInput.get_value()
		h2, m2 = self.dayTimeEndInput.get_value()
		dayTimeRange.setRange(
			(h1, m1, 0),
			(h2, m2, 0),
		)

	def calTypeComboChanged(self, _w: gtk.Widget | None = None) -> None:
		# overwrite method from common.WidgetClass
		newCalType = self.calTypeCombo.getActive()
		assert newCalType is not None
		self.startDateInput.changeCalType(self._event.calType, newCalType)
		self.endDateInput.changeCalType(self._event.calType, newCalType)
		self._event.calType = newCalType
