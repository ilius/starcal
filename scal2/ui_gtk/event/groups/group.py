# -*- coding: utf-8 -*-

from scal2.locale_man import tr as _
from scal2.core import jd_to

from scal2.ui_gtk.event.groups.base import BaseGroupWidget
from scal2.ui_gtk.mywidgets.multi_spin_button import DateButton


import gtk

from scal2.ui_gtk.mywidgets import MyColorButton

class GroupWidget(BaseGroupWidget):
    def __init__(self, group):
        BaseGroupWidget.__init__(self, group)
        ####
        hbox = gtk.HBox()
        label = gtk.Label(_('Start'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        self.sizeGroup.add_widget(label)
        self.startDateInput = DateButton()
        hbox.pack_start(self.startDateInput, 0, 0)
        self.pack_start(hbox, 0, 0)
        ###
        hbox = gtk.HBox()
        label = gtk.Label(_('End'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        self.sizeGroup.add_widget(label)
        self.endDateInput = DateButton()
        hbox.pack_start(self.endDateInput, 0, 0)
        self.pack_start(hbox, 0, 0)
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



