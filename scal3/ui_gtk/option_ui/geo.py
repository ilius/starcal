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

from scal3 import logger

log = logger.get()

import typing

from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
from scal3.ui_gtk.option_ui.base import OptionUI

if typing.TYPE_CHECKING:
	from scal3.option import Option

__all__ = ["WidthHeightOptionUI"]


class WidthHeightOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		option: Option[tuple[int, int]],
		maxim: int,
	) -> None:
		minim = 0
		self.option = option
		# ---
		self.widthItem = IntSpinButton(minim, maxim)
		self.heightItem = IntSpinButton(minim, maxim)
		# ---
		hbox = self._widget = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Width") + ":"))
		pack(hbox, self.widthItem)
		pack(hbox, gtk.Label(label="  "))
		pack(hbox, gtk.Label(label=_("Height") + ":"))
		pack(hbox, self.heightItem)

	def get(self) -> tuple[int, int]:
		return (
			int(self.widthItem.get_value()),
			int(self.heightItem.get_value()),
		)

	def set(self, value: tuple[int, int]) -> None:
		w, h = value
		self.widthItem.set_value(w)
		self.heightItem.set_value(h)
