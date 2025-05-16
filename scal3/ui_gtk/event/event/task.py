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

from scal3.event_lib.event_base import Event
from scal3.locale_man import tr as _
from scal3.ui_gtk import HBox, gtk, pack
from scal3.ui_gtk.event import common
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.mywidgets.multi_spin.time_b import TimeButton

__all__ = ["WidgetClass"]


class WidgetClass(common.WidgetClass):
	def __init__(self, event: Event) -> None:  # FIXME
		common.WidgetClass.__init__(self, event)
		# ------
		sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# ------
		hbox = HBox()
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
		hbox = HBox()
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
		self.endDateHbox = HBox()
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
		# self.filesBox = common.FilesBox(self.event)
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
		startDate, startTime = self.event.getStart()
		self.startDateInput.set_value(startDate)
		self.startTimeInput.set_value(startTime)
		# ---
		endType, values = self.event.getEnd()
		if endType == "duration":
			self.endTypeCombo.set_active(0)
			self.durationBox.setDuration(*values)
			self.endDateInput.set_value(startDate)  # FIXME
			self.endTimeInput.set_value(startTime)  # FIXME
		elif endType == "date":
			self.endTypeCombo.set_active(1)
			self.endDateInput.set_value(values[0])
			self.endTimeInput.set_value(values[1])
		else:
			raise RuntimeError
		self.endTypeComboChanged()

	def updateVars(self) -> None:  # FIXME
		common.WidgetClass.updateVars(self)
		self.event.setStart(
			self.startDateInput.get_value(),
			self.startTimeInput.get_value(),
		)
		# ---
		active = self.endTypeCombo.get_active()
		if active == 0:
			self.event.setEnd("duration", *self.durationBox.getDuration())
		elif active == 1:
			self.event.setEnd(
				"date",
				self.endDateInput.get_value(),
				self.endTimeInput.get_value(),
			)

	def calTypeComboChanged(self, _widget: gtk.Widget | None = None) -> None:
		# overwrite method from common.WidgetClass
		newCalType = self.calTypeCombo.get_active()
		self.startDateInput.changeCalType(self.event.calType, newCalType)
		self.endDateInput.changeCalType(self.event.calType, newCalType)
		self.event.calType = newCalType
