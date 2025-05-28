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


from scal3.locale_man import tr as _

__all__ = ["menuMainItemDefs"]


menuMainItemDefs = {
	"resize": dict(
		cls="ImageMenuItem",
		label=_("Resize"),
		imageName="resize.svg",
		func="onResizeFromMenu",
		signalName="button-press-event",
	),
	"onTop": dict(
		cls="CheckMenuItem",
		label=_("_On Top"),
		func="onKeepAboveClick",
		active="winKeepAbove",
	),
	"onAllDesktops": dict(
		cls="CheckMenuItem",
		label=_("On All De_sktops"),
		func="onStickyClick",
		active="winSticky",
	),
	"today": dict(
		cls="ImageMenuItem",
		label=_("Select _Today"),
		imageName="go-home.svg",
		func="goToday",
	),
	"selectDate": dict(
		cls="ImageMenuItem",
		label=_("Select _Date..."),
		imageName="select-date.svg",
		func="selectDateShow",
	),
	"dayInfo": dict(
		cls="ImageMenuItem",
		label=_("Day Info"),
		imageName="info.svg",
		func="dayInfoShow",
	),
	"customize": dict(
		cls="ImageMenuItem",
		label=_("_Customize"),
		imageName="document-edit.svg",
		func="customizeShow",
	),
	"preferences": dict(
		cls="ImageMenuItem",
		label=_("_Preferences"),
		imageName="preferences-system.svg",
		func="prefShow",
	),
	# ("addCustomEvent", dict(
	# 	cls="ImageMenuItem",
	# 	label=_("_Add Event"),
	# 	imageName="list-add.svg",
	# 	func="addCustomEvent",  # to call ui.addCustomEvent
	# )),
	"dayCalWin": dict(
		cls="ImageMenuItem",
		label=_("Day Calendar (Desktop Widget)"),
		imageName="starcal.svg",
		func="dayCalWinShow",
	),
	"eventManager": dict(
		cls="ImageMenuItem",
		label=_("_Event Manager"),
		imageName="list-add.svg",
		func="eventManShow",
	),
	"timeLine": dict(
		cls="ImageMenuItem",
		label=_("Time Line"),
		imageName="timeline.svg",
		func="timeLineShow",
	),
	"yearWheel": dict(
		cls="ImageMenuItem",
		label=_("Year Wheel"),
		imageName="year-wheel.svg",
		func="yearWheelShow",
	),  # icon? FIXME
	# ("weekCal", dict(
	# 	cls="ImageMenuItem",
	# 	label=_("Week Calendar"),
	# 	imageName="week-calendar.svg",
	# 	func="weekCalShow",
	# )),
	"exportToHtml": dict(
		cls="ImageMenuItem",
		label=_("Export to {format}").format(format="HTML"),
		imageName="export-to-html.svg",
		func="onExportClick",
	),
	"adjustTime": dict(
		cls="ImageMenuItem",
		label=_("Ad_just System Time"),
		imageName="preferences-system.svg",
		func="adjustTime",
	),
	"about": dict(
		cls="ImageMenuItem",
		label=_("_About"),
		imageName="dialog-information.svg",
		func="aboutShow",
	),
	"quit": dict(
		cls="ImageMenuItem",
		label=_("_Quit"),
		imageName="application-exit.svg",
		func="quit",
	),
}
