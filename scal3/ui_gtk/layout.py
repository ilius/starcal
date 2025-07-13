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
from scal3.ui_gtk.cal_obj_base import CustomizableCalObj

log = logger.get()

from typing import TYPE_CHECKING

from scal3.ui_gtk import gdk, getOrientation, gtk, pack
from scal3.ui_gtk.customize import (
	newSubPageButton,
)
from scal3.ui_gtk.stack import StackPage, StackPageButton
from scal3.ui_gtk.utils import imageFromIconName, setImageClassButton

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.option import ListOption, Option


__all__ = ["WinLayoutBox", "WinLayoutObj"]


class WinLayoutBase(CustomizableCalObj):
	hasOptions = False
	itemListCustomizable = False

	def __init__(
		self,
		name: str,
		desc: str,
		vertical: bool,
		expand: bool,
		enableParam: Option[bool] | None = None,
	) -> None:
		super().__init__()
		self.objName = name
		self.desc = desc
		self.vertical: bool = vertical
		self.expand: bool = expand
		self.enableParam = enableParam
		# ----
		self.optionsButtonBox: gtk.Box | None = None
		self.optionsButton: StackPageButton | None = None
		self.optionsButtonEnable = True
		self.subPages: list[StackPage] | None = None
		# ----
		CustomizableCalObj.__init__(self)
		self.initVars()

	def getOptionsButtonBox(self) -> gtk.Box:
		raise NotImplementedError

	def getWidget(self) -> gtk.Widget:
		raise NotImplementedError


class MoveButton(gtk.Button):
	def __init__(
		self,
		iconName: str,
		styleClass: str,
		size: gtk.IconSize,
		action: str,
	) -> None:
		gtk.Button.__init__(self)
		self.add(
			imageFromIconName(
				iconName,
				size,
			),
		)
		self.get_style_context().add_class("image-button")
		self.set_can_focus(False)
		if styleClass:
			self.get_style_context().add_class(styleClass)
		self.action = action


class WinLayoutObj(WinLayoutBase):
	isWrapper = True

	def __init__(
		self,
		name: str,
		desc: str,
		vertical: bool,
		expand: bool,
		enableParam: Option[bool] | None = None,
		movable: bool = False,
		buttonBorder: int = 5,
		labelAngle: int = 0,
		initializer: Callable[[], CustomizableCalObj] | None = None,
	) -> None:
		if initializer is None:
			raise ValueError("initializer= argument is missing")
		self.movable = movable
		self.buttonBorder = buttonBorder
		self.labelAngle = labelAngle
		self._item = item = initializer()
		item.enableParam = enableParam
		if enableParam:
			item.enable = enableParam.v
		self.w = item.w
		self.moveButton: MoveButton | None = None
		# ---
		WinLayoutBase.__init__(
			self,
			name=name,
			desc=desc,
			vertical=vertical,
			expand=expand,
			enableParam=enableParam,
		)
		self.appendItem(item)

	def getWidget(self) -> gtk.Widget:
		return self.w

	def getItem(self) -> CustomizableCalObj:
		return self._item

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey) -> bool:
		if self._item is None:
			return False
		return self._item.onKeyPress(arg, gevent)

	def showHide(self) -> None:
		WinLayoutBase.showHide(self)
		button = self.optionsButton
		if not button:
			return
		enable = self.optionsButtonEnable
		item = self._item
		itemEnable = item.enable
		if enable != itemEnable:
			label = self.desc
			if not itemEnable:
				label = "(" + label + ")"
			button.label.set_text(label)
			self.optionsButtonEnable = itemEnable

	def set_visible(self, visible: bool) -> None:
		# does not need to do anything, because self._item is already
		# a child, aka a memeber of self.items
		pass

	def getOptionsButtonBox(self) -> gtk.Box:
		# log.debug(f"WinLayoutObj: getOptionsButtonBox: name={self.objName}")
		if self.optionsButtonBox is not None:
			return self.optionsButtonBox
		item = self._item
		page = StackPage()
		page.pageWidget = gtk.Box(
			orientation=gtk.Orientation.VERTICAL,
			spacing=item.optionsPageSpacing,
		)
		page.pageName = item.objName
		page.pageTitle = item.desc
		pageLabel = self.desc
		if not item.enable:
			pageLabel = "(" + pageLabel + ")"
		page.pageLabel = pageLabel
		page.pageIcon = ""
		page.pageItem = item
		self.subPages = [page]
		# assert self.vertical is not None
		button = newSubPageButton(
			item,
			page,
			vertical=self.vertical,
			borderWidth=self.buttonBorder,
			spacing=5,
			labelAngle=self.labelAngle,
		)
		self.optionsButtonEnable = item.enable
		self.optionsButton = button
		vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		pack(vbox, button, expand=True, fill=True)
		self.optionsButtonBox = vbox
		return vbox

	def getSubPages(self) -> list[StackPage]:
		if self.subPages is not None:
			return self.subPages
		self.getOptionsButtonBox()
		assert self.subPages is not None
		return self.subPages


class WinLayoutBox(WinLayoutBase):
	def __init__(
		self,
		name: str,
		desc: str,
		vertical: bool,
		expand: bool,
		enableParam: Option[bool] | None = None,
		itemsMovable: bool = False,
		itemsParam: ListOption[str] | None = None,
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
		# self.items: list[WinLayoutObj]
		self.itemsMovable = itemsMovable
		self.itemsParam = itemsParam
		self.buttonSpacing = buttonSpacing
		self.arrowSize = arrowSize
		self.w: gtk.Box = gtk.Box(orientation=getOrientation(vertical))
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
		self.createWidget()
		self.widgetIsSet = True

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey) -> bool:
		return any(item.enable and item.onKeyPress(arg, gevent) for item in self.items)

	def getWidget(self) -> gtk.Widget:
		return self.w

	def showHide(self) -> None:
		box = self.w
		assert box is not None
		if self.enable:
			box.show()
		else:
			box.hide()

	def createWidget(self) -> None:
		box = self.w
		for child in box.get_children():
			box.remove(child)

		for item in self.items:
			if item.loaded:
				pack(box, item.w, item.expand, item.expand)
				item.showHide()

	def onConfigChange(self) -> None:
		super().onConfigChange()
		if self.itemsParam:
			self.itemsParam.v = [item.objName for item in self.items if item.enable]
		self.createWidget()

	def setItemsOrder(self, option: ListOption[str]) -> None:
		itemByName = {item.objName: item for item in self.items}
		self.items = [itemByName[name] for name in option.v]
		for name in option.default:
			if name not in option.v:
				self.items.append(itemByName[name])
		# for item in self.items:
		# 	self.connectItem(item)

	def getOptionsButtonBox(self) -> gtk.Box:
		# log.debug(f"WinLayoutBox: getOptionsButtonBox: name={self.objName}")
		if self.optionsButtonBox is not None:
			return self.optionsButtonBox

		optionsButtonBox = gtk.Box(
			orientation=getOrientation(self.vertical),
			spacing=self.buttonSpacing,
		)

		if self.itemsMovable:
			if not self.vertical:
				raise ValueError("horizontal movable buttons are not supported")
			listBox = gtk.ListBox(
				# spacing=self.buttonSpacing, # FIXME: does not seem to have it
			)
			for index, item in enumerate(self.items):
				assert isinstance(item, WinLayoutObj), f"{item=}"
				childBox = item.getOptionsButtonBox()
				hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=0)
				action = "down" if index == 0 else "up"
				moveButton = MoveButton(
					iconName=f"pan-{action}-symbolic",
					styleClass=action,
					size=self.arrowSize,
					action=action,
				)
				pack(hbox, childBox, 1, 1)
				pack(hbox, moveButton, 0, 0)
				listBox.insert(hbox, -1)
				# ---
				moveButton.connect("clicked", self.onItemMoveClick, listBox, item)
				item.moveButton = moveButton
				pack(optionsButtonBox, listBox, True, True)
		else:
			for item in self.items:
				assert isinstance(item, WinLayoutBase), f"{item=}"
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
		_b: gtk.Button,
		listBox: gtk.ListBox,
		item: WinLayoutBox | WinLayoutObj,
	) -> None:
		index = self.items.index(item)
		if index == 0:
			newIndex = index + 1
		else:
			newIndex = index - 1
		self.moveItem(index, newIndex)
		# ---
		hbox = listBox.get_row_at_index(index)
		assert hbox is not None
		listBox.remove(hbox)
		listBox.insert(hbox, newIndex)
		for tmpIndex, tmpItem in enumerate(self.items):
			assert isinstance(tmpItem, WinLayoutObj), f"{tmpItem=}"
			action = "down" if tmpIndex == 0 else "up"
			assert tmpItem.moveButton is not None
			if tmpItem.moveButton.action != action:
				setImageClassButton(
					tmpItem.moveButton,
					f"pan-{action}-symbolic",
					action,
					self.arrowSize,
				)
				tmpItem.moveButton.action = action
		self.onConfigChange()

	def getSubPages(self) -> list[StackPage]:
		if self.subPages is not None:
			return self.subPages
		subPages: list[StackPage] = []
		for item in self.items:
			assert isinstance(item, WinLayoutBase), f"{item=}"
			for page in item.getSubPages():
				if not page.pageName:
					raise ValueError(f"pageName empty, pagePath={page.pagePath}")
				page.pageParent = self.objName
				page.pagePath = self.objName + "." + page.pageName
				subPages.append(page)
		self.subPages = subPages
		return subPages
