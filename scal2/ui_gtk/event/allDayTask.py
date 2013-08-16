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

from scal2.cal_types import jd_to, to_jd
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import ui
from scal2.ui_gtk.mywidgets.multi_spin_button import DateButton, IntSpinButton
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
        ##
        self.pack_start(hbox, 0, 0)
        ######
        hbox = gtk.HBox()
        self.endTypeCombo = gtk.combo_box_new_text()
        for item in ('Duration', 'End'):
            self.endTypeCombo.append_text(_(item))
        self.endTypeCombo.connect('changed', self.endTypeComboChanged)
        sizeGroup.add_widget(self.endTypeCombo)
        hbox.pack_start(self.endTypeCombo, 0, 0)
        ####
        self.durationBox = gtk.HBox()
        self.durationSpin = IntSpinButton(1, 999)
        self.durationBox.pack_start(self.durationSpin, 0, 0)
        self.durationBox.pack_start(gtk.Label(_(' days')), 0, 0)
        hbox.pack_start(self.durationBox, 0, 0)
        ####
        self.endDateInput = DateButton()
        hbox.pack_start(self.endDateInput, 0, 0)
        ####
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.pack_start(hbox, 0, 0)
        #############
        self.notificationBox = common.NotificationBox(event)
        self.pack_start(self.notificationBox, 0, 0)
        #############
        #self.filesBox = common.FilesBox(self.event)
        #self.pack_start(self.filesBox, 0, 0)
    def endTypeComboChanged(self, combo=None):
        active = self.endTypeCombo.get_active()
        if active==0:## duration
            self.durationBox.show()
            self.endDateInput.hide()
        elif active==1:## end date
            self.durationBox.hide()
            self.endDateInput.show()
        else:
            raise RuntimeError
    def updateWidget(self):## FIXME
        common.EventWidget.updateWidget(self)
        mode = self.event.mode
        ###
        startJd = self.event.getJd()
        self.startDateInput.set_value(jd_to(startJd, mode))
        ###
        endType, endValue = self.event.getEnd()
        if endType=='duration':
            self.endTypeCombo.set_active(0)
            self.durationSpin.set_value(endValue)
            self.endDateInput.set_value(jd_to(self.event.getEndJd(), mode))## FIXME
        elif endType=='date':
            self.endTypeCombo.set_active(1)
            self.endDateInput.set_value(endValue)
        else:
            raise RuntimeError
        self.endTypeComboChanged()
    def updateVars(self):## FIXME
        common.EventWidget.updateVars(self)
        self.event.setStartDate(self.startDateInput.get_value())
        ###
        active = self.endTypeCombo.get_active()
        if active==0:
            self.event.setEnd('duration', self.durationSpin.get_value())
        elif active==1:
            self.event.setEnd(
                'date',
                self.endDateInput.get_value(),
            )
    def modeComboChanged(self, obj=None):## overwrite method from common.EventWidget
        newMode = self.modeCombo.get_active()
        self.startDateInput.changeMode(self.event.mode, newMode)
        self.endDateInput.changeMode(self.event.mode, newMode)
        self.event.mode = newMode



