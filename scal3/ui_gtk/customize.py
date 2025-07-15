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
from scal3.ui_gtk.cal_obj_base import CustomizableCalObj
from scal3.ui_gtk.stack import StackPageButton

log = logger.get()

from typing import TYPE_CHECKING

from scal3 import ui
from scal3.ui_gtk import getOrientation, gtk, pack
from scal3.ui_gtk.cal_obj_base import CalObjWidget

if TYPE_CHECKING:
	from scal3.option import Option
	from scal3.ui_gtk.pytypes import CustomizableCalObjType, StackPageType

__all__ = [
	"CustomizableCalBox",
	"CustomizableCalObj",
	"DummyCalObj",
	"newSubPageButton",
]


class DummyCalObj(CalObjWidget):
	loaded = False
	itemListCustomizable = False
	hasOptions = False
	isWrapper = False
	enableParam: Option[bool] | None = None
	itemListSeparatePage = False

	def __init__(
		self,
		name: str,
		desc: str,
		pkg: str,
		customizable: bool,
	) -> None:
		super().__init__()
		self.initVars()
		self.enable = False
		self.objName = name
		self.desc = desc
		self.moduleName = f"{pkg}.{name}"
		self.customizable = customizable
		self.optionsWidget: gtk.Widget | None = None
		self.items: list[CustomizableCalObjType] = []

	def getLoadedObj(self) -> CustomizableCalObjType:
		module = __import__(
			self.moduleName,
			fromlist=["CalObj"],
		)
		CalObj = module.CalObj
		obj = CalObj(ui.mainWin)
		obj.enable = self.enable
		# assert isinstance(obj, CustomizableCalObjType), f"{obj=}"
		return obj  # type: ignore[no-any-return]

	def updateVars(self) -> None:
		pass

	def getOptionsWidget(self) -> gtk.Widget | None:  # noqa: PLR6301
		return None

	def getSubPages(self) -> list[StackPageType]:  # noqa: PLR6301
		return []

	def showHide(self) -> None:  # noqa: PLR6301
		pass


class CustomizableCalBox(CustomizableCalObj):
	"""for GtkBox (HBox and VBox)."""

	def __init__(self, vertical: bool) -> None:
		super().__init__()
		self.box = gtk.Box(orientation=getOrientation(vertical))
		self.w: gtk.Widget = self.box
		self.initVars()
		self.vertical = vertical

	def appendItem(self, item: CustomizableCalObjType) -> None:
		super().appendItem(item)
		if item.loaded:
			pack(self.box, item.w, item.expand, item.expand)
			item.showHide()

	def repackAll(self) -> None:
		box = self.box
		for child in box.get_children():
			box.remove(child)
		for item in self.items:
			if item.loaded:
				pack(box, item.w, item.expand, item.expand)
				item.showHide()

	# Disabled the old implementation (with reorder_child) because it was
	# very buggy with Gtk3. Removing all (active) items from gtk.Box and
	# re-packing them all apears to be fast enough, so doing that instead

	def moveItem(self, i: int, j: int) -> None:
		super().moveItem(i, j)
		self.repackAll()

	def insertItemWidget(self, _i: int) -> None:
		self.repackAll()


def newSubPageButton(
	item: CustomizableCalObjType,
	page: StackPageType,
	vertical: bool = False,
	borderWidth: int = 10,
	spacing: int = 10,
	labelAngle: int = 0,
) -> StackPageButton:
	label = gtk.Label(label=page.pageLabel)
	label.set_use_markup(True)
	label.set_use_underline(True)
	label.set_angle(labelAngle)

	icon: str | None = None
	if page.pageIcon and conf.buttonIconEnable.v:
		icon = page.pageIcon

	button = StackPageButton(
		label=label,
		vertical=vertical,
		borderWidth=borderWidth,
		spacing=spacing,
		icon=icon,
	)

	def onClick(_b: gtk.Button, page: StackPageType) -> None:
		if not page.pagePath:
			raise ValueError(f"pagePath empty, {page = }")
		item.s.emit("goto-page", page.pagePath)

	button.connect("clicked", onClick, page)
	button.show_all()
	# button.label = label
	return button
