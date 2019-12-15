#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from scal3 import logger
log = logger.get()

from typing import Optional, Any, Union, List, Callable

from scal3 import core

from scal3 import locale_man
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import imageClassButton
from scal3.ui_gtk.customize import CustomizableCalObj, newSubPageButton
from scal3.ui_gtk.stack import StackPage


class WinLayoutBase(CustomizableCalObj):
	hasOptions = False
	itemListCustomizable = False

	def __init__(
		self,
		name: str = "",
		desc: str = "",
		enableParam: str = "",
		vertical: Optional[bool] = None,
		expand: Optional[bool] = None,
	):
		if not name:
			raise ValueError("name= argument is missing")
		if vertical is None:
			raise ValueError("vertical= argument is missing")
		if expand is None:
			raise ValueError("expand= argument is missing")
		self._name = name
		self.desc = desc
		self.enableParam = enableParam
		self.vertical = vertical
		self.expand = expand
		####
		self.optionsButtonBox = None  # type: gtk.Widget
		self.subPages = None
		####
		CustomizableCalObj.__init__(self)
		self.initVars()


class WinLayoutObj(WinLayoutBase):
	isWrapper = True
	def __init__(
		self,
		name: str = "",
		desc: str = "",
		enableParam: str = "",
		vertical: Optional[bool] = None,
		expand: Optional[bool] = None,
		movable: bool = False,
		buttonBorder: int = 5,
		labelAngle: int = 0,
		initializer: Optional[Callable[[], CustomizableCalObj]] = None,
	):
		if initializer is None:
			raise ValueError("initializer= argument is missing")
		###
		WinLayoutBase.__init__(
			self,
			name=name,
			desc=desc,
			enableParam=enableParam,
			vertical=vertical,
			expand=expand,
		)
		###
		self.movable = movable
		self.buttonBorder = buttonBorder
		self.labelAngle = labelAngle
		self.initializer = initializer
		self._item = None  # type: Optional[CustomizableCalObj]

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey):
		if self._item is None:
			return
		self._item.onKeyPress(arg, gevent)

	def getWidget(self):
		if self._item is not None:
			return self._item
		item = self.initializer()
		if not isinstance(item, gtk.Widget):
			raise ValueError(f"initializer returned non-widget: {type(item)}")
		item.enableParam = self.enableParam
		if item.enableParam:
			item.enable = getattr(ui, item.enableParam)
		self.appendItem(item)
		self._item = item
		return item

	def showHide(self):
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

	def getOptionsButtonBox(self):
		#log.debug(f"WinLayoutObj: getOptionsButtonBox: name={self._name}")
		if self.optionsButtonBox is not None:
			return self.optionsButtonBox
		item = self.getWidget()
		page = StackPage()
		page.pageWidget = VBox(spacing=item.optionsPageSpacing)
		page.pageName = item._name
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
		enableParam: str = "",
		vertical: Optional[bool] = None,
		expand: Optional[bool] = None,
		itemsMovable: bool = False,
		itemsParam: str = "",
		buttonSpacing: int = 5,
		arrowSize: gtk.IconSize = gtk.IconSize.LARGE_TOOLBAR,
		items: Optional[List[Union["WinLayoutBox", "WinLayoutObj"]]] = None,
	):
		if items is None:
			raise ValueError("items= argument is missing")
		if itemsMovable and not vertical:
			raise ValueError("horizontal movable buttons are not supported")
		if itemsMovable and not itemsParam:
			raise ValueError("itemsMovable=True but no itemsParam is given")
		###
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
		###
		self.itemsMovable = itemsMovable
		self.itemsParam = itemsParam
		self.buttonSpacing = buttonSpacing
		self.arrowSize = arrowSize
		###
		self._box = None  # type: gtk.Box

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey):
		kname = gdk.keyval_name(gevent.keyval).lower()
		for item in self.items:
			if item.enable:
				if item.onKeyPress(arg, gevent):
					break

	def showHide(self):
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

	def onConfigChange(self, *args, **kwargs):
		WinLayoutBase.onConfigChange(self, *args, **kwargs)
		if self._box is None:
			return
		box = self._box
		for child in box.get_children():
			box.remove(child)
		itemNames = []
		for item in self.items:
			itemNames.append(item._name)
			if item.loaded:
				pack(box, item.getWidget(), item.expand, item.expand)
				item.showHide()
		setattr(ui, self.itemsParam, itemNames)

	def setItemsOrder(self, itemNames):
		itemByName = {item._name: item for item in self.items}
		self.items = [itemByName[name] for name in itemNames]

	def getOptionsButtonBox(self):
		#log.debug(f"WinLayoutBox: getOptionsButtonBox: name={self._name}")
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
				upButton = imageClassButton(
					"pan-up-symbolic",
					"up",
					self.arrowSize,
				)
				pack(hbox, childBox, 1, 1)
				pack(hbox, upButton, 0, 0)
				optionsButtonBox.insert(hbox, -1)
				###
				upButton.connect("clicked", self.onItemMoveUpClick, item)
				item.upButton = upButton
				if index == 0:
					upButton.set_sensitive(False)
		else:
			optionsButtonBox = gtk.Box(
				orientation=getOrientation(self.vertical),
				spacing=self.buttonSpacing,
			)
			for item in self.items:
				pack(optionsButtonBox, item.getOptionsButtonBox(), item.expand, item.expand)
		self.optionsButtonBox = optionsButtonBox
		return optionsButtonBox

	def onItemMoveUpClick(self, button: gtk.Button, item: Union["WinLayoutBox", "WinLayoutObj"]):
		index = self.items.index(item)
		if index < 1:
			log.error(f"onItemMoveUpClick: bad index={index}, item={item}")
		###
		self.moveItem(index, index - 1)
		###
		listBox = self.optionsButtonBox
		hbox = listBox.get_row_at_index(index)
		listBox.remove(hbox)
		listBox.insert(hbox, index - 1)
		for tmpIndex, tmpItem in enumerate(self.items):
			tmpItem.upButton.set_sensitive(tmpIndex > 0)
		self.onConfigChange()

	def getSubPages(self):
		if self.subPages is not None:
			return self.subPages
		subPages = []
		for item in self.items:
			for page in item.getSubPages():
				page.pageParent = self._name
				page.pageName = self._name + "." + page.pageName
				subPages.append(page)
		self.subPages = subPages
		return subPages



