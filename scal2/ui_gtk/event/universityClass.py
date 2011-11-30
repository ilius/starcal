#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_man

from scal2 import ui
from scal2.ui_gtk.event import common
from scal2.ui_gtk.event.rules.weekNumMode import RuleWidget as WeekNumModeRuleWidget
from scal2.ui_gtk.utils import showError, WeekDayComboBox

import gtk
from gtk import gdk

class EventWidget(common.EventWidget):
    def __init__(self, event):## FIXME
        common.EventWidget.__init__(self, event)
        assert event.group and event.group.name == 'universityTerm' ## FIXME
        sizeGroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        #####
        if not event.group.courses:
            showError(_('Edit University Term and add some Courses before you add a Class'))
            raise RuntimeError('No courses added')
        self.courseIds = []
        #self.courseNames = []
        combo = gtk.combo_box_new_text()
        for course in event.group.courses:
            self.courseIds.append(course[0])
            #self.courseNames.append(course[1])
            combo.append_text(course[1])
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
        hbox.pack_start(self.weekDayCombo, 0, 0)
        self.pack_start(hbox, 0, 0)
    def updateWidget(self):## FIXME
        common.EventWidget.updateWidget(self)
        ##
        if self.event.courseId is None:
            pass
        else:
            self.courseCombo.set_active(self.courseIds.index(self.event.courseId))
        ##
        self.weekNumModeCombo.updateWidget()
        self.weekDayCombo.setValue(self.event['weekDay'].weekDayList[0])## FIXME
    def updateVars(self):## FIXME
        common.EventWidget.updateVars(self)
        ##
        courseIndex = self.courseCombo.get_active()
        if courseIndex is None:
            showError(_('No course is selected'), self)
            raise RuntimeError('No courses is selected')
        else:
            self.event.courseId = self.courseIds[courseIndex]
        ##
        self.weekNumModeCombo.updateVars()
        self.event['weekDay'].weekDayList = [self.weekDayCombo.getValue()]## FIXME
        




