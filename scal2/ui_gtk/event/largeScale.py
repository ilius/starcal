#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_man

from scal2 import ui
from scal2.ui_gtk.event import common

import gtk
from gtk import gdk

class Scale10PowerComboBox(gtk.ComboBox):
    def __init__(self):
        self.ls = gtk.ListStore(int, str)
        gtk.ComboBox.__init__(self, self.ls)
        ###
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 1)
        ###
        self.ls.append((1, _('Years')))
        self.ls.append((100, _('Centuries')))
        self.ls.append((1000, _('Thousand Years')))
        self.ls.append((1000**2, _('Million Years')))
        self.ls.append((1000**3, _('Billion (10^9) Years')))
        ###
        self.set_active(0)
    get_value = lambda self: self.ls[self.get_active()][0]
    def set_value(self, value):
        for i, row in enumerate(self.ls):
            if row[0] == value:
                self.set_active(i)
                return
        self.ls.append((value, _('%s Years')%_(value)))
        self.set_active(len(self.ls)-1)

class EventWidget(common.EventWidget):
    def __init__(self, event, maxStart=999999, maxDur=999):## FIXME
        common.EventWidget.__init__(self, event)
        ######
        sizeGroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        ######
        hbox = gtk.HBox()
        label = gtk.Label(_('Scale'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        self.scaleCombo = Scale10PowerComboBox()
        hbox.pack_start(self.scaleCombo, 0, 0)
        self.pack_start(hbox, 0, 0)
        ####
        hbox = gtk.HBox()
        label = gtk.Label(_('Start'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        spin = gtk.SpinButton()
        spin.set_increments(1, 10)
        spin.set_range(-maxStart, maxStart)
        spin.set_direction(gtk.TEXT_DIR_LTR)
        hbox.pack_start(spin, 0, 0)
        self.startSpin = spin
        self.pack_start(hbox, 0, 0)
        ####
        hbox = gtk.HBox()
        label = gtk.Label(_('Duration'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        spin = gtk.SpinButton()
        spin.set_increments(1, 10)
        spin.set_range(0, maxDur)
        spin.set_direction(gtk.TEXT_DIR_LTR)
        hbox.pack_start(spin, 0, 0)
        self.durationSpin = spin
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



if __name__=='__main__':
    combo = Scale10PowerComboBox()
    combo.set_value(200)
    win = gtk.Dialog()
    win.vbox.pack_start(combo)
    win.vbox.show_all()
    win.run()
    print combo.get_value()




