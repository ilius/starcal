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
from scal3.ui_gtk.gtk_ud import CalObjWidget

if TYPE_CHECKING:
	from scal3.property import Property
	from scal3.ui_gtk.stack import StackPage

__all__ = ["CustomizableCalObj"]


class CustomizableCalObj(CalObjWidget):
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
	params = ()
	# enablePrefItem = None

	def initVars(self) -> None:
		if self.hasOptions and self.itemListCustomizable and self.vertical is None:
			log.error(f"Add vertical to {self.__class__}")
		super().initVars()
		# self.itemWidgets = {}  # for lazy construction of widgets
		self.optionsWidget: gtk.Widget | None = None
		try:
			self.w.connect("key-press-event", self.onKeyPress)
		except TypeError as e:
			if "unknown signal name" not in str(e):
				log.exception("")

	@property
	def enable2(self) -> bool:
		if self.enableParam is not None:
			return self.enableParam.v
		return self.enable

	def getLoadedObj(self) -> CustomizableCalObj:
		return self

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

	def onEnableCheckClick(self) -> None:
		assert self.enableParam is not None
		self.enable = self.enableParam.v
		self.onConfigChange()
		self.showHide()

	def getOptionsWidget(self) -> gtk.Widget | None:  # noqa: PLR6301
		return None

	def getSubPages(self) -> list[StackPage]:  # noqa: PLR6301
		return []

	def insertItemWidget(self, _i: int) -> None:
		raise NotImplementedError
