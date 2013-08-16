# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2012 Saeed Rasooli <saeed.gnu@gmail.com>
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

from scal2 import core
from scal2.locale_man import tr as _

from scal2.ui_gtk.event import common
from scal2.ui_gtk.utils import set_tooltip, DateTypeCombo

import gtk

from scal2.ui_gtk.mywidgets import MyColorButton, TextFrame
from scal2.ui_gtk.mywidgets.multi_spin_button import IntSpinButton


class BaseGroupWidget(gtk.VBox):
    def __init__(self, group):
        gtk.VBox.__init__(self)
        self.group = group
        ########
        self.sizeGroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        #####
        hbox = gtk.HBox()
        label = gtk.Label(_('Title'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        self.sizeGroup.add_widget(label)
        self.titleEntry = gtk.Entry()
        hbox.pack_start(self.titleEntry, 1, 1)
        self.pack_start(hbox, 0, 0)
        #####
        hbox = gtk.HBox()
        label = gtk.Label(_('Color'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        self.sizeGroup.add_widget(label)
        self.colorButton = MyColorButton()
        self.colorButton.set_use_alpha(True) ## FIXME
        hbox.pack_start(self.colorButton, 0, 0)
        self.pack_start(hbox, 0, 0)
        #####
        hbox = gtk.HBox()
        label = gtk.Label(_('Default Icon'))## FIXME
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        self.sizeGroup.add_widget(label)
        self.iconSelect = common.IconSelectButton()
        hbox.pack_start(self.iconSelect, 0, 0)
        self.pack_start(hbox, 0, 0)
        #####
        hbox = gtk.HBox()
        label = gtk.Label(_('Default Calendar Type'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        self.sizeGroup.add_widget(label)
        combo = DateTypeCombo()
        hbox.pack_start(combo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.modeCombo = combo
        self.pack_start(hbox, 0, 0)
        #####
        hbox = gtk.HBox()
        label = gtk.Label(_('Show in Calendar'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        self.sizeGroup.add_widget(label)
        self.showInDCalCheck = gtk.CheckButton(_('Day'))
        self.showInWCalCheck = gtk.CheckButton(_('Week'))
        self.showInMCalCheck = gtk.CheckButton(_('Month'))
        hbox.pack_start(self.showInDCalCheck, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        hbox.pack_start(self.showInWCalCheck, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        hbox.pack_start(self.showInMCalCheck, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.pack_start(hbox, 0, 0)
        #####
        hbox = gtk.HBox()
        label = gtk.Label(_('Show in'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        self.sizeGroup.add_widget(label)
        self.showInTimeLineCheck = gtk.CheckButton(_('Time Line'))
        self.showInTrayCheck = gtk.CheckButton(_('Tray'))
        hbox.pack_start(self.showInTimeLineCheck, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        hbox.pack_start(self.showInTrayCheck, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.pack_start(hbox, 0, 0)
        #####
        hbox = gtk.HBox()
        label = gtk.Label(_('Event Cache Size'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        self.sizeGroup.add_widget(label)
        self.cacheSizeSpin = IntSpinButton(0, 9999)
        hbox.pack_start(self.cacheSizeSpin, 0, 0)
        self.pack_start(hbox, 0, 0)
        #####
        hbox = gtk.HBox()
        label = gtk.Label(_('Event Text Seperator'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        self.sizeGroup.add_widget(label)
        self.sepInput = TextFrame()
        hbox.pack_start(self.sepInput, 1, 1)
        self.pack_start(hbox, 0, 0)
        set_tooltip(hbox, _('Using to seperate Summary and Description when displaying event'))
        #####
        #hbox = gtk.HBox()
        #label = gtk.Label(_('Show Full Event Description'))
        #label.set_alignment(0, 0.5)
        #hbox.pack_start(label, 0, 0)
        #self.sizeGroup.add_widget(label)
        #self.showFullEventDescCheck = gtk.CheckButton('')
        #hbox.pack_start(self.showFullEventDescCheck, 1, 1)
        #self.pack_start(hbox, 0, 0)
        ###
        self.modeCombo.connect('changed', self.modeComboChanged)## right place? before updateWidget? FIXME
    def updateWidget(self):
        self.titleEntry.set_text(self.group.title)
        self.colorButton.set_color(self.group.color)
        self.iconSelect.set_filename(self.group.icon)
        self.modeCombo.set_active(self.group.mode)
        self.showInDCalCheck.set_active(self.group.showInDCal)
        self.showInWCalCheck.set_active(self.group.showInWCal)
        self.showInMCalCheck.set_active(self.group.showInMCal)
        self.showInTimeLineCheck.set_active(self.group.showInTimeLine)
        self.showInTrayCheck.set_active(self.group.showInTray)
        self.cacheSizeSpin.set_value(self.group.eventCacheSize)
        self.sepInput.set_text(self.group.eventTextSep)
        #self.showFullEventDescCheck.set_active(self.group.showFullEventDesc)
    def updateVars(self):
        self.group.title = self.titleEntry.get_text()
        self.group.color = self.colorButton.get_color()
        self.group.icon = self.iconSelect.get_filename()
        self.group.mode = self.modeCombo.get_active()
        self.group.showInDCal = self.showInDCalCheck.get_active()
        self.group.showInWCal = self.showInWCalCheck.get_active()
        self.group.showInMCal = self.showInMCalCheck.get_active()
        self.group.showInTimeLine = self.showInTimeLineCheck.get_active()
        self.group.showInTray = self.showInTrayCheck.get_active()
        self.group.eventCacheSize = int(self.cacheSizeSpin.get_value())
        self.group.eventTextSep = self.sepInput.get_text()
        #self.group.showFullEventDesc = self.showFullEventDescCheck.get_active()
    def modeComboChanged(self, obj=None):
        pass



