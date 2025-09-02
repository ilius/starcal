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

from time import localtime, perf_counter
from typing import TYPE_CHECKING

from scal3 import core, locale_man, ui
from scal3.cal_types import calTypes
from scal3.locale_man import rtl  # import scal3.locale_man after core
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import gdk, gtk, timeout_add
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.utils import (
	get_menu_height,
	get_menu_width,
	openWindow,
	setClipboard,
	widgetActionCallback,
)

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.ui_gtk.cal_obj_base import CustomizableCalObj
	from scal3.ui_gtk.pytypes import CustomizableCalObjType
	from scal3.ui_gtk.right_panel import MainWinRightPanel
	from scal3.ui_gtk.signals import SignalHandlerType
	from scal3.ui_gtk.starcal_types import OptEvent, OptWidget

__all__ = [
	"childButtonPress",
	"copyCurrentDate",
	"copyCurrentDateTime",
	"copyDateGetCallback",
	"createPluginsText",
	"eventSearchShow",
	"getStatusIconTooltip",
	"liveConfChanged",
	"menuMainPopup",
	"onMainButtonPress",
	"onResizeFromMenu",
	"onScreenSizeChange",
	"onStatusIconPress",
	"onToggleRightPanel",
	"prefUpdateBgColor",
	"shouldUseAppIndicator",
	"yearWheelShow",
]


def liveConfChanged() -> None:
	tm = perf_counter()
	if tm - ui.lastLiveConfChangeTime > ui.saveLiveConfDelay:
		timeout_add(
			int(ui.saveLiveConfDelay * 1000),
			ui.saveLiveConfLoop,
		)
		ui.lastLiveConfChangeTime = tm


def prefUpdateBgColor(_sig: SignalHandlerType) -> None:
	if ui.prefWindow:
		ui.prefWindow.colorbBg.setRGBA(conf.bgColor.v)
	# else:  # FIXME
	ui.saveLiveConf()


def copyDate(calType: int) -> None:
	assert ud.dateFormatBin is not None
	setClipboard(ui.cells.current.format(ud.dateFormatBin, calType=calType))


@widgetActionCallback
def copyDateGetCallback(calType: int) -> None:
	assert ud.dateFormatBin is not None
	setClipboard(
		ui.cells.current.format(
			ud.dateFormatBin,
			calType=calType,
		),
	)


def copyCurrentDate(
	_w: OptWidget = None,
	_event: OptEvent = None,
) -> None:
	assert ud.dateFormatBin is not None
	setClipboard(ui.cells.today.format(ud.dateFormatBin))


def copyCurrentDateTime(
	_w: OptWidget = None,
	_event: OptEvent = None,
) -> None:
	assert ud.dateFormatBin is not None
	assert ud.clockFormatBin is not None
	dateStr = ui.cells.today.format(ud.dateFormatBin)
	timeStr = ui.cells.today.format(
		ud.clockFormatBin,
		tm=localtime()[3:6],
	)
	setClipboard(f"{dateStr}, {timeStr}")


def createPluginsText() -> CustomizableCalObj:
	from scal3.ui_gtk.pluginsText import PluginsTextBox

	return PluginsTextBox(insideExpanderParam=conf.pluginsTextInsideExpander)


def shouldUseAppIndicator() -> bool:
	if not conf.useAppIndicator.v:
		return False
	try:
		import scal3.ui_gtk.starcal_appindicator  # noqa: F401
	except (ImportError, ValueError):
		return False
	return True


def getStatusIconTooltip() -> str:
	# tt = core.weekDayName[core.getWeekDay(*ddate)]
	tt = core.weekDayName[core.jwday(ui.cells.today.jd)]
	# if conf.pluginsTextStatusIcon.v:--?????????
	# 	sep = _(",")+" "
	# else:
	sep = "\n"
	for calType in calTypes.active:
		y, m, d = ui.cells.today.dates[calType]
		tt += sep + _(d) + " " + locale_man.getMonthName(calType, m, y) + " " + _(y)
	if conf.pluginsTextStatusIcon.v:
		text = ui.cells.today.getPluginsText()
		if text:
			tt += "\n\n" + text  # .replace("\t", "\n") # FIXME
	for item in ui.cells.today.getEventsData():
		if not item.showInStatusIcon:
			continue
		itemS = ""
		if item.time:
			itemS += item.time + " - "
		itemS += item.text[0]
		tt += "\n\n" + itemS
	return tt


def eventSearchCreate() -> None:
	if ui.eventSearchWin is None:
		from scal3.ui_gtk.event.search_events import EventSearchWindow

		ui.eventSearchWin = EventSearchWindow()


def eventSearchShow(
	_w: OptWidget = None,
	_ge: OptEvent = None,
) -> None:
	eventSearchCreate()
	openWindow(ui.eventSearchWin.w)


def yearWheelShow(
	_w: OptWidget = None,
	_ge: OptEvent = None,
) -> None:
	if not ui.yearWheelWin:
		from scal3.ui_gtk.year_wheel import YearWheelWindow

		ui.yearWheelWin = YearWheelWindow()
	openWindow(ui.yearWheelWin.w)


def onStatusIconPress(
	_obj: gtk.Widget,
	gevent: gdk.EventButton,
) -> bool:
	if gevent.button == 2:
		# middle button press
		copyDate(calTypes.primary)
		return True
	return False


def onToggleRightPanel(
	rightPanel: MainWinRightPanel,
	win: gtk.Window,
) -> None:
	enable = not conf.mainWinRightPanelEnable.v
	conf.mainWinRightPanelEnable.v = enable
	rightPanel.enable = enable
	rightPanel.showHide()
	rightPanel.broadcastDateChange()

	# update Enable checkbutton in Customize dialog
	rightPanel.onToggleFromMainWin()

	if conf.mainWinRightPanelResizeOnToggle.v:
		ww, wh = win.get_size()
		mw = conf.mainWinRightPanelWidth.v
		if enable:
			ww += mw
		else:
			ww -= mw
		if rtl:
			wx, wy = win.get_position()
			wx += mw * (-1 if enable else 1)
			win.move(wx, wy)
		win.resize(ww, wh)


def onScreenSizeChange(win: gtk.Window, rect: gdk.Rectangle) -> None:
	if conf.winMaximized.v:
		return
	winWidth = min(conf.winWidth.v, rect.width)
	winHeight = min(conf.winHeight.v, rect.height)
	winX = min(conf.winX.v, rect.width - conf.winWidth.v)
	winY = min(conf.winY.v, rect.height - conf.winHeight.v)

	if (winWidth, winHeight) != (conf.winWidth.v, conf.winHeight.v):
		win.resize(winWidth, winHeight)

	if (winX, winY) != (conf.winX.v, conf.winY.v):
		win.move(winX, winY)


def childButtonPress(
	win: gtk.Window,
	menuMainCreate: Callable[[], gtk.Menu],
	gevent: gdk.EventButton,
) -> bool:
	b = gevent.button
	# log.debug(dir(gevent))
	# foo, x, y, mask = gevent.get_window().get_pointer()
	# x, y = self.w.get_pointer()
	x, y = int(gevent.x_root), int(gevent.y_root)
	result = False
	if b == 1:
		win.begin_move_drag(gevent.button, x, y, gevent.time)
		result = True
	elif b == 3:
		menuMain = menuMainCreate()
		if rtl:
			x -= get_menu_width(menuMain)
		menuMain.popup(
			None,
			None,
			lambda *_args: (x, y, True),
			None,
			3,
			gevent.time,
		)
		result = True
	ui.updateFocusTime()
	return result


def onResizeFromMenu(
	menuMain: gtk.Menu | None,
	win: gtk.Window,
	gevent: gdk.EventButton,
) -> bool:
	if menuMain:
		menuMain.hide()
	conf.winMaximized.v = False
	ui.updateFocusTime()
	win.begin_resize_drag(
		gdk.WindowEdge.SOUTH_EAST,
		gevent.button,
		int(gevent.x_root),
		int(gevent.y_root),
		gevent.time,
	)
	return True


def onMainButtonPress(
	win: gtk.Window,
	menuMainCreate: Callable[[], gtk.Menu],
	gevent: gdk.EventButton,
) -> bool:
	# only for mainVBox for now, not rightPanel
	# does not work for statusBar, don't know why
	# log.debug(f"MainWin: onMainButtonPress, {gevent.button=}")
	b = gevent.button
	if b == 3:
		menuMain = menuMainCreate()
		menuMain.popup(None, None, None, None, 3, gevent.time)
	elif b == 1:
		# FIXME: used to cause problems with `ConButton`
		# when using 'pressed' and 'released' signals
		win.begin_move_drag(
			gevent.button,
			int(gevent.x_root),
			int(gevent.y_root),
			gevent.time,
		)
	ui.updateFocusTime()
	return False


def menuMainPopup(
	w: gtk.Widget,
	menuMainCreate: Callable[[], gtk.Menu],
	x: int,
	y: int,
	item: CustomizableCalObjType,
) -> None:
	widget = item.w
	menu = menuMainCreate()
	dcoord = widget.translate_coordinates(w, x, y)
	assert dcoord is not None
	dx, dy = dcoord
	win = w.get_window()
	assert win is not None
	_foo, wx, wy = win.get_origin()
	x = wx + dx
	y = wy + dy
	if rtl:
		x -= get_menu_width(menu)
	menuH = get_menu_height(menu)
	if menuH > 0 and y + menuH > ud.screenH:
		if y - menuH >= 0:
			y -= menuH
		else:
			y -= menuH // 2
	etime = gtk.get_current_event_time()
	# log.debug("menuMainPopup", x, y, etime)
	menu.popup(
		None,
		None,
		lambda *_args: (x, y, True),
		None,
		3,
		etime,
	)
	ui.updateFocusTime()
