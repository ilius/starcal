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
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk import timeout_add
from scal3.ui_gtk.utils import (
	openWindow,
	setClipboard,
	widgetActionCallback,
)

if TYPE_CHECKING:
	from scal3.ui_gtk import gdk, gtk
	from scal3.ui_gtk.cal_obj_base import CustomizableCalObj
	from scal3.ui_gtk.signals import SignalHandlerType
	from scal3.ui_gtk.starcal_types import OptEvent, OptWidget

__all__ = [
	"copyCurrentDate",
	"copyCurrentDateTime",
	"copyDateGetCallback",
	"createPluginsText",
	"eventSearchShow",
	"getStatusIconTooltip",
	"liveConfChanged",
	"onStatusIconPress",
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
) -> bool | None:
	if gevent.button == 2:
		# middle button press
		copyDate(calTypes.primary)
		return True
	return None
