#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.

from __future__ import annotations

from typing import TYPE_CHECKING

from gi.repository import GLib as glib

from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.mywidgets import MyColorButton
from scal3.ui_gtk.mywidgets.floatingMsg import FloatingMsg, NoFillFloatingMsgWindow
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.event_lib.notifiers import FloatingMsgNotifier


__all__ = ["WidgetClass", "notify"]


class WidgetClass(gtk.Box):
	def __init__(self, notifier: FloatingMsgNotifier) -> None:
		self.notifier = notifier
		# --
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		# [_] Fill Screen Width   Speed [__]   BG Color [__]  Text Color [__]
		# --
		self.fillWidthCb = gtk.CheckButton(label=_("Fill Width"))
		pack(self, self.fillWidthCb)
		pack(self, gtk.Label(), 1, 1)
		# --
		self.speedSpin = IntSpinButton(1, 999)
		pack(self, gtk.Label(label=_("Speed")))
		pack(self, self.speedSpin)
		pack(self, gtk.Label(), 1, 1)
		# --
		self.bgColorButton = MyColorButton()
		pack(self, gtk.Label(label=_("BG Color")))
		pack(self, self.bgColorButton)
		pack(self, gtk.Label(), 1, 1)
		# --
		self.textColorButton = MyColorButton()
		pack(self, gtk.Label(label=_("Text Color")))
		pack(self, self.textColorButton)
		pack(self, gtk.Label(), 1, 1)

	def updateWidget(self) -> None:
		self.fillWidthCb.set_active(self.notifier.fillWidth)
		self.speedSpin.set_value(self.notifier.speed)
		self.bgColorButton.set_rgba(self.notifier.bgColor)
		self.textColorButton.set_rgba(self.notifier.textColor)

	def updateVars(self) -> None:
		self.notifier.fillWidth = self.fillWidthCb.get_active()
		self.notifier.speed = self.speedSpin.get_value()
		self.notifier.bgColor = self.bgColorButton.get_rgba()
		self.notifier.textColor = self.textColorButton.get_rgba()


def notify(notifier: FloatingMsgNotifier, finishFunc: Callable[[], None]) -> None:
	glib.idle_add(_notify, notifier, finishFunc)


def _notify(
	notifier: FloatingMsgNotifier,
	finishFunc: Callable[[], None],
) -> None:  # FIXME
	cls = FloatingMsg if notifier.fillWidth else NoFillFloatingMsgWindow
	text = notifier.event.getText()
	msg = cls(
		text,
		speed=notifier.speed,
		bgColor=notifier.bgColor,
		textColor=notifier.textColor,
		finishFunc=finishFunc,
	)
	msg.show()
