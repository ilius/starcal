#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_lib

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
        self.startSpin.connect('changed', self.startSpinChanged)
        hbox.pack_start(self.startSpin, 0, 0)
        self.pack_start(hbox, 0, 0)
        ####
        hbox = gtk.HBox()
        self.endRelCombo = gtk.combo_box_new_text()
        for item in ('Duration', 'End'):
            self.endRelCombo.append_text(_(item))
        self.endRelCombo.connect('changed', self.endRelComboChanged)
        sizeGroup.add_widget(self.endRelCombo)
        hbox.pack_start(self.endRelCombo, 0, 0)
        self.endSpin = IntSpinButton(-maxDur, maxDur)
        hbox.pack_start(self.endSpin, 0, 0)
        self.pack_start(hbox, 0, 0)
        ####
        self.endRelComboChanged()
    def endRelComboChanged(self, combo=None):
        rel = self.endRelCombo.get_active()
        start = self.startSpin.get_value()
        end = self.endSpin.get_value()
        if rel==0:## reletive(duration)
            self.endSpin.set_range(1, maxStart)
            self.endSpin.set_value(max(1, end-start))
        elif rel==1:## absolute(end)
            self.endSpin.set_range(start+1, maxStart)
            self.endSpin.set_value(max(start+1, start+end))
    def startSpinChanged(self, spin=None):
        if self.endRelCombo.get_active() == 1:## absolute(end)
            self.endSpin.set_range(self.startSpin.get_value()+1, maxStart)
    def updateWidget(self):
        common.EventWidget.updateWidget(self)
        self.scaleCombo.set_value(self.event.scale)
        self.startSpin.set_value(self.event.start)
        self.endRelCombo.set_active(0 if self.event.endRel else 1)
        self.endSpin.set_value(self.event.end)
    def updateVars(self):## FIXME
        common.EventWidget.updateVars(self)
        self.event.scale = self.scaleCombo.get_value()
        self.event.start = self.startSpin.get_value()
        self.event.endRel = (self.endRelCombo.get_active()==0)
        self.event.end = self.endSpin.get_value()



if __name__=='__main__':
    combo = Scale10PowerComboBox()
    combo.set_value(200)
    win = gtk.Dialog()
    win.vbox.pack_start(combo)
    win.vbox.show_all()
    win.run()
    print(combo.get_value())




