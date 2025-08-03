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

from scal3.font import Font
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.font_utils import gfontDecode
from scal3.ui_gtk.mywidgets import MyFontButton
from scal3.ui_gtk.option_ui.base import OptionUI

if typing.TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.option import Option

__all__ = ["FontFamilyOptionUI", "FontOptionUI"]


class FontFamilyOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		option: Option[str] | Option[str | None],
		hasAuto: bool = False,
		label: str = "",
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		self.option = option
		self.hasAuto = hasAuto
		self._onChangeFunc = onChangeFunc
		# ---
		self.fontButton = MyFontButton()
		self.fontButton.set_show_size(False)
		if gtk.MINOR_VERSION >= 24:
			self.fontButton.set_level(gtk.FontChooserLevel.FAMILY)
		# set_level: FAMILY, STYLE, SIZE
		self.fontButton.connect("font-set", self.onChange)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
		if label:
			pack(hbox, gtk.Label(label=label))
		if hasAuto:
			self.fontRadio = gtk.RadioButton()
			self.autoRadio = gtk.RadioButton(
				label=_("Auto"),
				group=self.fontRadio,
			)
			pack(hbox, self.fontRadio)
			pack(hbox, self.fontButton)
			pack(hbox, self.autoRadio, padding=5)
			self.fontButton.connect("clicked", self.onFontButtonClick)
			self.fontRadio.connect("clicked", self.onChange)
			self.autoRadio.connect("clicked", self.onChange)
		else:
			pack(hbox, self.fontButton)
		hbox.show_all()
		self._widget = hbox

	def onFontButtonClick(self, _w: gtk.Widget) -> None:
		if not self.hasAuto:
			return
		self.fontRadio.set_active(True)

	def get(self) -> str | None:
		if self.hasAuto and self.autoRadio.get_active():
			return None
		font = gfontDecode(self.fontButton.get_font_name())
		return font.family

	def set(self, value: str | None) -> None:
		if value is None:
			if self.hasAuto:
				self.autoRadio.set_active(True)
			return
		# now value is not None
		if self.hasAuto:
			self.fontRadio.set_active(True)
		self.fontButton.setFont(Font(family=value, size=15))

	def onChange(self, _w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()

	def setPreviewText(self, text: str) -> None:
		self.fontButton.set_property("preview-text", text)


# TODO: FontStyleOptionUI
# get() should return a dict, with keys and values being compatible
# with svg and gtk+css, these keys and values
# 	"font-family"
# 	"font-size"
# 	"font-weight"
# 	"font-style": normal | oblique | italic
# 	"font-variant": normal | small-caps
# 	"font-stretch": ultra-condensed | extra-condensed | condensed |
# 		semi-condensed | normal | semi-expanded | expanded |
# 		extra-expanded | ultra-expanded

# Constructor can accept argument `optionDict: dict[str, Option]`
# with keys being a subset these 6 style keys, and values
# being the attribute/variable names for reading (in updateWidget)
# and storing (in updateVar) the style values
# or maybe we should leave that to the user of class, and just accept
# a `option: Option` argument like other classes


class FontOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		option: Option[Font | None],
		dragAndDrop: bool = True,
		previewText: str = "",
	) -> None:
		self.option = option
		w = MyFontButton(dragAndDrop=dragAndDrop)
		self._widget = w
		if previewText:
			self.setPreviewText(previewText)

	def get(self) -> Font:
		return self._widget.getFont()

	def set(self, value: Font | None) -> None:
		if value is None:
			return
		self._widget.setFont(value)

	def setPreviewText(self, text: str) -> None:
		self._widget.set_preview_text(text)
		# self._widget.set_property("preview-text", text)
