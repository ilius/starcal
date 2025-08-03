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

from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.option_ui.base import OptionUI

if typing.TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.option import Option

__all__ = ["JustificationOptionUI"]


class JustificationOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		option: Option[str],
		label: str = "",
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		from scal3.ui_gtk.mywidgets.justification_combo import JustificationComboBox

		# ---
		self.option = option
		self._onChangeFunc = onChangeFunc
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=10)
		if label:
			pack(hbox, gtk.Label(label=label))
		combo = JustificationComboBox()
		self._combo = combo
		pack(hbox, combo)
		combo.connect("changed", self.onComboChange)
		self._widget = hbox
		# ---
		self.updateWidget()

	def get(self) -> str:
		"""Returns one of "left", "right", "center", "fill"."""
		return self._combo.getValue()

	def set(self, value: str) -> None:
		"""Value must be one of "left", "right", "center", "fill"."""
		self._combo.setValue(value)

	def onComboChange(self, _w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()
