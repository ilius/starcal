#!/usr/bin/env python
# -*- coding: utf-8 -*-

from scal2.cal_types import convert
from scal2 import core
from scal2.locale_man import tr as _
from scal2 import event_lib
from scal2 import ui

from scal2.ui_gtk import *
from scal2.ui_gtk.mywidgets.multi_spin_button import DateButton
from scal2.ui_gtk.event import common


class EventWidget(common.EventWidget):
    def __init__(self, event):
        common.EventWidget.__init__(self, event)
        ###
        hbox = gtk.HBox()
        pack(hbox, gtk.Label(_('Date')))
        self.dateInput = DateButton()
        pack(hbox, self.dateInput)
        pack(self, hbox)
        #############
        #self.filesBox = common.FilesBox(self.event)
        #pack(self, self.filesBox)
    def updateWidget(self):
        common.EventWidget.updateWidget(self)
        self.dateInput.set_value(self.event.getDate())
    def updateVars(self):
        common.EventWidget.updateVars(self)
        self.event.setDate(*self.dateInput.get_value())
    def modeComboChanged(self, obj=None):## overwrite method from common.EventWidget
        newMode = self.modeCombo.get_active()
        self.dateInput.changeMode(self.event.mode, newMode)
        self.event.mode = newMode



