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

from scal3 import logger
from scal3.event_lib.groups import UniversityTerm
from scal3.event_lib.rules import DayTimeRangeEventRule

log = logger.get()

from typing import TYPE_CHECKING

from scal3 import ui
from scal3.locale_man import tr as _
from scal3.ui_gtk import HBox, gtk, pack
from scal3.ui_gtk.event import common
from scal3.ui_gtk.mywidgets import TextFrame
from scal3.ui_gtk.mywidgets.icon import IconSelectButton
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.mywidgets.multi_spin.hour_minute import HourMinuteButton
from scal3.ui_gtk.utils import showError

if TYPE_CHECKING:
	from scal3.event_lib.events import UniversityExamEvent

__all__ = ["WidgetClass"]


class WidgetClass(gtk.Box):
	def __init__(self, event: UniversityExamEvent) -> None:  # FIXME
		assert isinstance(event.parent, UniversityTerm)
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.event = event
		sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# -----
		if not event.parent.courses:
			showError(event.parent.noCourseError, transient_for=ui.eventManDialog)
			raise RuntimeError("No courses added")
		self.courseIds = []
		self.courseNames = []
		combo = gtk.ComboBoxText()
		for course in event.parent.courses:
			self.courseIds.append(course[0])
			self.courseNames.append(course[1])
			combo.append_text(course[1])
		# combo.connect("changed", self.updateSummary)
		self.courseCombo = combo
		# --
		hbox = HBox()
		label = gtk.Label(label=_("Course"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		pack(hbox, combo)
		# --
		pack(self, hbox)
		# -----
		hbox = HBox()
		label = gtk.Label(label=_("Date"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.dateInput = DateButton()
		pack(hbox, self.dateInput)
		pack(self, hbox)
		# -----
		hbox = HBox()
		label = gtk.Label(label=_("Time"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		# --
		self.dayTimeStartCombo = HourMinuteButton()
		self.dayTimeEndCombo = HourMinuteButton()
		# --
		# self.dayTimeStartCombo.get_child().set_direction(gtk.TextDirection.LTR)
		# self.dayTimeEndCombo.get_child().set_direction(gtk.TextDirection.LTR)
		# --
		pack(hbox, self.dayTimeStartCombo)
		pack(hbox, gtk.Label(label=" " + _("To", ctx="time range") + " "))
		pack(hbox, self.dayTimeEndCombo)
		pack(self, hbox)
		# -----------
		# hbox = HBox()
		# label = gtk.Label(label=_("Summary"))
		# label.set_xalign(0)
		# sizeGroup.add_widget(label)
		# pack(hbox, label)
		# self.summaryEntry = gtk.Entry()
		# pack(hbox, self.summaryEntry, 1, 1)
		# pack(self, hbox)
		# -----
		hbox = HBox()
		label = gtk.Label(label=_("Description"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.descriptionInput = TextFrame()
		pack(hbox, self.descriptionInput, 1, 1)
		pack(self, hbox)
		# -----
		hbox = HBox()
		label = gtk.Label(label=_("Icon"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.iconSelect = IconSelectButton()
		# log.debug(join(pixDir, self.icon))
		pack(hbox, self.iconSelect)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		# ------
		self.notificationBox = common.NotificationBox(event)
		pack(self, self.notificationBox)
		# ------
		# self.filesBox = common.FilesBox(self.event)
		# pack(self, self.filesBox)
		# ------
		self.courseCombo.set_active(0)
		# self.updateSummary()

	def focusSummary(self) -> None:
		pass

	# def updateSummary(self, widget=None):
	# 	courseIndex = self.courseCombo.get_active()
	# 	summary = _("{courseName} Exam").format(
	# 		courseName=self.courseNames[courseIndex],
	# 	)
	# 	self.summaryEntry.set_text(summary)
	# 	self.event.summary = summary

	def updateWidget(self) -> None:  # FIXME
		if self.event.courseId is None:
			pass
		else:
			courseIndex = self.courseIds.index(self.event.courseId)
			assert courseIndex >= 0
			self.courseCombo.set_active(courseIndex)
		# --
		date = self.event.getDate()
		assert date is not None
		self.dateInput.setDate(date)
		# --
		timeRangeRule = DayTimeRangeEventRule.getFrom(self.event)
		if timeRangeRule is None:
			raise RuntimeError("no dayTimeRange rule")
		self.dayTimeStartCombo.set_value(timeRangeRule.dayTimeStart)
		self.dayTimeEndCombo.set_value(timeRangeRule.dayTimeEnd)
		# ----
		# self.summaryEntry.set_text(self.event.summary)
		self.descriptionInput.set_text(self.event.description)
		self.iconSelect.set_filename(self.event.icon)
		# ----
		self.notificationBox.updateWidget()
		# ----
		# self.filesBox.updateWidget()

	def updateVars(self) -> None:  # FIXME
		courseIndex = self.courseCombo.get_active()
		if courseIndex is None:
			showError(_("No course is selected"), transient_for=ui.eventManDialog)
			raise RuntimeError("No courses is selected")
		self.event.courseId = self.courseIds[courseIndex]
		# --
		self.event.setDate(*self.dateInput.get_value())
		# --
		timeRangeRule = DayTimeRangeEventRule.getFrom(self.event)
		if timeRangeRule is None:
			raise RuntimeError("no dayTimeRange rule")
		h1, m1 = self.dayTimeStartCombo.get_value()
		h2, m2 = self.dayTimeEndCombo.get_value()
		timeRangeRule.setRange(
			(h1, m1, 0),
			(h2, m2, 0),
		)
		# ----
		# self.event.summary = self.summaryEntry.get_text()
		self.event.description = self.descriptionInput.get_text()
		self.event.icon = self.iconSelect.get_filename()
		# ----
		self.notificationBox.updateVars()
		self.event.updateSummary()

	def calTypeComboChanged(self, _w: gtk.Widget | None = None) -> None:
		# overwrite method from common.WidgetClass
		newCalType = self.calTypeCombo.get_active()
		self.dateInput.changeCalType(self.event.calType, newCalType)
		self.event.calType = newCalType
