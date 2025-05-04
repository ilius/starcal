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

from scal3.ui_gtk import HBox, VBox, gdk, getOrientation, gtk, pack
from scal3.ui_gtk.customize import CustomizableCalObj, newSubPageButton
from scal3.ui_gtk.stack import StackPage
from scal3.ui_gtk.utils import imageClassButton, setImageClassButton

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.property import Property


__all__ = ["WinLayoutBox", "WinLayoutObj"]


class WinLayoutBase(CustomizableCalObj):
	hasOptions = False
	itemListCustomizable = False

	def __init__(
		self,
		name: str = "",
		desc: str = "",
		enableParam: Property | None = None,
		vertical: bool | None = None,
		expand: bool | None = None,
	) -> None:
		if not name:
			raise ValueError("name= argument is missing")
		if vertical is None:
			raise ValueError("vertical= argument is missing")
		if expand is None:
			raise ValueError("expand= argument is missing")
		self.objName = name
		self.desc = desc
		self.enableParam = enableParam
		self.vertical = vertical
		self.expand = expand
		# ----
		self.optionsButtonBox = None  # type: gtk.Widget
		self.subPages = None
		# ----
		CustomizableCalObj.__init__(self)
		self.initVars()


class WinLayoutObj(WinLayoutBase):
	isWrapper = True

	def __init__(
		self,
		name: str = "",
		desc: str = "",
		enableParam: Property | None = None,
		vertical: bool | None = None,
		expand: bool | None = None,
		movable: bool = False,
		buttonBorder: int = 5,
		labelAngle: int = 0,
		initializer: Callable[[], CustomizableCalObj] | None = None,
	) -> None:
		if initializer is None:
			raise ValueError("initializer= argument is missing")
		# ---
		WinLayoutBase.__init__(
			self,
			name=name,
			desc=desc,
			enableParam=enableParam,
			vertical=vertical,
			expand=expand,
		)
		# ---
		self.movable = movable
		self.buttonBorder = buttonBorder
		self.labelAngle = labelAngle
		self.initializer = initializer
		self._item: CustomizableCalObj | None = None

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey) -> None:
		if self._item is None:
			return
		self._item.onKeyPress(arg, gevent)

	def getWidget(self):
		if self._item is not None:
			return self._item
		item = self.initializer()
		if not isinstance(item, gtk.Widget):
			raise TypeError(f"initializer returned non-widget: {type(item)}")
		item.enableParam = self.enableParam
		if item.enableParam:
			item.enable = item.enableParam.v
		self.appendItem(item)
		self._item = item
		return item

	def showHide(self) -> None:
		WinLayoutBase.showHide(self)
		button = self.optionsButtonBox
		if not button:
			return
		item = self.getWidget()
		if button.enable != item.enable:
			label = self.desc
			if not item.enable:
				label = "(" + label + ")"
			button.label.set_text(label)
			button.enable = item.enable

	def set_visible(self, visible: bool) -> None:
		# does not need to do anything, because self._item is already
		# a child, aka a memeber of self.items
		pass

	def getOptionsButtonBox(self):
		# log.debug(f"WinLayoutObj: getOptionsButtonBox: name={self.objName}")
		if self.optionsButtonBox is not None:
			return self.optionsButtonBox
		item = self.getWidget()
		page = StackPage()
		page.pageWidget = VBox(spacing=item.optionsPageSpacing)
		page.pageName = item.objName
		page.pageTitle = item.desc
		pageLabel = self.desc
		if not item.enable:
			pageLabel = "(" + pageLabel + ")"
		page.pageLabel = pageLabel
		page.pageIcon = ""
		page.pageItem = item
		self.subPages = [page]
		optionsButtonBox = newSubPageButton(
			item,
			page,
			vertical=self.vertical,
			borderWidth=self.buttonBorder,
			spacing=5,
			labelAngle=self.labelAngle,
		)
		optionsButtonBox.enable = item.enable
		self.optionsButtonBox = optionsButtonBox
		return optionsButtonBox

	def getSubPages(self):
		if self.subPages is not None:
			return self.subPages
		self.getOptionsButtonBox()
		return self.subPages


class WinLayoutBox(WinLayoutBase):
	def __init__(
		self,
		name: str = "",
		desc: str = "",
		enableParam: Property | None = None,
		vertical: bool | None = None,
		expand: bool | None = None,
		itemsMovable: bool = False,
		itemsParam: Property | None = None,
		buttonSpacing: int = 5,
		arrowSize: gtk.IconSize = gtk.IconSize.LARGE_TOOLBAR,
		items: list[WinLayoutBox | WinLayoutObj] | None = None,
	) -> None:
		if items is None:
			raise ValueError("items= argument is missing")
		if itemsMovable and not vertical:
			raise ValueError("horizontal movable buttons are not supported")
		if itemsMovable and not itemsParam:
			raise ValueError("itemsMovable=True but no itemsParam is given")
		# ---
		WinLayoutBase.__init__(
			self,
			name=name,
			desc=desc,
			enableParam=enableParam,
			vertical=vertical,
			expand=expand,
		)
		for item in items:
			self.appendItem(item)
		# ---
		self.itemsMovable = itemsMovable
		self.itemsParam = itemsParam
		self.buttonSpacing = buttonSpacing
		self.arrowSize = arrowSize
		# ---
		self._box = None  # type: gtk.Box

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey) -> None:
		for item in self.items:
			if item.enable and item.onKeyPress(arg, gevent):
				break

	def showHide(self) -> None:
		if self.enable:
			self._box.show()
		else:
			self._box.hide()

	def getWidget(self):
		if self._box is not None:
			return self._box
		box = gtk.Box(orientation=getOrientation(self.vertical))

		for item in self.items:
			if item.loaded:
				pack(box, item.getWidget(), item.expand, item.expand)
				item.showHide()

		self._box = box
		return box

	def onConfigChange(self, *args, **kwargs) -> None:
		WinLayoutBase.onConfigChange(self, *args, **kwargs)
		if self._box is None:
			return
		box = self._box
		for child in box.get_children():
			box.remove(child)
		itemNames = []
		for item in self.items:
			itemNames.append(item.objName)
			if item.loaded:
				pack(box, item.getWidget(), item.expand, item.expand)
				item.showHide()
		if self.itemsParam:
			self.itemsParam.v = itemNames

	def setItemsOrder(self, itemNames) -> None:
		itemByName = {item.objName: item for item in self.items}
		self.items = [itemByName[name] for name in itemNames]

	def getOptionsButtonBox(self):
		# log.debug(f"WinLayoutBox: getOptionsButtonBox: name={self.objName}")
		if self.optionsButtonBox is not None:
			return self.optionsButtonBox

		if self.itemsMovable:
			if not self.vertical:
				raise ValueError("horizontal movable buttons are not supported")
			optionsButtonBox = gtk.ListBox(
				# spacing=self.buttonSpacing, # FIXME: does not seem to have it
			)
			for index, item in enumerate(self.items):
				childBox = item.getOptionsButtonBox()
				hbox = HBox(spacing=0)
				action = "down" if index == 0 else "up"
				upButton = imageClassButton(
					f"pan-{action}-symbolic",
					action,
					self.arrowSize,
				)
				upButton.action = action
				pack(hbox, childBox, 1, 1)
				pack(hbox, upButton, 0, 0)
				optionsButtonBox.insert(hbox, -1)
				# ---
				upButton.connect("clicked", self.onItemMoveClick, item)
				item.upButton = upButton
		else:
			optionsButtonBox = gtk.Box(
				orientation=getOrientation(self.vertical),
				spacing=self.buttonSpacing,
			)
			for item in self.items:
				pack(
					optionsButtonBox,
					item.getOptionsButtonBox(),
					item.expand,
					item.expand,
				)
		self.optionsButtonBox = optionsButtonBox
		return optionsButtonBox

	def onItemMoveClick(
		self,
		_button: gtk.Button,
		item: WinLayoutBox | WinLayoutObj,
	) -> None:
		index = self.items.index(item)
		if index == 0:
			newIndex = index + 1
		else:
			newIndex = index - 1
		self.moveItem(index, newIndex)
		# ---
		listBox = self.optionsButtonBox
		hbox = listBox.get_row_at_index(index)
		listBox.remove(hbox)
		listBox.insert(hbox, newIndex)
		for tmpIndex, tmpItem in enumerate(self.items):
			action = "down" if tmpIndex == 0 else "up"
			if tmpItem.upButton.action != action:
				setImageClassButton(
					tmpItem.upButton,
					f"pan-{action}-symbolic",
					action,
					self.arrowSize,
				)
				tmpItem.upButton.action = action
		self.onConfigChange()

	def getSubPages(self):
		if self.subPages is not None:
			return self.subPages
		subPages = []
		for item in self.items:
			for page in item.getSubPages():
				if not page.pageName:
					raise ValueError(f"pageName empty, pagePath={page.pagePath}")
				page.pageParent = self.objName
				page.pagePath = self.objName + "." + page.pageName
				subPages.append(page)
		self.subPages = subPages
		return subPages
