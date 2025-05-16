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

from scal3.locale_man import tr as _
from scal3.ui_gtk import HBox, gtk, pack
from scal3.ui_gtk.event import common
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.mywidgets.ymd import YearMonthDayBox

if TYPE_CHECKING:
	from scal3.event_lib.event_base import Event

__all__ = ["WidgetClass"]


class WidgetClass(common.WidgetClass):
	def __init__(self, event: Event) -> None:  # FIXME
		common.WidgetClass.__init__(self, event)
		# ------
		sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# ------
		try:
			separateYmd = event.parent.showSeparateYmdInputs
		except AttributeError:
			separateYmd = False
		if separateYmd:
			self.startDateInput = YearMonthDayBox()
			self.endDateInput = YearMonthDayBox()
		else:
			self.startDateInput = DateButton()
			self.endDateInput = DateButton()
		# ------
		hbox = HBox()
		label = gtk.Label(label=_("Start") + ": ")
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		pack(hbox, self.startDateInput)
		pack(self, hbox)
		# ------
		hbox = HBox()
		label = gtk.Label(label=_("End") + ": ")
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		pack(hbox, self.endDateInput)
		pack(self, hbox)
		# -------------
		# self.filesBox = common.FilesBox(self.event)
		# pack(self, self.filesBox)

	def updateWidget(self) -> None:
		common.WidgetClass.updateWidget(self)
		start, ok = self.event["start"]
		if not ok:
			raise KeyError('rule "start" not found')
		end, ok = self.event["end"]
		if not ok:
			raise KeyError('rule "end" not found')
		self.startDateInput.set_value(start.date)
		self.endDateInput.set_value(end.date)

	def updateVars(self) -> None:  # FIXME
		common.WidgetClass.updateVars(self)
		start, ok = self.event["start"]
		if not ok:
			raise KeyError('rule "start" not found')
		end, ok = self.event["end"]
		if not ok:
			raise KeyError('rule "end" not found')
		start.setDate(self.startDateInput.get_value())
		end.setDate(self.endDateInput.get_value())

	def calTypeComboChanged(self, _widget: gtk.Widget | None = None) -> None:
		# overwrite method from common.WidgetClass
		newCalType = self.calTypeCombo.get_active()
		self.startDateInput.changeCalType(self.event.calType, newCalType)
		self.endDateInput.changeCalType(self.event.calType, newCalType)
		self.event.calType = newCalType
