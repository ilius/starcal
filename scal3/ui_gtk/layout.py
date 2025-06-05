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
from scal3.ui_gtk.stack import StackPage, StackPageButton
from scal3.ui_gtk.utils import imageFromIconName, setImageClassButton

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.property import Property


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
		enableParam: Property | None = None,
	) -> None:
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


class CustomizableCalWidget(gtk.Widget, CustomizableCalObj):  # type: ignore
	pass


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
		enableParam: Property | None = None,
		movable: bool = False,
		buttonBorder: int = 5,
		labelAngle: int = 0,
		initializer: Callable[[], CustomizableCalWidget] | None = None,
	) -> None:
		if initializer is None:
			raise ValueError("initializer= argument is missing")
		# ---
		WinLayoutBase.__init__(
			self,
			name=name,
			desc=desc,
			vertical=vertical,
			expand=expand,
			enableParam=enableParam,
		)
		# ---
		self.movable = movable
		self.buttonBorder = buttonBorder
		self.labelAngle = labelAngle
		self.initializer = initializer
		self._item: CustomizableCalWidget | None = None
		self.moveButton: MoveButton | None = None

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey) -> bool:
		if self._item is None:
			return False
		return self._item.onKeyPress(arg, gevent)

	def getWidget(self) -> CustomizableCalWidget:
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
		button = self.optionsButton
		if not button:
			return
		enable = self.optionsButtonEnable
		item = self.getWidget()
		# FIXME: item.enable
		itemEnable = item.enable  # type: ignore[attr-defined]
		# buttonLabel = button.label
		if enable != itemEnable:
			label = self.desc
			if not itemEnable:
				label = "(" + label + ")"
			# button.set_la
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
		vbox = VBox()
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
		enableParam: Property | None = None,
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
		self.items: list[WinLayoutObj]
		self.itemsMovable = itemsMovable
		self.itemsParam = itemsParam
		self.buttonSpacing = buttonSpacing
		self.arrowSize = arrowSize
		# ---
		self._box: gtk.Box | None = None

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey) -> bool:
		return any(item.enable and item.onKeyPress(arg, gevent) for item in self.items)

	def showHide(self) -> None:
		assert self._box is not None
		if self.enable:
			self._box.show()
		else:
			self._box.hide()

	def getWidget(self) -> gtk.Widget:
		if self._box is not None:
			return self._box
		# assert self.vertical is not None
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

	def setItemsOrder(self, itemNames: list[str]) -> None:
		itemByName = {item.objName: item for item in self.items}
		self.items = [itemByName[name] for name in itemNames]

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
				# item is instance of WinLayoutObj
				childBox = item.getOptionsButtonBox()
				hbox = HBox(spacing=0)
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
