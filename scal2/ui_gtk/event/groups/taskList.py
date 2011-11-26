#!/usr/bin/env python
# -*- coding: utf-8 -*-

from scal2.locale_man import tr as _

from scal2.ui_gtk.event import common
from scal2.ui_gtk.event.groups.group import GroupWidget as BaseGroupWidget

import gtk

class GroupWidget(BaseGroupWidget):
    def __init__(self, group):
        BaseGroupWidget.__init__(self, group)
        ###
        hbox = gtk.HBox()
        label = gtk.Label(_('Default Task Duration'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        self.sizeGroup.add_widget(label)
        self.defaultDurationBox = common.DurationInputBox()
        hbox.pack_start(self.defaultDurationBox, 0, 0)
        self.pack_start(hbox, 0, 0)
    def updateWidget(self):## FIXME
        BaseGroupWidget.updateWidget(self)
        self.defaultDurationBox.setDuration(*self.group.defaultDuration)
    def updateVars(self):
        BaseGroupWidget.updateVars(self)
        self.group.defaultDuration = self.defaultDurationBox.getDuration()


