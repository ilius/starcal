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
from os.path import isabs, join

from gi.repository import GdkPixbuf

from scal3.path import pixDir
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.option_ui.base import OptionUI
from scal3.ui_gtk.utils import (
	newAlignLabel,
)

if typing.TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.option import Option

__all__ = ["ComboEntryTextOptionUI", "ComboTextOptionUI"]


class ComboTextOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		option: Option[str],
		items: list[str],
		label: str = "",
		labelSizeGroup: gtk.SizeGroup | None = None,
		live: bool = False,
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		self.option = option
		combo = gtk.ComboBoxText()
		self._combo = combo
		self._items = items
		if items:
			for s in items:
				combo.append_text(s)

		self._widget: gtk.Widget
		if label:
			hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=3)
			pack(hbox, newAlignLabel(sgroup=labelSizeGroup, label=label))
			pack(hbox, combo)
			self._widget = hbox
		else:
			self._widget = combo

		if live:
			self._onChangeFunc = onChangeFunc
			# updateWidget needs to be called before following connect() calls
			self.updateWidget()
			combo.connect("changed", self.onChange)
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")

	def onChange(self, _w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()

	def get(self) -> str:
		return self._combo.get_active_text() or ""

	def set(self, value: str) -> None:
		self._combo.set_active(self._items.index(value))


class ComboEntryTextOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		option: Option[str],
		items: list[str] | None = None,
	) -> None:
		"""Items is a list of strings."""
		self.option = option
		w = gtk.ComboBoxText.new_with_entry()
		self._widget = w
		if items:
			for s in items:
				w.append_text(s)

	def get(self) -> str:
		child = self._widget.get_child()
		assert isinstance(child, gtk.Entry), f"{child=}"
		return child.get_text()

	def set(self, value: str) -> None:
		child = self._widget.get_child()
		assert isinstance(child, gtk.Entry), f"{child=}"
		child.set_text(value)

	def addDescriptionColumn(self, descByValue: dict[str, str]) -> None:
		w = self._widget
		cell = gtk.CellRendererText()
		w.pack_start(cell, expand=True)
		w.add_attribute(cell, "text", 1)
		ls = w.get_model()
		for row in ls:
			row[1] = descByValue.get(row[0], "")


class ComboImageTextOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		option: Option[int],
		items: list[tuple[str, str]] | None = None,
	) -> None:
		"""Items is a list of (imagePath, text) tuples."""
		self.option = option
		# ---
		ls = gtk.ListStore(GdkPixbuf.Pixbuf, str)
		combo = gtk.ComboBox()
		combo.set_model(ls)
		cell: gtk.CellRenderer
		# ---
		cell = gtk.CellRendererPixbuf()
		combo.pack_start(cell, expand=False)
		combo.add_attribute(cell, "pixbuf", 0)
		# ---
		cell = gtk.CellRendererText()
		combo.pack_start(cell, expand=True)
		combo.add_attribute(cell, "text", 1)
		# ---
		self._widget = combo
		self.ls = ls
		if items:
			for imPath, label in items:
				self.append(imPath, label)

	def get(self) -> int:
		return self._widget.get_active()

	def set(self, value: int) -> None:
		self._widget.set_active(value)

	def append(self, imPath: str, label: str) -> None:
		if imPath:
			if not isabs(imPath):
				imPath = join(pixDir, imPath)
			pix = GdkPixbuf.Pixbuf.new_from_file(imPath)
		else:
			pix = None
		self.ls.append([pix, label])
