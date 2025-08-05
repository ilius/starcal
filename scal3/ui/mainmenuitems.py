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
from scal3.ui_gtk.menuitems import CheckMenuItem, ImageMenuItem

log = logger.get()


from scal3.locale_man import tr as _

__all__ = ["menuMainItemDefs"]


class MainMenuItemArgsType(TypedDict):
	imageName: NotRequired[str | None]  # for ImageMenuItem
	active: NotRequired[str | None]  # for CheckMenuItem


class MainMenuItemType(TypedDict):
	cls: type
	label: str
	args: MainMenuItemArgsType


menuMainItemDefs: dict[str, MainMenuItemType] = {
	"onTop": dict(
		cls=CheckMenuItem,
		label=_("_On Top"),
		args={"active": "winKeepAbove"},
	),
	"onAllDesktops": dict(
		cls=CheckMenuItem,
		label=_("On All De_sktops"),
		args={"active": "winSticky"},
	),
	"today": dict(
		cls=ImageMenuItem,
		label=_("Select _Today"),
		args={"imageName": "go-home.svg"},
	),
	"selectDate": dict(
		cls=ImageMenuItem,
		label=_("Select _Date..."),
		args={"imageName": "select-date.svg"},
	),
	"dayInfo": dict(
		cls=ImageMenuItem,
		label=_("Day Info"),
		args={"imageName": "info.svg"},
	),
	"customize": dict(
		cls=ImageMenuItem,
		label=_("_Customize"),
		args={"imageName": "document-edit.svg"},
	),
	"preferences": dict(
		cls=ImageMenuItem,
		label=_("_Preferences"),
		args={"imageName": "preferences-system.svg"},
	),
	# "addCustomEvent": dict(
	# 	cls=ImageMenuItem,
	# 	label=_("_Add Event"),
	# 	args={"imageName": "list-add.svg"},
	# ),
	"dayCalWin": dict(
		cls=ImageMenuItem,
		label=_("Day Calendar (Desktop Widget)"),
		args={"imageName": "starcal.svg"},
	),
	"eventManager": dict(
		cls=ImageMenuItem,
		label=_("_Event Manager"),
		args={"imageName": "list-add.svg"},
	),
	"timeLine": dict(
		cls=ImageMenuItem,
		label=_("Time Line"),
		args={"imageName": "timeline.svg"},
	),
	"yearWheel": dict(
		cls=ImageMenuItem,
		label=_("Year Wheel"),
		args={"imageName": "year-wheel.svg"},
	),  # icon? FIXME
	# "weekCal": dict(
	# 	cls=ImageMenuItem,
	# 	label=_("Week Calendar"),
	# 	args={"imageName": "week-calendar.svg"},
	# ),
	"exportToHtml": dict(
		cls=ImageMenuItem,
		label=_("Export to {format}").format(format="HTML"),
		args={"imageName": "export-to-html.svg"},
	),
	"adjustTime": dict(
		cls=ImageMenuItem,
		label=_("Ad_just System Time"),
		args={"imageName": "preferences-system.svg"},
	),
	"about": dict(
		cls=ImageMenuItem,
		label=_("_About"),
		args={"imageName": "dialog-information.svg"},
	),
	"quit": dict(
		cls=ImageMenuItem,
		label=_("_Quit"),
		args={"imageName": "application-exit.svg"},
	),
}
