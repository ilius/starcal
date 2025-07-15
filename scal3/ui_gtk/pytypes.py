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

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
	from collections.abc import Iterable

	from scal3.option import Option
	from scal3.ui_gtk import gdk, gtk
	from scal3.ui_gtk.signals import SignalHandlerType


__all__ = ["CalObjType", "CustomizableCalObjType", "StackPageType"]


class CalObjType(Protocol):
	enable: bool
	loaded: bool
	objName: str
	desc: str
	customizable: bool
	myKeys: set[str]
	expand: bool
	s: SignalHandlerType

	def show(self) -> None: ...
	def hide(self) -> None: ...
	def showHide(self) -> None: ...
	def onConfigChange(self) -> None: ...
	def onDateChange(self) -> None: ...
	def broadcastConfigChange(
		self,
		sig: SignalHandlerType | None = None,
		emit: bool = True,
	) -> None: ...
	def broadcastDateChange(
		self,
		sig: SignalHandlerType | None = None,
		emit: bool = True,
	) -> None: ...
	def updateVars(self) -> None: ...
	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey) -> bool: ...


class CustomizableCalObjType(CalObjType, Protocol):
	w: gtk.Widget
	hasOptions: bool
	itemListCustomizable: bool
	vertical: bool
	enableParam: Option[bool] | None
	optionsPageSpacing: int
	itemListSeparatePage: bool
	itemsPageTitle: str
	itemsPageButtonBorder: int
	params: list[str]
	# enableOptionUI = None
	itemHaveOptions: bool

	def itemCount(self) -> int: ...
	def itemIter(self) -> Iterable[CustomizableCalObjType]: ...
	def itemGet(self, index: int) -> CustomizableCalObjType: ...
	def moveItem(self, i: int, j: int) -> None: ...
	def onEnableCheckClick(self) -> None: ...
	def getOptionsWidget(self) -> gtk.Widget | None: ...
	def getSubPages(self) -> list[StackPageType]: ...
	def getLoadedObj(self) -> CustomizableCalObjType: ...
	def replaceItem(self, itemIndex: int, item: CustomizableCalObjType) -> None: ...
	def insertItemWidget(self, _i: int) -> None: ...


class StackPageType(Protocol):
	pageWidget: gtk.Box | None
	pageParent: str
	pageName: str
	pagePath: str
	pageTitle: str
	pageLabel: str
	pageIcon: str
	pageExpand: bool
	pageItem: CustomizableCalObjType | None
	iconSize: int
