# -*- coding: utf-8 -*-

from scal2.core import jd_to
from scal2.locale_man import tr as _

from scal2.ui_gtk import *
from scal2.ui_gtk.mywidgets import MyColorButton
from scal2.ui_gtk.mywidgets.multi_spin_button import DateButton
from scal2.ui_gtk.event.groups.base import BaseGroupWidget


class GroupWidget(BaseGroupWidget):
    def __init__(self, group):
        BaseGroupWidget.__init__(self, group)
        ####
        hbox = gtk.HBox()
        label = gtk.Label(_('Start'))
        label.set_alignment(0, 0.5)
        pack(hbox, label)
        self.sizeGroup.add_widget(label)
        self.startDateInput = DateButton()
        pack(hbox, self.startDateInput)
        pack(self, hbox)
        ###
        hbox = gtk.HBox()
        label = gtk.Label(_('End'))
        label.set_alignment(0, 0.5)
        pack(hbox, label)
        self.sizeGroup.add_widget(label)
        self.endDateInput = DateButton()
        pack(hbox, self.endDateInput)
        pack(self, hbox)
    def updateWidget(self):
        BaseGroupWidget.updateWidget(self)
        self.startDateInput.set_value(jd_to(self.group.startJd, self.group.mode))
        self.endDateInput.set_value(jd_to(self.group.endJd, self.group.mode))
    def updateVars(self):
        BaseGroupWidget.updateVars(self)
        self.group.startJd = self.startDateInput.get_jd(self.group.mode)
        self.group.endJd = self.endDateInput.get_jd(self.group.mode)
    def modeComboChanged(self, obj=None):
        newMode = self.modeCombo.get_active()
        self.startDateInput.changeMode(self.group.mode, newMode)
        self.endDateInput.changeMode(self.group.mode, newMode)
        self.group.mode = newMode



