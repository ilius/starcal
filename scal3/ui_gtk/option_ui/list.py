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
from typing import Any

from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.option_ui.base import OptionUI

if typing.TYPE_CHECKING:
	from scal3.option import ListOption


# class RadioListOptionUI(OptionUI):
# 	def getWidget(self) -> gtk.Widget:
# 		return self._widget

# 	def __init__(
# 		self,
# 		vertical: bool,
# 		option: Option[int | None],
# 		texts: list[str],
# 		label: str | None = None,
# 	) -> None:
# 		self.num = len(texts)
# 		self.option = option
# 		if vertical:
# 			box = gtk.Box(orientation=gtk.Orientation.VERTICAL)
# 		else:
# 			box = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
# 		self._widget = box
# 		self.radios = [gtk.RadioButton(label=_(s)) for s in texts]
# 		first = self.radios[0]
# 		if label is not None:
# 			pack(box, gtk.Label(label=label))
# 			pack(box, gtk.Label(), 1, 1)
# 		pack(box, first)
# 		for r in self.radios[1:]:
# 			pack(box, gtk.Label(), 1, 1)
# 			pack(box, r)
# 			r.join_group(first)
# 		pack(box, gtk.Label(), 1, 1)  # FIXME

# 	def get(self) -> int | None:
# 		for i in range(self.num):
# 			if self.radios[i].get_active():
# 				return i
# 		return None

# 	def set(self, index: int) -> None:
# 		self.radios[index].set_active(True)


# class RadioHListOptionUI(RadioListOptionUI):
# 	def __init__(
# 		self,
# 		option: Option[int | None],
# 		texts: list[str],
# 		label: str | None = None,
# 	) -> None:
# 		RadioListOptionUI.__init__(
# 			self,
# 			vertical=False,
# 			option=option,
# 			texts=texts,
# 			label=label,
# 		)


# class RadioVListOptionUI(RadioListOptionUI):
# 	def __init__(
# 		self,
# 		option: Option[int | None],
# 		texts: list[str],
# 		label: str | None = None,
# 	) -> None:
# 		RadioListOptionUI.__init__(
# 			self,
# 			vertical=True,
# 			option=option,
# 			texts=texts,
# 			label=label,
# 		)


class ListOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		vertical: bool,
		option: ListOption[Any],
		items: list[OptionUI] | None = None,
	) -> None:
		self.option = option
		if vertical:
			box = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		else:
			box = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		if items is None:
			items = []
		for item in items:
			pack(box, item.getWidget())
		self.num = len(items)
		self.items = items
		self._widget = box

	def get(self) -> list[Any]:
		return [item.get() for item in self.items]

	def set(self, valueL: list[Any]) -> None:
		for i in range(self.num):
			self.items[i].set(valueL[i])

	def append(self, item: OptionUI) -> None:
		pack(self._widget, item.getWidget())
		self.items.append(item)


class HListOptionUI(ListOptionUI):
	def __init__(
		self,
		option: ListOption[Any],
		items: list[OptionUI] | None = None,
	) -> None:
		ListOptionUI.__init__(
			self,
			vertical=False,
			option=option,
			items=items,
		)


# class VListOptionUI(ListOptionUI):
# 	def __init__(
# 		self,
# 		option: ListOption[Any],
# 		items: list[OptionUI] | None = None,
# 	) -> None:
# 		ListOptionUI.__init__(
# 			self,
# 			vertical=True,
# 			option=option,
# 			items=items,
# 		)
