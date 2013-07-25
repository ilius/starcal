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

from scal2.cal_types import jd_to
from scal2 import core
from scal2.locale_man import tr as _


from scal2 import ui
from scal2.ui_gtk.mywidgets.multi_spin_button import IntSpinButton, DateButton, HourMinuteButton
from scal2.ui_gtk.event import common

import gtk

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
        self.startDateInput = DateButton()
        hbox.pack_start(self.startDateInput, 0, 0)
        ###
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.pack_start(hbox, 0, 0)
        ######
        hbox = gtk.HBox()
        label = gtk.Label(_('Repeat Every '))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        self.weeksSpin = IntSpinButton(1, 99999)
        hbox.pack_start(self.weeksSpin, 0, 0)
        hbox.pack_start(gtk.Label('  '+_(' Weeks')), 0, 0)
        ###
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.pack_start(hbox, 0, 0)
        ######
        hbox = gtk.HBox()
        label = gtk.Label(_('End'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        self.endDateInput = DateButton()
        hbox.pack_start(self.endDateInput, 0, 0)
        ###
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.pack_start(hbox, 0, 0)
        #########
        hbox = gtk.HBox()
        label = gtk.Label(_('Time'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        ##
        self.dayTimeStartInput = HourMinuteButton()
        self.dayTimeEndInput = HourMinuteButton()
        ##
        hbox.pack_start(self.dayTimeStartInput, 0, 0)
        hbox.pack_start(gtk.Label(' ' + _('to') + ' '), 0, 0)
        hbox.pack_start(self.dayTimeEndInput, 0, 0)
        self.pack_start(hbox, 0, 0)
        #############
        #self.notificationBox = common.NotificationBox(event)
        #self.pack_start(self.notificationBox, 0, 0)
        #############
        #self.filesBox = common.FilesBox(self.event)
        #self.pack_start(self.filesBox, 0, 0)
    def updateWidget(self):## FIXME
        common.EventWidget.updateWidget(self)
        mode = self.event.mode
        ###
        self.startDateInput.set_value(jd_to(self.event.getStartJd(), mode))
        self.weeksSpin.set_value(self.event['cycleWeeks'].weeks)
        self.endDateInput.set_value(jd_to(self.event.getEndJd(), mode))
        ###
        timeRangeRule = self.event['dayTimeRange']
        self.dayTimeStartInput.set_value(timeRangeRule.dayTimeStart)
        self.dayTimeEndInput.set_value(timeRangeRule.dayTimeEnd)
    def updateVars(self):## FIXME
        common.EventWidget.updateVars(self)
        self.event['start'].setDate(self.startDateInput.get_value())
        self.event['end'].setDate(self.endDateInput.get_value())
        self.event['cycleWeeks'].setData(self.weeksSpin.get_value())
        ###
        self.event['dayTimeRange'].setRange(
            self.dayTimeStartInput.get_value(),
            self.dayTimeEndInput.get_value(),
        )
    def modeComboChanged(self, obj=None):## overwrite method from common.EventWidget
        newMode = self.modeCombo.get_active()
        self.startDateInput.changeMode(self.event.mode, newMode)
        self.endDateInput.changeMode(self.event.mode, newMode)
        self.event.mode = newMode



