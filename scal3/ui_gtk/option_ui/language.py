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

from typing import TYPE_CHECKING

from scal3.locale_man import langDict
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk
from scal3.ui_gtk.option_ui.base import OptionUI

if TYPE_CHECKING:
	from scal3.option import Option

__all__ = ["LangOptionUI"]


class LangOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(self, option: Option[str]) -> None:
		self.option = option
		# ---
		listStore = self.listStore = gtk.ListStore(str)
		combo = gtk.ComboBox()
		combo.set_model(listStore)
		# ---
		cell = gtk.CellRendererText()
		combo.pack_start(cell, expand=True)
		combo.add_attribute(cell, "text", 0)
		# ---
		self._widget = combo
		self.ls = listStore
		self.ls.append([_("System Setting")])
		for langObj in langDict.values():
			# assert isinstance(langObj, locale_man.LangData)
			desc = " - ".join(
				list(
					{
						_(langObj.name),
						langObj.name,
						langObj.nativeName,
					}
				)
			)
			self.ls.append([desc])

	def get(self) -> str:
		i = self._widget.get_active()
		if i == 0:
			return ""
		return list(langDict)[i - 1]

	def set(self, value: str) -> None:
		if not value:
			self._widget.set_active(0)
		else:
			try:
				i = list(langDict).index(value)
			except ValueError:
				log.info(f"language {value!r} in not in list!")
				self._widget.set_active(0)
			else:
				self._widget.set_active(i + 1)

	# def updateVar(self):
	# 	lang =
