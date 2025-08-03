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
from scal3.ui_gtk.option_ui.base import OptionUI

if typing.TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.option import Option

__all__ = ["DirectionOptionUI"]


class DirectionOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		option: Option[str],
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		from scal3.ui_gtk.mywidgets.direction_combo import DirectionComboBox

		# ---
		self.option = option
		self._onChangeFunc = onChangeFunc
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Direction")))
		combo = DirectionComboBox()
		self._combo = combo
		pack(hbox, combo)
		combo.connect("changed", self.onComboChange)
		self._widget = hbox
		# ---
		self.updateWidget()

	def get(self) -> str:
		"""Returns one of "ltr", "rtl", "auto"."""
		return self._combo.getValue()

	def set(self, value: str) -> None:
		"""Value must be one of "ltr", "rtl", "auto"."""
		self._combo.setValue(value)

	def onComboChange(self, _w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()
