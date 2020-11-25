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

from os.path import join, isfile

from typing import Optional, List, Tuple

from scal3.path import confDir
from scal3.json_utils import *
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import registerSignals
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.utils import imageFromFile


@registerSignals
class DummyCalObj(ud.CalObjType):
	loaded = False
	itemListCustomizable = False
	hasOptions = False
	isWrapper = False
	enableParam = ""
	itemsPageEnable = False
	signals = ud.BaseCalObj.signals

	def __init__(
		self,
		name: str,
		desc: str,
		pkg: str,
		customizable: bool,
	) -> None:
		ud.CalObjType.__init__(self)
		self.enable = False
		self._name = name
		self.desc = desc
		self.moduleName = ".".join([pkg, name])
		self.customizable = customizable
		self.optionsWidget = None
		self.items = []

	def getLoadedObj(self) -> ud.BaseCalObj:
		try:
			module = __import__(
				self.moduleName,
				fromlist=["CalObj"],
			)
			CalObj = module.CalObj
		except Exception:
			log.exception("")
			return
		obj = CalObj(ui.mainWin)
		obj.enable = self.enable
		return obj

	def updateVars(self) -> None:
		pass

	def getOptionsWidget(self) -> Optional[gtk.Widget]:
		return None

	def getSubPages(self) -> "List[StackPage]":
		return []

	def showHide(self) -> None:
		pass


class CustomizableCalObj(ud.BaseCalObj):
	customizable = True
	itemListCustomizable = True
	hasOptions = True
	isWrapper = False
	enableParam = ""
	optionsPageSpacing = 0
	itemsPageEnable = False
	itemsPageTitle = ""
	itemsPageButtonBorder = 5
	expand = False
	params = ()
	myKeys = ()

	def initVars(self) -> None:
		ud.BaseCalObj.initVars(self)
		self.itemWidgets = {} ## for lazy construction of widgets
		self.optionsWidget = None
		try:
			self.connect("key-press-event", self.onKeyPress)## FIXME
		except TypeError:
			# TypeError: <...>: unknown signal name
			pass

	def getItemsData(self) -> List[Tuple[str, bool]]:
		return [
			(item._name, item.enable)
			for item in self.items
		]

	def updateVars(self) -> None:
		for item in self.items:
			if item.customizable:
				item.updateVars()

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey):
		kname = gdk.keyval_name(gevent.keyval).lower()
		for item in self.items:
			if item.enable and kname in item.myKeys:
				if item.onKeyPress(arg, gevent):
					break

	def getOptionsWidget(self) -> gtk.Widget:
		return None

	def getSubPages(self) -> "List[StackPage]":
		return []


class CustomizableCalBox(CustomizableCalObj):
	"""for GtkBox (HBox and VBox)"""

	def appendItem(self, item):
		CustomizableCalObj.appendItem(self, item)
		if item.loaded:
			pack(self, item, item.expand, item.expand)
			item.showHide()

	def repackAll(self):
		for item in self.items:
			if item.loaded:
				self.remove(item)
		for item in self.items:
			if item.loaded:
				pack(self, item, item.expand, item.expand)

	# Disabled the old implementation (with reorder_child) because it was
	# very buggy with Gtk3. Removing all (active) items from gtk.Box and
	# re-packing them all apears to be fast enough, so doing that instead

	def moveItem(self, i, j):
		CustomizableCalObj.moveItem(self, i, j)
		self.repackAll()

	def insertItemWidget(self, i):
		self.repackAll()


def newSubPageButton(
	item: CustomizableCalObj,
	page: "StackPage",
	vertical: bool = False,
	borderWidth: int = 10,
	spacing: int = 10,
	labelAngle: int = 0,
) -> gtk.Button:
	hbox = gtk.Box(
		orientation=getOrientation(vertical),
		spacing=spacing,
	)
	hbox.set_border_width(borderWidth)
	label = gtk.Label(label=page.pageLabel)
	label.set_use_underline(True)
	label.set_angle(labelAngle)
	pack(hbox, gtk.Label(), 1, 1)
	if page.pageIcon and ui.buttonIconEnable:
		pack(hbox, imageFromFile(page.pageIcon, size=ui.stackIconSize))
	pack(hbox, label, 0, 0)
	pack(hbox, gtk.Label(), 1, 1)
	button = gtk.Button()
	button.add(hbox)
	button.connect("clicked", lambda b: item.emit("goto-page", page.pageName))
	button.show_all()
	button.label = label
	return button
