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

__all__ = ["TextOptionUI"]


class TextOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		option: Option[str],
		label: str = "",
		live: bool = False,
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		from scal3.ui_gtk.mywidgets import TextFrame

		self.option = option
		self._onChangeFunc = onChangeFunc
		# ---
		kwargs = {}
		if live:
			kwargs["onTextChange"] = self.onTextChange
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")
		self.textInput = TextFrame(**kwargs)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		if label:
			pack(hbox, gtk.Label(label=label))
		pack(hbox, self.textInput, 1, 1)
		hbox.show_all()
		self._widget = hbox
		# ---
		if live:
			self.updateWidget()

	def get(self) -> str:
		return self.textInput.get_text()

	def set(self, text: str) -> None:
		self.textInput.set_text(text)

	def onTextChange(self, _w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()
