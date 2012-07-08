#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_man

from scal2 import ui
from scal2.ui_gtk.event import common

import gtk
from gtk import gdk

from scal2.ui_gtk.mywidgets.multi_spin_button import IntSpinButton

maxStart = 999999
maxDur = 99999

class EventWidget(common.EventWidget):
    def __init__(self, event):## FIXME
        common.EventWidget.__init__(self, event)
        ######
        sizeGroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        ######
        hbox = gtk.HBox()
        label = gtk.Label(_('Scale'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        self.scaleCombo = common.Scale10PowerComboBox()
        hbox.pack_start(self.scaleCombo, 0, 0)
        self.pack_start(hbox, 0, 0)
        ####
        hbox = gtk.HBox()
        label = gtk.Label(_('Start'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        self.startSpin = IntSpinButton(-maxStart, maxStart)
        hbox.pack_start(self.startSpin, 0, 0)
        self.pack_start(hbox, 0, 0)
        ####
        hbox = gtk.HBox()
        label = gtk.Label(_('Duration'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        self.durationSpin = IntSpinButton(0, maxDur)
        hbox.pack_start(self.durationSpin, 0, 0)
        self.pack_start(hbox, 0, 0)
        ####
    def updateWidget(self):
        common.EventWidget.updateWidget(self)
        self.scaleCombo.set_value(self.event.scale)
        self.startSpin.set_value(self.event.start)
        self.durationSpin.set_value(self.event.duration)
    def updateVars(self):## FIXME
        common.EventWidget.updateVars(self)
        self.event.scale = self.scaleCombo.get_value()
        self.event.start = self.startSpin.get_value()
        self.event.duration = self.durationSpin.get_value()
        print 'self.startSpin.get_value()', self.startSpin.get_value()



if __name__=='__main__':
    combo = Scale10PowerComboBox()
    combo.set_value(200)
    win = gtk.Dialog()
    win.vbox.pack_start(combo)
    win.vbox.show_all()
    win.run()
    print combo.get_value()




