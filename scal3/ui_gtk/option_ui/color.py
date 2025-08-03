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

if typing.TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.color_utils import ColorType
	from scal3.option import Option

__all__ = ["ColorOptionUI"]


class ColorOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		option: Option[ColorType] | Option[ColorType | None],
		useAlpha: bool = False,
		live: bool = False,
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		from scal3.ui_gtk.mywidgets import MyColorButton

		self.option = option
		colorb = MyColorButton()
		gtk.ColorChooser.set_use_alpha(colorb, useAlpha)
		self.useAlpha = useAlpha
		self._widget = colorb
		# ---
		if live:
			self._onChangeFunc = onChangeFunc
			# updateWidget needs to be called before following connect() calls
			self.updateWidget()
			colorb.connect("color-set", self.onColorSet)
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")

	def get(self) -> ColorType:
		return self._widget.getRGBA()

	def set(self, color: ColorType | None) -> None:
		if color is None:
			return
		self._widget.setRGBA(color)

	def onColorSet(self, _w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()


# class OptionalColorOptionUI(ColorOptionUI):
# 	def __init__(
# 		self,
# 		option: Option[ColorType | None],
# 		useAlpha: bool = False,
# 		live: bool = False,
# 		onChangeFunc: Callable | None = None,
# 	) -> None:
