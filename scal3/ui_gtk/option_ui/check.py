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

from scal3.ui_gtk import gtk
from scal3.ui_gtk.option_ui.base import OptionUI
from scal3.ui_gtk.utils import (
	set_tooltip,
)

if typing.TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.option import Option

__all__ = ["CheckOptionUI"]


class CheckOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		option: Option[bool],
		label: str = "",
		tooltip: str = "",
		live: bool = False,
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		self.option = option
		checkb = gtk.CheckButton(label=label)
		if tooltip:
			set_tooltip(checkb, tooltip)
		self._widget = checkb
		self._checkButton = checkb

		if live:
			self._onChangeFunc = onChangeFunc
			# updateWidget needs to be called before following connect() calls
			self.updateWidget()
			checkb.connect("clicked", self.onClick)
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")

	def get(self) -> bool:
		return self._widget.get_active()

	def set(self, value: bool) -> None:
		self._widget.set_active(value)

	def onClick(self, _w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()

	def syncSensitive(self, widget: gtk.Widget, reverse: bool = False) -> None:
		self._sensitiveWidget = widget
		self._sensitiveReverse = reverse
		self._widget.connect("show", self.syncSensitiveUpdate)
		self._widget.connect("clicked", self.syncSensitiveUpdate)

	def syncSensitiveUpdate(self, _widget: gtk.Widget) -> None:
		active = self._checkButton.get_active()
		if self._sensitiveReverse:
			active = not active
		self._sensitiveWidget.set_sensitive(active)
