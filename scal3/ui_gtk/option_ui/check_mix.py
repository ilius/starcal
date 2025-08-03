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

from scal3.ui_gtk import getOrientation, gtk, pack
from scal3.ui_gtk.option_ui.base import OptionUI

if typing.TYPE_CHECKING:
	from collections.abc import Callable

	from .check import CheckOptionUI
	from .color import ColorOptionUI
	from .font import FontOptionUI

__all__ = ["CheckColorOptionUI", "CheckFontOptionUI"]


# combination of CheckOptionUI and ColorOptionUI in a HBox,
# with auto-update / auto-apply, for use in Customize window
class CheckColorOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		checkItem: CheckOptionUI,
		colorItem: ColorOptionUI,
		checkSizeGroup: gtk.SizeGroup | None = None,
		live: bool = False,
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		self._checkItem = checkItem
		self._colorItem = colorItem
		self.live = live
		self._onChangeFunc = onChangeFunc

		checkb = self._checkItem.getWidget()
		colorb = self._colorItem.getWidget()

		if checkSizeGroup:
			checkSizeGroup.add_widget(checkb)

		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=3)
		pack(hbox, checkb)
		pack(hbox, colorb)
		self._widget = hbox

		if live:
			# updateWidget needs to be called before following connect() calls
			self.updateWidget()
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")
		checkb.connect("clicked", self.onChange)
		colorb.connect("color-set", self.onChange)

	def updateVar(self) -> None:
		self._checkItem.updateVar()
		self._colorItem.updateVar()

	def updateWidget(self) -> None:
		# FIXME: this func is triggering onChange func, can we avoid that?
		self._checkItem.updateWidget()
		self._colorItem.updateWidget()
		self._colorItem.getWidget().set_sensitive(self._checkItem.get())

	def onChange(self, _w: gtk.Widget) -> None:
		self._colorItem.getWidget().set_sensitive(self._checkItem.get())
		if self.live:
			self.updateVar()
			if self._onChangeFunc:
				self._onChangeFunc()


# combination of CheckOptionUI and FontOptionUI in a HBox
class CheckFontOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		checkItem: CheckOptionUI,
		fontItem: FontOptionUI,
		checkSizeGroup: gtk.SizeGroup | None = None,
		vertical: bool = False,
		spacing: int = 3,
		live: bool = False,
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		self._checkItem = checkItem
		self._fontItem = fontItem
		self.live = live
		self._onChangeFunc = onChangeFunc

		checkb = self._checkItem.getWidget()
		fontb = self._fontItem.getWidget()

		if checkSizeGroup:
			checkSizeGroup.add_widget(checkb)

		box = gtk.Box(orientation=getOrientation(vertical), spacing=spacing)
		pack(box, checkb)
		pack(box, fontb)
		self._widget = box

		if live:
			# updateWidget needs to be called before following connect() calls
			self.updateWidget()
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")
		checkb.connect("clicked", self.onChange)
		fontb.connect("font-set", self.onChange)

	def updateVar(self) -> None:
		self._checkItem.updateVar()
		self._fontItem.updateVar()

	def updateWidget(self) -> None:
		# FIXME: this func is triggering onChange func, can we avoid that?
		self._checkItem.updateWidget()
		self._fontItem.updateWidget()
		self._fontItem.getWidget().set_sensitive(self._checkItem.get())

	def onChange(self, _w: gtk.Widget) -> None:
		self._fontItem.getWidget().set_sensitive(self._checkItem.get())
		if self.live:
			self.updateVar()
			if self._onChangeFunc:
				self._onChangeFunc()
