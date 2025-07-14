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
from scal3.event_lib.rules import (
	DayTimeRangeEventRule,
	WeekDayEventRule,
	WeekNumberModeEventRule,
)
from scal3.event_lib.university import UniversityTerm

log = logger.get()

from typing import TYPE_CHECKING

from scal3 import ui
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.event import common
from scal3.ui_gtk.event.rule.weekNumMode import WidgetClass as WeekNumModeWidgetClass
from scal3.ui_gtk.mywidgets import TextFrame
from scal3.ui_gtk.mywidgets.icon import IconSelectButton
from scal3.ui_gtk.mywidgets.multi_spin.option_box.hour_minute import (
	HourMinuteButtonOption,
)
from scal3.ui_gtk.mywidgets.weekday_combo import WeekDayComboBox
from scal3.ui_gtk.utils import showError

if TYPE_CHECKING:
	from scal3.event_lib.university import UniversityClassEvent

__all__ = ["WidgetClass"]


class WidgetClass(gtk.Box):
	def show(self) -> None:
		gtk.Box.show_all(self)

	def __init__(self, event: UniversityClassEvent) -> None:  # FIXME
		assert isinstance(event.parent, UniversityTerm), f"{event.parent=}"
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.w = self
		self._event = event
		sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# -----
		if not event.parent.courses:
			showError(event.parent.noCourseError, transient_for=ui.eventManDialog.w)
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
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Course"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		pack(hbox, combo)
		# --
		pack(self, hbox)
		# -----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Week"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		weekNumModeRule = WeekNumberModeEventRule.getFrom(event)
		if weekNumModeRule is None:
			raise RuntimeError("no weekNumMode rule")
		self.weekNumModeCombo = WeekNumModeWidgetClass(weekNumModeRule)
		pack(hbox, self.weekNumModeCombo)
		pack(self, hbox)
		# -----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Week Day"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.weekDayCombo = WeekDayComboBox()
		# self.weekDayCombo.connect("changed", self.updateSummary)
		pack(hbox, self.weekDayCombo)
		pack(self, hbox)
		# -----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Time"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		# --
		self.dayTimeStartCombo = HourMinuteButtonOption()
		self.dayTimeEndCombo = HourMinuteButtonOption()
		# --
		# self.dayTimeStartCombo.get_child().set_direction(gtk.TextDirection.LTR)
		# self.dayTimeEndCombo.get_child().set_direction(gtk.TextDirection.LTR)
		# --
		pack(hbox, self.dayTimeStartCombo)
		pack(hbox, gtk.Label(label=" " + _("To", ctx="time range") + " "))
		pack(hbox, self.dayTimeEndCombo)
		pack(self, hbox)
		# -----------
		# hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		# label = gtk.Label(label=_("Summary"))
		# label.set_xalign(0)
		# sizeGroup.add_widget(label)
		# pack(hbox, label)
		# self.summaryEntry = gtk.Entry()
		# pack(hbox, self.summaryEntry, 1, 1)
		# pack(self, hbox)
		# -----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Description"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.descriptionInput = TextFrame()
		pack(hbox, self.descriptionInput, 1, 1)
		pack(self, hbox)
		# -----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
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
		# self.filesBox = common.FilesBox(self._event)
		# pack(self, self.filesBox)
		# ------
		self.courseCombo.set_active(0)
		# self.updateSummary()

	def focusSummary(self) -> None:
		pass

	# def updateSummary(self, widget=None):
	# 	courseIndex = self.courseCombo.getActive()
	# 	summary = (
	# 		_("{courseName} Class").format(
	# 			courseName=self.courseNames[courseIndex],
	# 		) +
	# 		" (" +
	# 		self.weekDayCombo.getActive_text() +
	# 		")"
	# 	)
	# 	self.summaryEntry.set_text(summary)
	# 	self._event.summary = summary

	def updateWidget(self) -> None:  # FIXME
		assert isinstance(self._event.parent, UniversityTerm), f"{self._event.parent=}"
		if self._event.courseId is None:
			pass
		else:
			self.courseCombo.set_active(self.courseIds.index(self._event.courseId))
		# --
		self.weekNumModeCombo.updateWidget()
		weekDayRule = WeekDayEventRule.getFrom(self._event)
		if weekDayRule is None:
			raise RuntimeError("no weekDay rule")
		weekDayList = weekDayRule.weekDayList
		if len(weekDayList) == 1:
			self.weekDayCombo.setValue(weekDayList[0])  # FIXME
		else:
			self.weekDayCombo.set_active(0)
		# --
		self.dayTimeStartCombo.clear_history()
		self.dayTimeEndCombo.clear_history()
		for hm in reversed(self._event.parent.classTimeBounds):
			for combo in (self.dayTimeStartCombo, self.dayTimeEndCombo):
				combo.set_value(hm)
				combo.add_history()
		timeRangeRule = DayTimeRangeEventRule.getFrom(self._event)
		if timeRangeRule is None:
			raise RuntimeError("no dayTimeRange rule")
		self.dayTimeStartCombo.set_value(timeRangeRule.dayTimeStart)
		self.dayTimeEndCombo.set_value(timeRangeRule.dayTimeEnd)
		# ----
		# self.summaryEntry.set_text(self._event.summary)
		self.descriptionInput.set_text(self._event.description)
		self.iconSelect.set_filename(self._event.icon)
		# ----
		self.notificationBox.updateWidget()
		# ----
		# self.filesBox.updateWidget()

	def updateVars(self) -> None:  # FIXME
		courseIndex = self.courseCombo.get_active()
		if courseIndex is None:
			showError(_("No course is selected"), transient_for=ui.eventManDialog.w)
			raise RuntimeError("No courses is selected")
		self._event.courseId = self.courseIds[courseIndex]
		# --
		self.weekNumModeCombo.updateVars()
		# --
		weekDay = WeekDayEventRule.getFrom(self._event)
		if weekDay is None:
			raise RuntimeError("no weekDay rule")
		weekDay.weekDayList = [self.weekDayCombo.getValue()]  # FIXME
		# --
		dayTimeRange = DayTimeRangeEventRule.getFrom(self._event)
		if dayTimeRange is None:
			raise RuntimeError("no dayTimeRange rule")
		h1, m1 = self.dayTimeStartCombo.get_value()
		h2, m2 = self.dayTimeEndCombo.get_value()
		dayTimeRange.setRange(
			(h1, m1, 0),
			(h2, m2, 0),
		)
		# ----
		# self._event.summary = self.summaryEntry.get_text()
		self._event.description = self.descriptionInput.get_text()
		self._event.icon = self.iconSelect.get_filename()
		# ----
		self.notificationBox.updateVars()
		self._event.updateSummary()
