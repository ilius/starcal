# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Saeed Rasooli <saeed.gnu@gmail.com>
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

from scal2 import ui
from scal2.ui_gtk.mywidgets.multi_spin_button import DateButton
from scal2.ui_gtk.mywidgets.ymd import YearMonthDayBox

from scal2.ui_gtk.event import common

import gtk

class EventWidget(common.EventWidget):
    def __init__(self, event):## FIXME
        common.EventWidget.__init__(self, event)
        ######
        sizeGroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        ######
        try:
            seperated = event.parent.showSeperatedYmdInputs
        except AttributeError:
            seperated = False
        if seperated:
            self.startDateInput = YearMonthDayBox()
            self.endDateInput = YearMonthDayBox()
        else:
            self.startDateInput = DateButton()
            self.endDateInput = DateButton()
        ######
        hbox = gtk.HBox()
        label = gtk.Label(_('Start')+': ')
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        hbox.pack_start(self.startDateInput, 0, 0)
        self.pack_start(hbox, 0, 0)
        ######
        hbox = gtk.HBox()
        label = gtk.Label(_('End')+': ')
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        hbox.pack_start(self.endDateInput, 0, 0)
        self.pack_start(hbox, 0, 0)
        #############
        #self.filesBox = common.FilesBox(self.event)
        #self.pack_start(self.filesBox, 0, 0)
    def updateWidget(self):
        common.EventWidget.updateWidget(self)
        self.startDateInput.set_value(self.event['start'].date)
        self.endDateInput.set_value(self.event['end'].date)
    def updateVars(self):## FIXME
        common.EventWidget.updateVars(self)
        self.event['start'].setDate(self.startDateInput.get_value())
        self.event['end'].setDate(self.endDateInput.get_value())
    def modeComboChanged(self, obj=None):## overwrite method from common.EventWidget
        newMode = self.modeCombo.get_active()
        self.startDateInput.changeMode(self.event.mode, newMode)
        self.endDateInput.changeMode(self.event.mode, newMode)
        self.event.mode = newMode












