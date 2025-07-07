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
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.event import common
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.mywidgets.multi_spin.time_b import TimeButton

if TYPE_CHECKING:
	from scal3.event_lib.events import TaskEvent

__all__ = ["WidgetClass"]


class WidgetClass(common.WidgetClass):
	_event: TaskEvent

	def __init__(self, event: TaskEvent) -> None:  # FIXME
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
		# --
		pack(hbox, gtk.Label(label=" " + _("Time")))
		self.startTimeInput = TimeButton()
		pack(hbox, self.startTimeInput)
		# --
		pack(self, hbox)
		# ------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.endTypeCombo = gtk.ComboBoxText()
		for item in ("Duration", "End"):
			self.endTypeCombo.append_text(_(item))
		self.endTypeCombo.connect("changed", self.endTypeComboChanged)
		sizeGroup.add_widget(self.endTypeCombo)
		pack(hbox, self.endTypeCombo)
		# ----
		self.durationBox = common.DurationInputBox()
		pack(hbox, self.durationBox, 1, 1)
		# ----
		self.endDateHbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.endDateInput = DateButton()
		pack(self.endDateHbox, self.endDateInput)
		# --
		pack(self.endDateHbox, gtk.Label(label=" " + _("Time")))
		self.endTimeInput = TimeButton()
		pack(self.endDateHbox, self.endTimeInput)
		# --
		pack(hbox, self.endDateHbox, 1, 1)
		# ----
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		# -------------
		self.notificationBox = common.NotificationBox(event)
		pack(self, self.notificationBox)
		# -------------
		# self.filesBox = common.FilesBox(self._event)
		# pack(self, self.filesBox)

	def endTypeComboChanged(self, _combo: gtk.ComboBox | None = None) -> None:
		active = self.endTypeCombo.get_active()
		if active == 0:  # duration
			self.durationBox.show()
			self.endDateHbox.hide()
		elif active == 1:  # end date
			self.durationBox.hide()
			self.endDateHbox.show()
		else:
			raise RuntimeError

	def updateWidget(self) -> None:  # FIXME
		common.WidgetClass.updateWidget(self)
		# ---
		startDate, startTime = self._event.getStart()
		self.startDateInput.set_value(startDate)
		self.startTimeInput.set_value(startTime)
		# ---
		endType, values = self._event.getEnd()
		if endType == "duration":
			self.endTypeCombo.set_active(0)
			self.durationBox.setDuration(*values)
			self.endDateInput.set_value(startDate)  # FIXME
			self.endTimeInput.set_value(startTime)  # FIXME
		elif endType == "date":
			self.endTypeCombo.set_active(1)
			self.endDateInput.set_value(values[0])  # type: ignore[arg-type]
			self.endTimeInput.set_value(values[1])  # type: ignore[arg-type]
		else:
			raise RuntimeError
		self.endTypeComboChanged()

	def updateVars(self) -> None:  # FIXME
		common.WidgetClass.updateVars(self)
		self._event.setStart(
			self.startDateInput.getDate(),
			self.startTimeInput.getTime(),
		)
		# ---
		active = self.endTypeCombo.get_active()
		if active == 0:
			self._event.setEndDuration(*self.durationBox.getDuration())
		elif active == 1:
			self._event.setEndDateTime(
				self.endDateInput.getDate(),
				self.endTimeInput.getTime(),
			)

	def calTypeComboChanged(self, _w: gtk.Widget | None = None) -> None:
		# overwrite method from common.WidgetClass
		newCalType = self.calTypeCombo.getActive()
		assert newCalType is not None
		self.startDateInput.changeCalType(self._event.calType, newCalType)
		self.endDateInput.changeCalType(self._event.calType, newCalType)
		self._event.calType = newCalType
