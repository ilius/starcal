#!/usr/bin/env python
# -*- coding: utf-8 -*-

from scal2.locale_man import tr as _

from scal2.ui_gtk.event import common
from scal2.ui_gtk.event.groups.group import GroupWidget as NormalGroupWidget

import gtk

class GroupWidget(NormalGroupWidget):
    def __init__(self, group):
        NormalGroupWidget.__init__(self, group)
        ###
        hbox = gtk.HBox()
        label = gtk.Label(_('Show Date in Event Summary'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        self.sizeGroup.add_widget(label)
        self.showDateCheck = gtk.CheckButton()
        hbox.pack_start(self.showDateCheck, 0, 0)
        self.pack_start(hbox, 0, 0)
    def updateWidget(self):## FIXME
        NormalGroupWidget.updateWidget(self)
        self.showDateCheck.set_active(self.group.showDate)
    def updateVars(self):
        NormalGroupWidget.updateVars(self)
        self.group.showDate = self.showDateCheck.get_active()


