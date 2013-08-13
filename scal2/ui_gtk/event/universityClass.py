# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2012 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_lib

from scal2 import ui
from scal2.ui_gtk.mywidgets import TextFrame
from scal2.ui_gtk.mywidgets.multi_spin_button import HourMinuteButtonOption
from scal2.ui_gtk.event import common
from scal2.ui_gtk.event.rules.weekNumMode import RuleWidget as WeekNumModeRuleWidget
from scal2.ui_gtk.utils import showError, WeekDayComboBox

import gtk
from gtk import gdk

class EventWidget(gtk.VBox):
    showTimeZone = True
    def __init__(self, event):## FIXME
        gtk.VBox.__init__(self)
        self.event = event
        assert event.parent.name == 'universityTerm' ## FIXME
        sizeGroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        #####
        if not event.parent.courses:
            showError(event.parent.noCourseError)
            raise RuntimeError('No courses added')
        self.courseIds = []
        self.courseNames = []
        combo = gtk.combo_box_new_text()
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
        hbox.pack_start(label, 0, 0)
        hbox.pack_start(combo, 0, 0)
        ##
        self.pack_start(hbox, 0, 0)
        #####
        hbox = gtk.HBox()
        label = gtk.Label(_('Week'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        self.weekNumModeCombo = WeekNumModeRuleWidget(event['weekNumMode'])
        hbox.pack_start(self.weekNumModeCombo, 0, 0)
        self.pack_start(hbox, 0, 0)
        #####
        hbox = gtk.HBox()
        label = gtk.Label(_('Week Day'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        self.weekDayCombo = WeekDayComboBox()
        #self.weekDayCombo.connect('changed', self.updateSummary)
        hbox.pack_start(self.weekDayCombo, 0, 0)
        self.pack_start(hbox, 0, 0)
        #####
        hbox = gtk.HBox()
        label = gtk.Label(_('Time'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        ##
        self.dayTimeStartCombo = HourMinuteButtonOption()
        self.dayTimeEndCombo = HourMinuteButtonOption()
        ##
        #self.dayTimeStartCombo.child.set_direction(gtk.TEXT_DIR_LTR)
        #self.dayTimeEndCombo.child.set_direction(gtk.TEXT_DIR_LTR)
        ##
        hbox.pack_start(self.dayTimeStartCombo, 0, 0)
        hbox.pack_start(gtk.Label(' ' + _('to') + ' '), 0, 0)
        hbox.pack_start(self.dayTimeEndCombo, 0, 0)
        self.pack_start(hbox, 0, 0)
        ###########
        #hbox = gtk.HBox()
        #label = gtk.Label(_('Summary'))
        #label.set_alignment(0, 0.5)
        #sizeGroup.add_widget(label)
        #hbox.pack_start(label, 0, 0)
        #self.summaryEntry = gtk.Entry()
        #hbox.pack_start(self.summaryEntry, 1, 1)
        #self.pack_start(hbox, 0, 0)
        #####
        hbox = gtk.HBox()
        label = gtk.Label(_('Description'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        self.descriptionInput = TextFrame()
        hbox.pack_start(self.descriptionInput, 1, 1)
        self.pack_start(hbox, 0, 0)
        #####
        hbox = gtk.HBox()
        label = gtk.Label(_('Icon'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        self.iconSelect = common.IconSelectButton()
        #print join(pixDir, self.icon)
        hbox.pack_start(self.iconSelect, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.pack_start(hbox, 0, 0)
        ######
        self.notificationBox = common.NotificationBox(event)
        self.pack_start(self.notificationBox, 0, 0)
        ######
        #self.filesBox = common.FilesBox(self.event)
        #self.pack_start(self.filesBox, 0, 0)
        ######
        self.courseCombo.set_active(0)
        #self.updateSummary()
    def focusSummary(self):
        pass
    #def updateSummary(self, widget=None):
    #    courseIndex = self.courseCombo.get_active()
    #    summary = _('%s Class')%self.courseNames[courseIndex] + ' (' + self.weekDayCombo.get_active_text() + ')'
    #    self.summaryEntry.set_text(summary)
    #    self.event.summary = summary
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
            showError(_('No course is selected'), self)
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



