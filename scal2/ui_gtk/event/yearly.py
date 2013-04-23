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

from scal2.cal_types import calTypes
from scal2 import core
from scal2.core import convert
from scal2.locale_man import tr as _

from scal2 import event_lib
import gtk
from gtk import gdk

from scal2.ui_gtk.utils import MonthComboBox
from scal2.ui_gtk.mywidgets.multi_spin_button import YearSpinButton, DaySpinButton
from scal2.ui_gtk.event import common


class EventWidget(common.EventWidget):
    def __init__(self, event):## FIXME
        common.EventWidget.__init__(self, event)
        ################
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Month')), 0, 0)
        self.monthCombo = MonthComboBox()
        self.monthCombo.build(event.mode)
        hbox.pack_start(self.monthCombo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        #self.pack_start(hbox, 0, 0)
        ###
        #hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Day')), 0, 0)
        self.daySpin = DaySpinButton()
        hbox.pack_start(self.daySpin, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.pack_start(hbox, 0, 0)
        ###
        hbox = gtk.HBox()
        self.startYearCheck = gtk.CheckButton(_('Start Year'))
        hbox.pack_start(self.startYearCheck, 0, 0)
        self.startYearSpin = YearSpinButton()
        hbox.pack_start(self.startYearSpin, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.pack_start(hbox, 0, 0)
        self.startYearCheck.connect('clicked', self.startYearCheckClicked)
        ####
        self.notificationBox = common.NotificationBox(event)
        self.pack_start(self.notificationBox, 0, 0)
        ####
        #self.filesBox = common.FilesBox(self.event)
        #self.pack_start(self.filesBox, 0, 0)
    startYearCheckClicked = lambda self, obj=None: self.startYearSpin.set_sensitive(self.startYearCheck.get_active())
    def updateWidget(self):## FIXME
        common.EventWidget.updateWidget(self)
        self.monthCombo.setValue(self.event.getMonth())
        self.daySpin.set_value(self.event.getDay())
        try:
            startRule = self.event['start']
        except:
            self.startYearCheck.set_active(False)
            self.startYearSpin.set_value(self.event.getSuggestedStartYear())
        else:
            self.startYearCheck.set_active(True)
            self.startYearSpin.set_value(startRule.date[0])
        self.startYearCheckClicked()
    def updateVars(self):## FIXME
        common.EventWidget.updateVars(self)
        self.event.setMonth(self.monthCombo.getValue())
        self.event.setDay(int(self.daySpin.get_value()))
        if self.startYearCheck.get_active():
            startRule = self.event.getAddRule('start')
            startRule.date = (self.startYearSpin.get_value(), 1, 1)
        else:
            try:
                del self.event['start']
            except KeyError:
                pass
    def modeComboChanged(self, obj=None):## overwrite method from common.EventWidget
        newMode = self.modeCombo.get_active()
        module = calTypes[newMode]
        monthCombo = self.monthCombo
        month = monthCombo.getValue()
        monthCombo.build(newMode)
        y2, m2, d2 = convert(
            int(self.startYearSpin.get_value()),
            month,
            int(self.daySpin.get_value()),
            self.event.mode,
            newMode,
        )
        self.startYearSpin.set_value(y2)
        monthCombo.setValue(m2)
        self.daySpin.set_value(d2)
        self.event.mode = newMode
        


