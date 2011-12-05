#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_man

from scal2 import ui
from scal2.ui_gtk.mywidgets.multi_spin_button import DateButton, TimeButton
from scal2.ui_gtk.event import common

import gtk
from gtk import gdk

class EventWidget(common.EventWidget):
    def __init__(self, event):## FIXME
        common.EventWidget.__init__(self, event)
        ######
        sizeGroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        ######
        hbox = gtk.HBox()
        label = gtk.Label(_('Start'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        self.startDateInput = DateButton(lang=core.langSh)
        hbox.pack_start(self.startDateInput, 0, 0)
        ##
        hbox.pack_start(gtk.Label(' '+_('Time')), 0, 0)
        self.startTimeInput = TimeButton(lang=core.langSh)
        hbox.pack_start(self.startTimeInput, 0, 0)
        ##
        self.pack_start(hbox, 0, 0)
        ######
        hbox = gtk.HBox()
        self.endTypeCombo = gtk.combo_box_new_text()
        for item in ('---', 'Duration', 'End'):
            self.endTypeCombo.append_text(_(item))
        self.endTypeCombo.connect('changed', self.endTypeComboChanged)
        sizeGroup.add_widget(self.endTypeCombo)
        hbox.pack_start(self.endTypeCombo, 0, 0)
        ####
        self.durationBox = common.DurationInputBox()
        hbox.pack_start(self.durationBox, 1, 1)
        ####
        self.endDateHbox = gtk.HBox()
        self.endDateInput = DateButton(lang=core.langSh)
        self.endDateHbox.pack_start(self.endDateInput, 0, 0)
        ##
        self.endDateHbox.pack_start(gtk.Label(' '+_('Time')), 0, 0)
        self.endTimeInput = TimeButton(lang=core.langSh)
        self.endDateHbox.pack_start(self.endTimeInput, 0, 0)
        ##
        hbox.pack_start(self.endDateHbox, 1, 1)
        ####
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.pack_start(hbox, 0, 0)
        #############
        self.notificationBox = common.NotificationBox(event)
        self.pack_start(self.notificationBox, 0, 0)
        #############
        self.filesBox = common.FilesBox(self.event)
        self.pack_start(self.filesBox, 0, 0)
    def endTypeComboChanged(self, combo=None):
        active = self.endTypeCombo.get_active()
        if active==0:
            self.durationBox.hide()
            self.endDateHbox.hide()
        elif active==1:## duration
            self.durationBox.show()
            self.endDateHbox.hide()
        elif active==2:## end date
            self.durationBox.hide()
            self.endDateHbox.show()
        else:
            raise RuntimeError
    def updateWidget(self):## FIXME
        common.EventWidget.updateWidget(self)
        ###
        (startDate, startTime) = self.event.getStart()
        self.startDateInput.set_date(startDate)
        self.startTimeInput.set_time(startTime)
        ###
        (endType, values) = self.event.getEnd()
        if not endType:
            self.endTypeCombo.set_active(0)
            self.endDateInput.set_date(startDate)
            self.endTimeInput.set_time(startTime)
        elif endType=='duration':
            self.endTypeCombo.set_active(1)
            self.durationBox.setDuration(*values)
            self.endDateInput.set_date(startDate)## FIXME
            self.endTimeInput.set_time(startTime)## FIXME
        elif endType=='end':
            self.endTypeCombo.set_active(2)
            self.endDateInput.set_date(values[0])
            self.endTimeInput.set_time(values[1])
        else:
            raise RuntimeError
        self.endTypeComboChanged()
        ###
        self.notificationBox.updateWidget()
    def updateVars(self):## FIXME
        common.EventWidget.updateVars(self)
        self.event.setStart(self.startDateInput.get_date(), self.startTimeInput.get_time())
        ###
        active = self.endTypeCombo.get_active()
        if active==0:
            self.event.setEnd(None)
        elif active==1:
            self.event.setEnd('duration', *self.durationBox.getDuration())
        elif active==2:
            self.event.setEnd(
                'date',
                self.endDateInput.get_date(),
                self.endTimeInput.get_time(),
            )
        ###
        self.notificationBox.updateVars()




