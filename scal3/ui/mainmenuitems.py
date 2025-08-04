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

from typing import NotRequired, TypedDict

from scal3 import logger
from scal3.ui_gtk.menuitems import CheckMenuItem, ImageMenuItem, ResizeMenuItem

log = logger.get()


from scal3.locale_man import tr as _

__all__ = ["menuMainItemDefs"]


class MainMenuItemArgsType(TypedDict):
	imageName: NotRequired[str | None]  # for ImageMenuItem
	active: NotRequired[str | None]  # for CheckMenuItem


class MainMenuItemType(TypedDict):
	cls: type
	label: str
	func: str
	args: MainMenuItemArgsType


menuMainItemDefs: dict[str, MainMenuItemType] = {
	"resize": dict(
		cls=ResizeMenuItem,
		label=_("Resize"),
		func="onResizeFromMenu",
		args={},
	),
	"onTop": dict(
		cls=CheckMenuItem,
		label=_("_On Top"),
		func="onKeepAboveClick",
		args={"active": "winKeepAbove"},
	),
	"onAllDesktops": dict(
		cls=CheckMenuItem,
		label=_("On All De_sktops"),
		func="onStickyClick",
		args={"active": "winSticky"},
	),
	"today": dict(
		cls=ImageMenuItem,
		label=_("Select _Today"),
		func="goToday",
		args={"imageName": "go-home.svg"},
	),
	"selectDate": dict(
		cls=ImageMenuItem,
		label=_("Select _Date..."),
		func="selectDateShow",
		args={"imageName": "select-date.svg"},
	),
	"dayInfo": dict(
		cls=ImageMenuItem,
		label=_("Day Info"),
		func="dayInfoShow",
		args={"imageName": "info.svg"},
	),
	"customize": dict(
		cls=ImageMenuItem,
		label=_("_Customize"),
		func="customizeShow",
		args={"imageName": "document-edit.svg"},
	),
	"preferences": dict(
		cls=ImageMenuItem,
		label=_("_Preferences"),
		func="prefShow",
		args={"imageName": "preferences-system.svg"},
	),
	# "addCustomEvent": dict(
	# 	cls=ImageMenuItem,
	# 	label=_("_Add Event"),
	# 	func="addCustomEvent",  # to call ui.addCustomEvent
	# 	args={"imageName": "list-add.svg"},
	# ),
	"dayCalWin": dict(
		cls=ImageMenuItem,
		label=_("Day Calendar (Desktop Widget)"),
		func="dayCalWinShow",
		args={"imageName": "starcal.svg"},
	),
	"eventManager": dict(
		cls=ImageMenuItem,
		label=_("_Event Manager"),
		func="eventManShow",
		args={"imageName": "list-add.svg"},
	),
	"timeLine": dict(
		cls=ImageMenuItem,
		label=_("Time Line"),
		func="timeLineShow",
		args={"imageName": "timeline.svg"},
	),
	"yearWheel": dict(
		cls=ImageMenuItem,
		label=_("Year Wheel"),
		func="yearWheelShow",
		args={"imageName": "year-wheel.svg"},
	),  # icon? FIXME
	# ("weekCal", dict(
	# 	cls=ImageMenuItem,
	# 	label=_("Week Calendar"),
	# 	func="weekCalShow",
	# 	args={"imageName": "week-calendar.svg"},
	# )),
	"exportToHtml": dict(
		cls=ImageMenuItem,
		label=_("Export to {format}").format(format="HTML"),
		func="onExportClick",
		args={"imageName": "export-to-html.svg"},
	),
	"adjustTime": dict(
		cls=ImageMenuItem,
		label=_("Ad_just System Time"),
		func="adjustTime",
		args={"imageName": "preferences-system.svg"},
	),
	"about": dict(
		cls=ImageMenuItem,
		label=_("_About"),
		func="aboutShow",
		args={"imageName": "dialog-information.svg"},
	),
	"quit": dict(
		cls=ImageMenuItem,
		label=_("_Quit"),
		func="quit",
		args={"imageName": "application-exit.svg"},
	),
}
