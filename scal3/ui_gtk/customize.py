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
from scal3.ui import conf

log = logger.get()

from typing import TYPE_CHECKING

from scal3 import ui
from scal3.ui_gtk import gdk, getOrientation, gtk, pack
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.decorators import registerSignals
from scal3.ui_gtk.utils import imageFromFile

if TYPE_CHECKING:
	from scal3.ui_gtk.stack import StackPage

__all__ = [
	"CustomizableCalBox",
	"CustomizableCalObj",
	"DummyCalObj",
	"newSubPageButton",
]


@registerSignals
class DummyCalObj(ud.CalObjType):
	loaded = False
	itemListCustomizable = False
	hasOptions = False
	isWrapper = False
	enableParam = ""
	itemListSeparatePage = False
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
		self.objName = name
		self.desc = desc
		self.moduleName = f"{pkg}.{name}"
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

	def getOptionsWidget(self) -> gtk.Widget | None:  # noqa: PLR6301
		return None

	def getSubPages(self) -> list[StackPage]:  # noqa: PLR6301
		return []

	def showHide(self) -> None:  # noqa: PLR6301
		pass


class CustomizableCalObj(ud.BaseCalObj):
	customizable = True
	hasOptions = True
	itemListCustomizable = True
	vertical: bool | None = None
	# vertical: only set (non-None) when `hasOptions and itemListCustomizable`
	# vertical: True if items are on top of each other
	isWrapper = False
	enableParam = ""
	optionsPageSpacing = 0
	itemListSeparatePage = False
	itemsPageTitle = ""
	itemsPageButtonBorder = 5
	expand = False
	params = ()
	myKeys = ()

	def initVars(self) -> None:
		if self.hasOptions and self.itemListCustomizable and self.vertical is None:
			log.error(f"Add vertical to {self.__class__}")
		ud.BaseCalObj.initVars(self)
		self.itemWidgets = {}  # for lazy construction of widgets
		self.optionsWidget = None
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

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey) -> None:
		kname = gdk.keyval_name(gevent.keyval).lower()
		for item in self.items:
			if item.enable and kname in item.myKeys and item.onKeyPress(arg, gevent):
				break

	def getOptionsWidget(self) -> gtk.Widget:  # noqa: PLR6301
		return None

	def getSubPages(self) -> list[StackPage]:  # noqa: PLR6301
		return []


class CustomizableCalBox(CustomizableCalObj):

	"""for GtkBox (HBox and VBox)."""

	def appendItem(self, item: CustomizableCalObj) -> None:
		CustomizableCalObj.appendItem(self, item)
		if item.loaded:
			pack(self, item, item.expand, item.expand)
			item.showHide()

	def repackAll(self) -> None:
		for item in self.items:
			if item.loaded:
				self.remove(item)
		for item in self.items:
			if item.loaded:
				pack(self, item, item.expand, item.expand)

	# Disabled the old implementation (with reorder_child) because it was
	# very buggy with Gtk3. Removing all (active) items from gtk.Box and
	# re-packing them all apears to be fast enough, so doing that instead

	def moveItem(self, i: int, j: int) -> None:
		CustomizableCalObj.moveItem(self, i, j)
		self.repackAll()

	def insertItemWidget(self, _i: int) -> None:
		self.repackAll()


def newSubPageButton(
	item: CustomizableCalObj,
	page: StackPage,
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
	label.set_use_markup(True)
	label.set_use_underline(True)
	label.set_angle(labelAngle)
	pack(hbox, gtk.Label(), 1, 1)
	if page.pageIcon and conf.buttonIconEnable.v:
		pack(hbox, imageFromFile(page.pageIcon, size=conf.stackIconSize.v))
	pack(hbox, label, 0, 0)
	pack(hbox, gtk.Label(), 1, 1)
	button = gtk.Button()
	button.add(hbox)

	def onClick(_button: gtk.Button, page: StackPage) -> None:
		if not page.pagePath:
			raise ValueError(f"pagePath empty, {page = }")
		item.emit("goto-page", page.pagePath)

	button.connect("clicked", onClick, page)
	button.show_all()
	button.label = label
	return button
