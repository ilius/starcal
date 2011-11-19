# -*- coding: utf-8 -*-

from os.path import join, dirname

from scal2 import core
from scal2.locale_man import tr as _
from scal2.core import pixDir

from scal2 import event_man
from scal2 import ui

from scal2.ui_gtk.event import common

import gtk
from gtk import gdk

from scal2.ui_gtk.mywidgets import MyColorButton

class GroupWidget(gtk.VBox):
    def __init__(self, group):
        gtk.VBox.__init__(self)
        self.group = group
        ####
        sizeGroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        ##
        hbox = gtk.HBox()
        label = gtk.Label(_('Title'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        sizeGroup.add_widget(label)
        self.titleEntry = gtk.Entry()
        hbox.pack_start(self.titleEntry, 1, 1)
        self.pack_start(hbox, 0, 0)
        ##
        hbox = gtk.HBox()
        label = gtk.Label(_('Color'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        sizeGroup.add_widget(label)
        self.colorButton = MyColorButton()
        self.colorButton.set_use_alpha(True) ## FIXME
        hbox.pack_start(self.colorButton, 0, 0)
        self.pack_start(hbox, 0, 0)
        ##
        hbox = gtk.HBox()
        label = gtk.Label(_('Default Icon'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        sizeGroup.add_widget(label)
        self.defaultIconSelect = common.IconSelectButton()
        hbox.pack_start(self.defaultIconSelect, 0, 0)
        self.pack_start(hbox, 0, 0)
        ##
        hbox = gtk.HBox()
        label = gtk.Label(_('Default Calendar Type'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        sizeGroup.add_widget(label)
        combo = gtk.combo_box_new_text()
        for m in core.modules:
            combo.append_text(_(m.desc))
        #if i>0:## FIXME
        #    combo.append_text(_('Julian Day'))
        hbox.pack_start(combo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.defaultModeCombo = combo
        self.pack_start(hbox, 0, 0)
        ##
        hbox = gtk.HBox()
        label = gtk.Label(_('Event Cache Size'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        sizeGroup.add_widget(label)
        spin = gtk.SpinButton()
        spin.set_increments(1, 10)
        spin.set_range(0, 9999)
        spin.set_digits(0)
        #spin.set_width_chars(3)
        spin.set_direction(gtk.TEXT_DIR_LTR)
        hbox.pack_start(spin, 0, 0)
        self.cacheSizeSpin = spin
        self.pack_start(hbox, 0, 0)
        ####
        self.updateWidget()
    def updateWidget(self):
        self.titleEntry.set_text(self.group.title)
        self.colorButton.set_color(self.group.color)
        self.defaultIconSelect.set_filename(self.group.defaultIcon)
        self.defaultModeCombo.set_active(self.group.defaultMode)
        self.cacheSizeSpin.set_value(self.group.eventCacheSize)
    def updateVars(self):
        self.group.title = self.titleEntry.get_text()
        self.group.color = self.colorButton.get_color()
        self.group.defaultIcon = self.defaultIconSelect.get_filename()
        self.group.defaultMode = self.defaultModeCombo.get_active()
        self.group.eventCacheSize = int(self.cacheSizeSpin.get_value())





