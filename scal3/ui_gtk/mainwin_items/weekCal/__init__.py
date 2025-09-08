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

from typing import TYPE_CHECKING, Any

from scal3 import ui
from scal3.locale_man import rtl, rtlSgn
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import gdk, getScrollValue, gtk, pack
from scal3.ui_gtk.cal_obj import CalBase
from scal3.ui_gtk.cal_obj_base import CustomizableCalObj
from scal3.ui_gtk.customize import CustomizableCalBox, newSubPageButton
from scal3.ui_gtk.mainwin_items.weekCal.days import DaysOfMonthColumnGroup
from scal3.ui_gtk.mainwin_items.weekCal.moon import MoonStatusColumn
from scal3.ui_gtk.option_ui.spin import FloatSpinOptionUI
from scal3.ui_gtk.stack import StackPage

from .base import ColumnBase
from .events import (
	EventsBoxColumn,
	EventsCountColumn,
	EventsIconColumn,
	EventsTextColumn,
)
from .mainmenu import MainMenuToolBoxItem
from .plugins import PluginsTextColumn
from .toolbar import ToolbarColumn
from .weekdays import WeekDaysColumn

if TYPE_CHECKING:
	from gi.repository import GObject

	from scal3.pytypes import WeekStatusType
	from scal3.ui_gtk.option_ui.base import OptionUI
	from scal3.ui_gtk.pytypes import CustomizableCalObjType, StackPageType
	from scal3.ui_gtk.starcal_types import MainWinType


__all__ = ["CalObj"]


class CalObj(CalBase):
	objName = "weekCal"
	desc = _("Week Calendar")
	vertical = False
	expand = True
	optionsPageSpacing = 7
	itemListSeparatePage = True
	itemsPageTitle = _("Columns")
	itemsPageButtonBorder = 15
	myKeys = CalBase.myKeys | {
		"up",
		"down",
		"left",
		"right",
		"page_up",
		"k",
		"p",
		"page_down",
		"j",
		"n",
		"end",
		"f10",
		"m",
	}

	def do_get_preferred_height(self) -> tuple[int, int]:  # noqa: PLR6301
		return 0, int(conf.winHeight.v / 3)

	def __init__(self, win: MainWinType) -> None:
		super().__init__()
		self.box = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.w: gtk.Widget = self.box
		self.w.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.parentWin = win
		# self.items: list[ColumnBase] = []
		self.initCal()
		# ----------------------
		self.w.connect("scroll-event", self.scroll)
		self.w.connect("button-press-event", self.onButtonPress)
		# -----
		# set in self.updateStatus
		self.status: WeekStatusType | None = None
		self.cellIndex = 0
		# -----
		defaultItems: list[ColumnBase] = [
			ToolbarColumn(self),
			WeekDaysColumn(self),
			PluginsTextColumn(self),
			EventsIconColumn(self),
			EventsCountColumn(self),
			EventsTextColumn(self),
			EventsBoxColumn(self),
			DaysOfMonthColumnGroup(self),
			MoonStatusColumn(self),
		]
		defaultItemsDict = {item.objName: item for item in defaultItems}
		itemNames = list(defaultItemsDict)
		for name, enable in conf.wcalItems.v:
			item = defaultItemsDict.get(name)
			if item is None:
				log.info(f"weekCal item '{name}' does not exist")
				continue
			item.enable = enable
			self.appendItem(item)
			itemNames.remove(name)
		for name in itemNames:
			item = defaultItemsDict[name]
			item.enable = False
			self.appendItem(item)

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

	def moveItem(self, i: int, j: int) -> None:
		CustomizableCalObj.moveItem(self, i, j)
		self.repackAll()

	def insertItemWidget(self, _i: int) -> None:
		self.repackAll()

	def getOptionsWidget(self) -> gtk.Widget | None:
		from scal3.ui_gtk.option_ui.check import CheckOptionUI
		from scal3.ui_gtk.option_ui.check_mix import CheckColorOptionUI
		from scal3.ui_gtk.option_ui.color import ColorOptionUI

		if self.optionsWidget:
			return self.optionsWidget

		optionsWidget = gtk.Box(
			orientation=gtk.Orientation.VERTICAL,
			spacing=self.optionsPageSpacing,
		)
		option: OptionUI
		# ------------
		pageVBox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=20)
		pageVBox.set_border_width(10)
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# ----
		option = FloatSpinOptionUI(
			option=conf.wcalCursorLineWidthFactor,
			bounds=(0, 1),
			digits=2,
			step=0.1,
			label=_("Line Width Factor"),
			labelSizeGroup=sgroup,
			live=True,
			onChangeFunc=self.w.queue_draw,
		)
		pack(pageVBox, option.getWidget())
		# ---
		option = FloatSpinOptionUI(
			option=conf.wcalCursorRoundingFactor,
			bounds=(0, 1),
			digits=2,
			step=0.1,
			label=_("Rounding Factor"),
			labelSizeGroup=sgroup,
			live=True,
			onChangeFunc=self.w.queue_draw,
		)
		pack(pageVBox, option.getWidget())
		# ---
		pageVBox.show_all()
		# ---
		page = StackPage()
		page.pageWidget = pageVBox
		page.pageName = "cursor"
		page.pageTitle = _("Cursor")
		page.pageLabel = _("Cursor")
		page.pageIcon = ""
		self.subPages = [page]
		# ---
		button = newSubPageButton(self.s, page, borderWidth=10)
		pack(optionsWidget, button, padding=10)
		# ---------
		option = FloatSpinOptionUI(
			option=conf.wcalTextSizeScale,
			bounds=(0.01, 1),
			digits=3,
			step=0.1,
			label=_("Text Size Scale"),
			live=True,
			onChangeFunc=self.w.queue_draw,
		)
		pack(optionsWidget, option.getWidget())
		# ---
		option = CheckColorOptionUI(
			CheckOptionUI(option=conf.wcalGrid, label=_("Grid")),
			ColorOptionUI(option=conf.wcalGridColor, useAlpha=True),
			live=True,
			onChangeFunc=self.w.queue_draw,
		)
		pack(optionsWidget, option.getWidget())
		# ---
		frame = gtk.Frame(label=_("Row's Upper Gradient"))
		frameBox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		frameBox.set_border_width(5)
		frame.add(frameBox)
		option = CheckColorOptionUI(
			CheckOptionUI(
				option=conf.wcalUpperGradientEnable,
				label=_("Color"),
			),
			ColorOptionUI(option=conf.wcalUpperGradientColor, useAlpha=True),
			live=True,
			onChangeFunc=self.w.queue_draw,
		)
		pack(frameBox, option.getWidget())
		option = FloatSpinOptionUI(
			option=conf.wcalUpperGradientSize,
			bounds=(0, 5),
			digits=2,
			step=0.1,
			label=_("Size"),
			live=True,
			onChangeFunc=self.w.queue_draw,
		)
		pack(frameBox, option.getWidget())
		pack(optionsWidget, frame)
		# ---------
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def getSubPages(self) -> list[StackPageType]:
		if self.subPages is not None:
			return self.subPages
		self.getOptionsWidget()
		assert self.subPages is not None
		return self.subPages

	def updateVars(self) -> None:
		CustomizableCalBox.updateVars(self)
		conf.wcalItems.v = self.getItemsData()

	def updateStatus(self) -> None:
		self.status = ui.cells.getCurrentWeekStatus()
		index = ui.cells.current.jd - self.status[0].jd
		if index > 6:
			log.info(f"warning: drawCursorFg: {index = }")
			return
		self.cellIndex = index

	def onConfigChange(self) -> None:
		self.updateStatus()
		super().onConfigChange()
		self.w.queue_draw()

	def onDateChange(self) -> None:
		self.updateStatus()
		super().onDateChange()
		self.w.queue_draw()
		# for item in self.items:
		# 	item.queue_draw()

	def goBackward4(self, _obj: GObject.Object) -> None:
		self.jdPlus(-28)

	def goBackward(self, _obj: GObject.Object) -> None:
		self.jdPlus(-7)

	def goForward(self, _obj: GObject.Object) -> None:
		self.jdPlus(7)

	def goForward4(self, _obj: GObject.Object) -> None:
		self.jdPlus(28)

	def itemContainsGdkWindow(self, item: gtk.Widget, col_win: gdk.Window) -> bool:
		if col_win == item.get_window():
			return True
		if isinstance(item, gtk.Container):
			for child in item.get_children():
				if self.itemContainsGdkWindow(child, col_win):
					return True
		return False

	def findColumnWidgetByGdkWindow(self, col_win: gdk.Window) -> ColumnBase | None:
		for item in self.items:
			if isinstance(item, gtk.Box):
				# right now only DaysOfMonthColumnGroup
				for child in item.get_children():
					if self.itemContainsGdkWindow(child, col_win):
						return child
			elif self.itemContainsGdkWindow(item.w, col_win):
				assert isinstance(item, ColumnBase), f"{item=}"
				return item
		return None

	def onButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		assert self.status is not None
		col = self.findColumnWidgetByGdkWindow(gevent.get_window())
		if not col:
			return False
		if not col.autoButtonPressHandler:
			return False
		# ---
		# stub for gevent.get_coords() is wrong!
		x_col = int(gevent.x)
		y_col = int(gevent.y)
		# x_col is relative to the column, not to the weekCal
		# y_col is relative to the column, but also to the weekCal,
		# 		because we have nothing above columns
		# ---
		i = int(y_col * 7.0 / self.w.get_allocation().height)
		cell = self.status[i]
		self.gotoJd(cell.jd)
		if gevent.type == gdk.EventType.DOUBLE_BUTTON_PRESS:
			self.s.emit("double-button-press")
		if gevent.button == 3:
			coords = col.w.translate_coordinates(self.w, x_col, y_col)
			assert coords is not None
			x, y = coords
			self.s.emit("popup-cell-menu", x, y)
		return True

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey) -> bool:
		if CalBase.onKeyPress(self, arg, gevent):
			return True
		kname = gdk.keyval_name(gevent.keyval)
		if not kname:
			return False
		kname = kname.lower()
		if kname == "up":
			self.jdPlus(-1)
		elif kname == "down":
			self.jdPlus(1)
		elif kname == "left":
			self.jdPlus(rtlSgn() * 7)
		elif kname == "right":
			self.jdPlus(rtlSgn() * -7)
		elif kname == "end":
			assert self.status is not None
			self.gotoJd(self.status[-1].jd)
		elif kname in {"page_up", "k", "p"}:
			self.jdPlus(-7)
		elif kname in {"page_down", "j", "n"}:
			self.jdPlus(7)
		elif kname in {"f10", "m"}:
			if gevent.state & gdk.ModifierType.SHIFT_MASK:
				# Simulate right click (key beside Right-Ctrl)
				self.s.emit("popup-cell-menu", *self.getCellPos())
			else:
				self.s.emit("popup-main-menu", *self.getMainMenuPos())
		else:
			return False
		return True

	def scroll(self, _w: gtk.Widget, gevent: gdk.EventScroll) -> bool:
		d = getScrollValue(gevent)
		if d == "up":
			self.jdPlus(-1)
			return False
		if d == "down":
			self.jdPlus(1)
			return False
		return False

	def getCellPos(self, *_args: Any) -> tuple[int, int]:
		alloc = self.w.get_allocation()
		return (
			int(alloc.width / 2),
			int((ui.cells.current.weekDayIndex + 1) * alloc.height / 7),
		)

	def getToolbar(self) -> ToolbarColumn | None:
		for item in self.items:
			if item.enable and isinstance(item.objName, ToolbarColumn):
				return item
		return None

	def getMainMenuPos(self) -> tuple[int, int]:
		toolbar = self.getToolbar()
		if toolbar:
			for item in toolbar.items:
				if item.enable and isinstance(item, MainMenuToolBoxItem):
					return item.getMenuPos()
		if rtl:
			return self.w.get_allocation().width, 0

		return 0, 0
