# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
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

from scal3 import core
from scal3.locale_man import tr as _

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.floatingMsg import *

class WidgetClass(gtk.HBox):
	def __init__(self, notifier):
		self.notifier = notifier
		##
		gtk.HBox.__init__(self)
		## [_] Fill Screen Width       Speed [__]      BG Color [__]     Text Color [__]
		##
		self.fillWidthCb = gtk.CheckButton(_('Fill Width'))
		pack(self, self.fillWidthCb)
		pack(self, gtk.Label(''), 1, 1)
		##
		self.speedSpin = IntSpinButton(1, 999)
		pack(self, gtk.Label(_('Speed')))
		pack(self, self.speedSpin)
		pack(self, gtk.Label(''), 1, 1)
		##
		self.bgColorButton = MyColorButton()
		pack(self, gtk.Label(_('BG Color')))
		pack(self, self.bgColorButton)
		pack(self, gtk.Label(''), 1, 1)
		##
		self.textColorButton = MyColorButton()
		pack(self, gtk.Label(_('Text Color')))
		pack(self, self.textColorButton)
		pack(self, gtk.Label(''), 1, 1)
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

