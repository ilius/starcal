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

from scal3.cal_types import jd_to
from scal3.locale_man import tr as _
from scal3.ui_gtk import HBox, gtk, pack
from scal3.ui_gtk.event import common
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton

if TYPE_CHECKING:
	from scal3.event_lib.events import AllDayTaskEvent

__all__ = ["WidgetClass"]


class WidgetClass(common.WidgetClass):
	_event: AllDayTaskEvent

	def __init__(self, event: AllDayTaskEvent) -> None:  # FIXME
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
		self.durationBox = HBox()
		self.durationSpin = IntSpinButton(1, 999)
		pack(self.durationBox, self.durationSpin)
		pack(self.durationBox, gtk.Label(label=_(" days")))
		pack(hbox, self.durationBox)
		# ----
		self.endDateInput = DateButton()
		pack(hbox, self.endDateInput)
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
			self.endDateInput.hide()
		elif active == 1:  # end date
			self.durationBox.hide()
			self.endDateInput.show()
		else:
			raise RuntimeError

	def updateWidget(self) -> None:  # FIXME
		common.WidgetClass.updateWidget(self)
		calType = self._event.calType
		# ---
		startJd = self._event.getJd()
		self.startDateInput.set_value(jd_to(startJd, calType))
		# ---
		endType, endValue = self._event.getEnd()
		if endType == "duration":
			self.endTypeCombo.set_active(0)
			self.durationSpin.set_value(endValue)  # type: ignore[arg-type]
			self.endDateInput.set_value(jd_to(self._event.getEndJd(), calType))
			# ^ FIXME
		elif endType == "date":
			self.endTypeCombo.set_active(1)
			self.endDateInput.set_value(endValue)  # type: ignore[arg-type]
		else:
			raise RuntimeError
		self.endTypeComboChanged()

	def updateVars(self) -> None:  # FIXME
		common.WidgetClass.updateVars(self)
		self._event.setStartDate(self.startDateInput.getDate())
		# ---
		active = self.endTypeCombo.get_active()
		if active == 0:
			self._event.setEnd("duration", self.durationSpin.get_value())
		elif active == 1:
			self._event.setEnd(
				"date",
				self.endDateInput.getDate(),
			)

	def calTypeComboChanged(self, _w: gtk.Widget | None = None) -> None:
		# overwrite method from common.WidgetClass
		newCalType = self.calTypeCombo.get_active()
		assert newCalType is not None
		self.startDateInput.changeCalType(self._event.calType, newCalType)
		self.endDateInput.changeCalType(self._event.calType, newCalType)
		self._event.calType = newCalType
