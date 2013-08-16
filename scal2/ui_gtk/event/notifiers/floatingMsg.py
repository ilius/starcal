# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2013 Saeed Rasooli <saeed.gnu@gmail.com>
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

from scal2.locale_man import tr as _
from scal2.ui_gtk.mywidgets.floatingMsg import *

class NotifierWidget(gtk.HBox):
    def __init__(self, notifier):
        self.notifier = notifier
        ##
        gtk.HBox.__init__(self)
        ## [_] Fill Screen Width       Speed [__]      BG Color [__]     Text Color [__]
        ##
        self.fillWidthCb = gtk.CheckButton(_('Fill Width'))
        self.pack_start(self.fillWidthCb, 0, 0)
        self.pack_start(gtk.Label(''), 1, 1)
        ##
        self.speedSpin = IntSpinButton(1, 999)
        self.pack_start(gtk.Label(_('Speed')), 0, 0)
        self.pack_start(self.speedSpin, 0, 0)
        self.pack_start(gtk.Label(''), 1, 1)
        ##
        self.bgColorButton = MyColorButton()
        self.pack_start(gtk.Label(_('BG Color')), 0, 0)
        self.pack_start(self.bgColorButton, 0, 0)
        self.pack_start(gtk.Label(''), 1, 1)
        ##
        self.textColorButton = MyColorButton()
        self.pack_start(gtk.Label(_('Text Color')), 0, 0)
        self.pack_start(self.textColorButton, 0, 0)
        self.pack_start(gtk.Label(''), 1, 1)
    def updateWidget(self):
        self.fillWidthCb.set_active(self.notifier.fillWidth)
        self.speedSpin.set_value(self.notifier.speed)
        self.bgColorButton.set_color(self.notifier.bgColor)
        self.textColorButton.set_color(self.notifier.textColor)
    def updateVars(self):
        self.notifier.fillWidth = self.fillWidthCb.get_active()
        self.notifier.speed = self.speedSpin.get_value()
        self.notifier.bgColor = self.bgColorButton.get_color()
        self.notifier.textColor = self.textColorButton.get_color()

def notify(notifier, finishFunc):## FIXME
    cls = FloatingMsg if notifier.fillWidth else NoFillFloatingMsgWindow
    text = notifier.event.getText()
    msg = cls(
        text,
        speed = notifier.speed,
        bgColor = notifier.bgColor,
        textColor = notifier.textColor,
        finishFunc = finishFunc
    )
    msg.show()

