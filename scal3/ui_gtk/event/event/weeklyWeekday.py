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

from scal3 import core, ui
from scal3.event_lib.rules import WeekDayEventRule
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.event.event.weekdayBase import WidgetBase
from scal3.ui_gtk.utils import showError

if TYPE_CHECKING:
	from scal3.event_lib.weekday import WeeklyWeekdayEvent

__all__ = ["WidgetClass"]


class WidgetClass(WidgetBase):
	_event: WeeklyWeekdayEvent

	def makePatternRow(self, sizeGroup: gtk.SizeGroup) -> None:
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Days of Week"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		# ---
		weekDayHbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		weekDayHbox.set_homogeneous(True)
		self.weekDayToggles = []
		start = core.firstWeekDay.v
		for i in range(7):
			cb = gtk.ToggleButton(label=core.weekDayNameAb[(start + i) % 7])
			pack(weekDayHbox, cb, 1, 1)
			self.weekDayToggles.append(cb)
		pack(hbox, weekDayHbox)
		# ---
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)

	def updatePatternWidget(self) -> None:
		weekDay = WeekDayEventRule.getFrom(self._event)
		if weekDay is None:
			raise RuntimeError("no weekDay rule")
		for cb in self.weekDayToggles:
			cb.set_active(False)
		for j in weekDay.weekDayList:
			self.weekDayToggles[j].set_active(True)

	def updatePatternVars(self) -> None:
		weekDayList = [j for j in range(7) if self.weekDayToggles[j].get_active()]
		if not weekDayList:
			showError(
				_("Select at least one day of week"),
				transient_for=ui.eventManDialog.w,
			)
			raise RuntimeError("No day of week selected")
		weekDay = WeekDayEventRule.getFrom(self._event)
		if weekDay is None:
			raise RuntimeError("no weekDay rule")
		weekDay.weekDayList = weekDayList
