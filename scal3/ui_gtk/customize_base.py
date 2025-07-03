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

from scal3.ui_gtk import gdk, gtk
from scal3.ui_gtk import gtk_ud as ud

if TYPE_CHECKING:
	from scal3.property import Property
	from scal3.ui_gtk.stack import StackPage

__all__ = ["CustomizableCalObj"]


class CustomizableCalObj(ud.BaseCalObj):
	customizable = True
	hasOptions = True
	itemListCustomizable = True
	vertical: bool | None = None
	# vertical: only set (non-None) when `hasOptions and itemListCustomizable`
	# vertical: True if items are on top of each other
	isWrapper = False
	enableParam: Property[bool] | None = None
	optionsPageSpacing = 0
	itemListSeparatePage = False
	itemsPageTitle = ""
	itemsPageButtonBorder = 5
	expand = False
	params = ()
	myKeys: set[str] = set()
	objName: str = ""

	def initVars(self) -> None:
		if self.hasOptions and self.itemListCustomizable and self.vertical is None:
			log.error(f"Add vertical to {self.__class__}")
		ud.BaseCalObj.initVars(self)
		# self.itemWidgets = {}  # for lazy construction of widgets
		self.optionsWidget: gtk.Widget | None = None
		try:
			self.connect("key-press-event", self.onKeyPress)
		except TypeError as e:
			if "unknown signal name" not in str(e):
				log.exception("")

	def getItemsData(self) -> list[tuple[str, bool]]:
		return [(item.objName, item.enable) for item in self.items]

	def updateVars(self) -> None:
		for item in self.items:
			if item.customizable:
				item.updateVars()

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey) -> bool:
		kname = gdk.keyval_name(gevent.keyval)
		if not kname:
			return False
		kname = kname.lower()
		for item in self.items:
			if item.enable and kname in item.myKeys and item.onKeyPress(arg, gevent):
				return True
		return False

	def getOptionsWidget(self) -> gtk.Widget | None:  # noqa: PLR6301
		return None

	def getSubPages(self) -> list[StackPage]:  # noqa: PLR6301
		return []
