# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from scal3 import core
from scal3.locale_man import tr as _
from scal3 import event_lib
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import showError
from scal3.ui_gtk.mywidgets import TextFrame
from scal3.ui_gtk.mywidgets.multi_spin.option_box.hour_minute import HourMinuteButtonOption
from scal3.ui_gtk.mywidgets.icon import IconSelectButton
from scal3.ui_gtk.mywidgets.weekday_combo import WeekDayComboBox
from scal3.ui_gtk.event import common
from scal3.ui_gtk.event.rule.weekNumMode import WidgetClass as WeekNumModeWidgetClass



class WidgetClass(gtk.VBox):
	def __init__(self, event):## FIXME
		gtk.VBox.__init__(self)
		self.event = event
		assert event.parent.name == 'universityTerm' ## FIXME
		sizeGroup = gtk.SizeGroup(gtk.SizeGroupMode.HORIZONTAL)
		#####
		if not event.parent.courses:
			showError(event.parent.noCourseError, ui.eventManDialog)
			raise RuntimeError('No courses added')
		self.courseIds = []
		self.courseNames = []
		combo = gtk.ComboBoxText()
		for course in event.parent.courses:
			self.courseIds.append(course[0])
			self.courseNames.append(course[1])
			combo.append_text(course[1])
		#combo.connect('changed', self.updateSummary)
		self.courseCombo = combo
		##
		hbox = gtk.HBox()
		label = gtk.Label(_('Course'))
		label.set_alignment(0, 0.5)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		pack(hbox, combo)
		##
		pack(self, hbox)
		#####
		hbox = gtk.HBox()
		label = gtk.Label(_('Week'))
		label.set_alignment(0, 0.5)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.weekNumModeCombo = WeekNumModeWidgetClass(event['weekNumMode'])
		pack(hbox, self.weekNumModeCombo)
		pack(self, hbox)
		#####
		hbox = gtk.HBox()
		label = gtk.Label(_('Week Day'))
		label.set_alignment(0, 0.5)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.weekDayCombo = WeekDayComboBox()
		#self.weekDayCombo.connect('changed', self.updateSummary)
		pack(hbox, self.weekDayCombo)
		pack(self, hbox)
		#####
		hbox = gtk.HBox()
		label = gtk.Label(_('Time'))
		label.set_alignment(0, 0.5)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		##
		self.dayTimeStartCombo = HourMinuteButtonOption()
		self.dayTimeEndCombo = HourMinuteButtonOption()
		##
		#self.dayTimeStartCombo.get_child().set_direction(gtk.TextDirection.LTR)
		#self.dayTimeEndCombo.get_child().set_direction(gtk.TextDirection.LTR)
		##
		pack(hbox, self.dayTimeStartCombo)
		pack(hbox, gtk.Label(' ' + _('to') + ' '))
		pack(hbox, self.dayTimeEndCombo)
		pack(self, hbox)
		###########
		#hbox = gtk.HBox()
		#label = gtk.Label(_('Summary'))
		#label.set_alignment(0, 0.5)
		#sizeGroup.add_widget(label)
		#pack(hbox, label)
		#self.summaryEntry = gtk.Entry()
		#pack(hbox, self.summaryEntry, 1, 1)
		#pack(self, hbox)
		#####
		hbox = gtk.HBox()
		label = gtk.Label(_('Description'))
		label.set_alignment(0, 0.5)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.descriptionInput = TextFrame()
		pack(hbox, self.descriptionInput, 1, 1)
		pack(self, hbox)
		#####
		hbox = gtk.HBox()
		label = gtk.Label(_('Icon'))
		label.set_alignment(0, 0.5)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.iconSelect = IconSelectButton()
		#print(join(pixDir, self.icon))
		pack(hbox, self.iconSelect)
		pack(hbox, gtk.Label(''), 1, 1)
		pack(self, hbox)
		######
		self.notificationBox = common.NotificationBox(event)
		pack(self, self.notificationBox)
		######
		#self.filesBox = common.FilesBox(self.event)
		#pack(self, self.filesBox)
		######
		self.courseCombo.set_active(0)
		#self.updateSummary()
	def focusSummary(self):
		pass
	#def updateSummary(self, widget=None):
	#	courseIndex = self.courseCombo.get_active()
	#	summary = _('%s Class')%self.courseNames[courseIndex] + ' (' + self.weekDayCombo.get_active_text() + ')'
	#	self.summaryEntry.set_text(summary)
	#	self.event.summary = summary
	def updateWidget(self):## FIXME
		if self.event.courseId is None:
			pass
		else:
			self.courseCombo.set_active(self.courseIds.index(self.event.courseId))
		##
		self.weekNumModeCombo.updateWidget()
		weekDayList = self.event['weekDay'].weekDayList
		if len(weekDayList)==1:
			self.weekDayCombo.setValue(weekDayList[0])## FIXME
		else:
			self.weekDayCombo.set_active(0)
		##
		self.dayTimeStartCombo.clear_history()
		self.dayTimeEndCombo.clear_history()
		for hm in reversed(self.event.parent.classTimeBounds):
			for combo in (self.dayTimeStartCombo, self.dayTimeEndCombo):
				combo.set_value(hm)
				combo.add_history()
		timeRangeRule = self.event['dayTimeRange']
		self.dayTimeStartCombo.set_value(timeRangeRule.dayTimeStart)
		self.dayTimeEndCombo.set_value(timeRangeRule.dayTimeEnd)
		####
		#self.summaryEntry.set_text(self.event.summary)
		self.descriptionInput.set_text(self.event.description)
		self.iconSelect.set_filename(self.event.icon)
		####
		self.notificationBox.updateWidget()
		####
		#self.filesBox.updateWidget()
	def updateVars(self):## FIXME
		courseIndex = self.courseCombo.get_active()
		if courseIndex is None:
			showError(_('No course is selected'), ui.eventManDialog)
			raise RuntimeError('No courses is selected')
		else:
			self.event.courseId = self.courseIds[courseIndex]
		##
		self.weekNumModeCombo.updateVars()
		self.event['weekDay'].weekDayList = [self.weekDayCombo.getValue()]## FIXME
		##
		self.event['dayTimeRange'].setRange(
			self.dayTimeStartCombo.get_value(),
			self.dayTimeEndCombo.get_value(),
		)
		####
		#self.event.summary = self.summaryEntry.get_text()
		self.event.description = self.descriptionInput.get_text()
		self.event.icon = self.iconSelect.get_filename()
		####
		self.notificationBox.updateVars()
		self.event.updateSummary()



