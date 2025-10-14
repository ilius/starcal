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
from scal3.ui_gtk.signals import SignalHandlerType

log = logger.get()

import os
from os.path import join
from time import perf_counter
from typing import TYPE_CHECKING, Any, Protocol

from scal3 import ui
from scal3.config_utils import loadSingleConfig, saveSingleConfig
from scal3.locale_man import rtl
from scal3.locale_man import tr as _
from scal3.path import confDir
from scal3.ui import conf
from scal3.ui_gtk import Dialog, Menu, gtk, pack, timeout_add
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.cal_obj_base import CalObjWidget
from scal3.ui_gtk.day_cal import DayCal
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.stack import MyStack, StackPage
from scal3.ui_gtk.utils import (
	dialog_add_button,
	get_menu_height,
	get_menu_width,
)

if TYPE_CHECKING:
	from collections.abc import Callable

	from gi.repository import Gdk as gdk

	from scal3.color_utils import ColorType
	from scal3.option import Option
	from scal3.pytypes import CellType
	from scal3.ui_gtk.cal_obj import CalBase
	from scal3.ui_gtk.day_cal import ParentWindowType
	from scal3.ui_gtk.signals import SignalHandlerType
	from scal3.ui_gtk.starcal_types import OptWidget

__all__ = ["DayCalWindow"]

confPathLive = join(confDir, "ui-daycal-live.json")

confOptionsLive = conf.dayCalWinOptionsLive

lastLiveConfChangeTime = 0.0

loadSingleConfig(confPathLive, confOptionsLive)


def saveLiveConf() -> None:  # FIXME: rename to saveConfLive
	saveSingleConfig(confPathLive, confOptionsLive)


def saveLiveConfLoop() -> bool:  # FIXME: rename to saveConfLiveLoop
	tm = perf_counter()
	if tm - lastLiveConfChangeTime > ui.saveLiveConfDelay:
		saveLiveConf()
		return False  # Finish loop
	return True  # Continue loop


def liveConfChanged() -> None:
	global lastLiveConfChangeTime
	tm = perf_counter()
	if tm - lastLiveConfChangeTime > ui.saveLiveConfDelay:
		timeout_add(
			int(ui.saveLiveConfDelay * 1000),
			saveLiveConfLoop,
		)
		lastLiveConfChangeTime = tm


class MainWinType(Protocol):
	def dayInfoShow(self, _sig: SignalHandlerType | None = None) -> None: ...
	def onStatusIconClick(self, _w: OptWidget = None) -> None: ...
	def getStatusIconPopupItems(self) -> list[gtk.MenuItem]: ...


class DayCalWindowCustomizeWindow(Dialog):
	def __init__(
		self,
		dayCal: DayCal,
		transient_for: gtk.Window | None = None,
	) -> None:
		Dialog.__init__(self, transient_for=transient_for)
		self._widget = dayCal
		# --
		self.set_title(_("Customize") + ": " + dayCal.desc)
		self.connect("delete-event", self.onDeleteEvent)
		# --
		dialog_add_button(
			self,
			res=gtk.ResponseType.OK,
			imageName="document-save.svg",
			label=_("_Save"),
			onClick=self.onSaveClick,
		)
		# --
		self.stack = MyStack(
			headerSpacing=10,
			iconSize=conf.stackIconSize.v,
		)
		pack(self.vbox, self.stack, 1, 1)
		pageWidget = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		optionsWidget = dayCal.getOptionsWidget()
		assert optionsWidget is not None
		pack(pageWidget, optionsWidget, True, True)
		pageName = "dayCalWin"
		page = StackPage()
		page.pageName = pageName
		page.pagePath = pageName
		page.pageWidget = pageWidget
		page.pageExpand = True
		page.pageExpand = True
		self.stack.addPage(page)
		for subPage in dayCal.getSubPages():
			if not subPage.pageParent:
				subPage.pageParent = pageName  # FIXME: or pagePath?
			subPage.pagePath = subPage.pageName
			self.stack.addPage(subPage)
		dayCal.s.connect("goto-page", self.gotoPageCallback)
		# --
		# self.vbox.connect("size-allocate", self.vboxSizeRequest)
		self.vbox.show_all()

	def gotoPageCallback(self, _sig: SignalHandlerType, pagePath: str) -> None:
		self.stack.gotoPage(pagePath)

	# def vboxSizeRequest(self, widget, req):
	# 	self.resize(self.w.get_size()[0], 1)

	def save(self) -> None:
		self._widget.updateVars()
		ui.saveConfCustomize()

	def onDeleteEvent(self, _w: gtk.Widget, _ge: gdk.Event) -> bool:
		self.save()
		self.hide()
		return True

	def onSaveClick(self, _w: gtk.Widget) -> None:
		self.save()
		self.hide()


class DayCalWindowWidget(DayCal):
	dragAndDropEnable = False
	doubleClickEnable = False

	backgroundColor = conf.dcalWinBackgroundColor
	dayOptions = conf.dcalWinDayParams
	monthOptions = conf.dcalWinMonthParams
	weekdayOptions = conf.dcalWinWeekdayParams
	widgetButtonsEnable = conf.dcalWinWidgetButtonsEnable
	widgetButtonsSize = conf.dcalWinWidgetButtonsSize
	widgetButtonsOpacity = conf.dcalWinWidgetButtonsOpacity
	widgetButtons = conf.dcalWinWidgetButtons
	eventIconSize = conf.dcalWinEventIconSize
	eventTotalSizeRatio = conf.dcalWinEventTotalSizeRatio
	weekdayLocalize = conf.dcalWinWeekdayLocalize
	weekdayAbbreviate = conf.dcalWinWeekdayAbbreviate
	weekdayUppercase = conf.dcalWinWeekdayUppercase

	seasonPieEnable = conf.dcalWinSeasonPieEnable
	seasonPieGeo = conf.dcalWinSeasonPieGeo
	seasonPieColors: dict[str, Option[ColorType]] = {
		"Spring": conf.dcalWinSeasonPieSpringColor,
		"Summer": conf.dcalWinSeasonPieSummerColor,
		"Autumn": conf.dcalWinSeasonPieAutumnColor,
		"Winter": conf.dcalWinSeasonPieWinterColor,
	}
	seasonPieTextColor = conf.dcalWinSeasonPieTextColor

	def __init__(self, win: ParentWindowType, mainWin: MainWinType | None) -> None:
		DayCal.__init__(self, win)
		self.mainWin = mainWin
		self.w.set_size_request(50, 50)
		self.menu: gtk.Menu | None = None
		self.customizeWindow: DayCalWindowCustomizeWindow | None = None

	@classmethod
	def getCell(cls) -> CellType:
		return ui.cells.today

	def customizeWindowCreate(self) -> None:
		if not self.customizeWindow:
			self.customizeWindow = DayCalWindowCustomizeWindow(
				self,
				transient_for=self.myWin,
			)

	def openCustomize(self, _w: gtk.Widget) -> None:
		self.customizeWindowCreate()
		win = self.myWin
		assert win is not None
		assert self.customizeWindow is not None
		x, y = win.get_position()
		w, h = win.get_size()
		cw, ch = self.customizeWindow.get_size()
		cx = x + w + 5
		cy = y
		if cx + cw > ud.workAreaW:
			cx = x - cw - 5
		if cy + ch > ud.workAreaH:
			cy = y + h - ch
		self.customizeWindow.present()
		self.customizeWindow.move(cx, cy)
		# should move() after present()

	def onButtonPress(self, obj: gtk.Widget, gevent: gdk.EventButton) -> bool:
		b = gevent.button
		if b == 1:
			buttons = self._allButtons
			if buttons:
				x, y = gevent.x, gevent.y
				w = self.w.get_allocation().width
				h = self.w.get_allocation().height
				for button in buttons:
					if button.contains(x, y, w, h):
						button.onPress(gevent)
						return True
			if self.mainWin:
				self.mainWin.onStatusIconClick()
				return True
		elif b == 3:
			self.popupMenuOnButtonPress(obj, gevent)
		elif b == 2:
			self.startMove(gevent, button=b)
		return True

	@staticmethod
	def getMenuPosFunc(
		menu: gtk.Menu,
		gevent: gdk.EventButton,
		above: bool,
	) -> Callable[[], tuple[int, int, bool]] | None:
		# FIXME: ^^^ *args
		# looks like gevent.x_root and gevent.y_root are wrong on Wayland
		# (tested on Fedora + Gnome3)
		# we should probably just pass func=None in Wayland for now
		if os.getenv("XDG_SESSION_TYPE") == "wayland":
			return None

		mw = get_menu_width(menu)
		mh = get_menu_height(menu)
		mx = int(max(0, gevent.x_root - mw) if rtl else gevent.x_root)
		my = int(max(0, gevent.y_root - mh) if above else gevent.y_root)

		if mx == my == 0:
			log.info(
				f"{mx=}, {my=}, {mw=}, {mh=}, {gevent.x_root=}, {gevent.y_root=}",
			)
			return None

		return lambda *_args: (mx, my, False)

	def getMenu(self, reverse: bool) -> gtk.Menu:
		menu = self.menu
		if menu is not None:
			menu.show_all()
			return menu
		assert self.mainWin is not None
		menu = Menu()
		if os.sep == "\\":
			from scal3.ui_gtk.windows import setupMenuHideOnLeave

			setupMenuHideOnLeave(menu)
		items = self.mainWin.getStatusIconPopupItems()
		items.insert(
			5,
			ImageMenuItem(
				_("Customize"),
				imageName="document-edit.svg",
				onActivate=self.openCustomize,
			),
		)
		if reverse:
			items.reverse()
		for item in items:
			menu.add(item)
		self.menu = menu
		menu.show_all()
		return menu

	def popupMenuOnButtonPress(self, _obj: gtk.Widget, gevent: gdk.EventButton) -> None:
		reverse = gevent.y_root > ud.screenH / 2.0
		menu = self.getMenu(reverse)
		menu.popup(
			None,
			None,
			self.getMenuPosFunc(menu, gevent, reverse),
			self,
			gevent.button,
			gevent.time,
		)
		ui.updateFocusTime()


class DayCalWindow(CalObjWidget):
	objName = "dayCalWin"
	desc = _("Day Calendar Window")

	def __init__(self, mainWin: MainWinType | None) -> None:
		super().__init__()
		self.win = win = gtk.Window()
		self.w: gtk.Widget = self.win
		self.mainWin = mainWin
		self.initVars()
		ud.windowList.appendItem(self)
		# ---
		win.resize(conf.dcalWinWidth.v, conf.dcalWinHeight.v)
		win.move(conf.dcalWinX.v, conf.dcalWinY.v)
		win.set_skip_taskbar_hint(True)
		win.set_decorated(False)
		win.set_keep_below(True)
		win.stick()
		# ---
		if TYPE_CHECKING:
			_win: ParentWindowType = self
		self._widget = DayCalWindowWidget(self, self.mainWin)
		self._widget.myWin = win  # noqa: SLF001

		self.w.connect("key-press-event", self._widget.onKeyPress)
		self.w.connect("delete-event", self.onDeleteEvent)
		self.w.connect("configure-event", self.configureEvent)

		win.add(self._widget.w)
		self._widget.show()
		self.appendItem(self._widget)

	def is_visible(self) -> bool:
		return self.win.is_visible()

	def menuCellPopup(self, widget: gtk.Widget, etime: int, x: int, y: int) -> None:
		reverse = False
		menu = self._widget.getMenu(reverse)
		coord = widget.translate_coordinates(self.w, x, y)
		if coord is None:
			raise RuntimeError(
				f"failed to translate coordinates ({x}, {y}) from widget {widget}",
			)
		dx, dy = coord
		win = self.w.get_window()
		assert win is not None
		_foo, wx, wy = win.get_origin()
		x = wx + dx
		y = wy + dy
		if rtl:
			x -= get_menu_width(menu)
		# ----
		etime = gtk.get_current_event_time()
		# log.debug("menuCellPopup", x, y, etime)
		# without the above line, the menu is not showing up
		# some GC-related pygi bug probably
		menu.popup(
			None,
			None,
			lambda *_args: (x, y, True),
			None,
			3,
			etime,
		)
		ui.updateFocusTime()

	def menuMainPopup(
		self,
		widget: gtk.Widget,
		etime: int,
		x: int,
		y: int,
	) -> None:
		pass

	def prefUpdateBgColor(self, cal: CalBase) -> None:
		pass

	def dayInfoShow(self, _w: gtk.Widget | None = None) -> None:
		if self.mainWin is None:
			return
		self.mainWin.dayInfoShow()

	def onDeleteEvent(self, _arg: Any = None, _ge: Any = None) -> bool:
		if self.mainWin:
			self.hide()
		else:
			gtk.main_quit()
		return True

	def configureEvent(self, _w: gtk.Widget, _ge: gdk.EventConfigure) -> bool:
		win = self.win
		if not win.get_property("visible"):
			return False
		wx, wy = win.get_position()
		ww, wh = win.get_size()
		conf.dcalWinX.v, conf.dcalWinY.v = (wx, wy)
		conf.dcalWinWidth.v = ww
		conf.dcalWinHeight.v = wh
		liveConfChanged()
		return False

	def customizeShow(
		self,
		widget: gtk.Widget,
	) -> None:
		self._widget.openCustomize(widget)
