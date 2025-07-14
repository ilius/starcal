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

# The low-level module for gtk ui dependent stuff (classes/functions/settings)
# ud = ui dependent
# upper the "ui" module

from __future__ import annotations

from scal3 import logger

log = logger.get()

from typing import TYPE_CHECKING, Any

from scal3.ui_gtk import gdk
from scal3.ui_gtk.signals import (
	SignalHandlerBase,
	SignalHandlerType,
	registerSignals,
)

if TYPE_CHECKING:
	from collections.abc import Iterable

	from scal3.option import Option
	from scal3.ui_gtk import gtk
	from scal3.ui_gtk.pytypes import CalObjType, CustomizableCalObjType, StackPageType

__all__ = [
	"CalObjBase",
	"CalObjWidget",
	"CommonSignalHandler",
	"CustomizableCalObj",
	"commonSignals",
]

commonSignals: list[tuple[str, list[Any]]] = [
	("config-change", []),
	("date-change", []),
	("goto-page", [str]),
]


@registerSignals
class CommonSignalHandler(SignalHandlerBase):
	signals = commonSignals


class CalObjBase:
	objName: str = ""
	desc: str = ""
	loaded: bool = True
	customizable: bool = False
	itemHaveOptions: bool = True
	Sig: type[SignalHandlerType] = CommonSignalHandler
	myKeys: set[str] = set()
	expand: bool = False

	s: SignalHandlerType  # FIXME: instance
	enable: bool  # FIXME: instance

	def itemIter(self) -> Iterable[CalObjType]:
		raise NotImplementedError

	def broadcastConfigChange(
		self,
		sig: SignalHandlerType | None = None,
		emit: bool = True,
	) -> None:
		self.onConfigChange()
		if emit:
			self.s.emit("config-change")
		if sig is None:
			sig = self.s
		for item in self.itemIter():
			if item.enable and item.s is not sig:
				item.broadcastConfigChange(sig=sig, emit=False)

	def broadcastDateChange(
		self,
		sig: SignalHandlerType | None = None,
		emit: bool = True,
	) -> None:
		self.onDateChange()
		if emit:
			self.s.emit("date-change")
		if sig is None:
			sig = self.s
		for item in self.itemIter():
			if item.enable and item.s is not sig:
				item.broadcastDateChange(sig=sig, emit=False)

	def onConfigChange(self) -> None:
		log.debug(f"onConfigChange: name={self.objName}")

	def onDateChange(self) -> None:
		log.debug(f"onDateChange: name={self.objName}")

	def updateVars(self) -> None:
		pass

	def show(self) -> None:
		raise NotImplementedError

	def hide(self) -> None:
		raise NotImplementedError

	def showHide(self) -> None:
		if self.enable:
			self.show()
		else:
			self.hide()
		for item in self.itemIter():
			item.showHide()

	def connectItem(self, item: CalObjType) -> None:
		# log.info(f"connectItem: {item.objName}")
		item.s.connect("config-change", self.broadcastConfigChange)
		item.s.connect("date-change", self.broadcastDateChange)

	def onKeyPress(  # noqa: PLR6301
		self,
		arg: gtk.Widget,  # noqa: ARG002
		gevent: gdk.EventKey,  # noqa: ARG002
	) -> bool:
		return False

	def moveItem(self, i: int, j: int) -> None:
		raise NotImplementedError


class CalObjWidget(CalObjBase):
	w: gtk.Widget

	def initVars(self) -> None:
		self.s = self.Sig()
		self.items: list[CustomizableCalObjType] = []
		self.enable = True

	def itemCount(self) -> int:
		return len(self.items)

	def itemIter(self) -> Iterable[CustomizableCalObjType]:
		return iter(self.items)

	def itemGet(self, index: int) -> CustomizableCalObjType:
		return self.items[index]

	def moveItem(self, i: int, j: int) -> None:
		self.items.insert(j, self.items.pop(i))

	def __getitem__(self, key: str) -> CustomizableCalObjType | None:
		for item in self.items:
			if item.objName == key:
				return item
		return None

	def appendItem(self, item: CustomizableCalObjType) -> None:
		self.items.append(item)
		self.connectItem(item)

	def replaceItem(self, itemIndex: int, item: CustomizableCalObjType) -> None:
		self.items[itemIndex] = item
		self.connectItem(item)

	def show(self) -> None:
		self.w.show()

	def hide(self) -> None:
		self.w.hide()


class CustomizableCalObj(CalObjWidget):
	customizable = True
	hasOptions = True
	itemListCustomizable = True
	vertical = True
	# vertical: True if items are on top of each other
	isWrapper = False
	enableParam: Option[bool] | None = None
	optionsPageSpacing = 0
	itemListSeparatePage = False
	itemsPageTitle = ""
	itemsPageButtonBorder = 5
	params: list[str] = []
	# enableOptionUI = None

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

	def getLoadedObj(self) -> CustomizableCalObjType:
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

	def getSubPages(self) -> list[StackPageType]:  # noqa: PLR6301
		return []

	def insertItemWidget(self, _i: int) -> None:
		raise NotImplementedError
