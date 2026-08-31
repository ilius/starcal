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

from scal3.color_utils import RGBA
from scal3.ui.options._base import CUSTOMIZE, LIVE, MAIN_CONF, NEED_RESTART, OptionData

__all__ = ["confOptionsData"]

confOptionsData: list[OptionData] = [
	OptionData(
		name="mainWin.openOnStartup",
		v3Name="showMain",
		flags=MAIN_CONF,
		type="bool",
		where="Preferences: General",
		desc="Open main window on start",
		default=True,
	),
	OptionData(
		name="mainWin.inTaskbar",
		v3Name="winTaskbar",
		flags=MAIN_CONF | NEED_RESTART,
		type="bool",
		where="Preferences: General",
		desc="Window in Taskbar",
		default=False,
	),
	OptionData(
		name="useAppIndicator",
		v3Name="useAppIndicator",
		flags=MAIN_CONF | NEED_RESTART,
		type="bool",
		where="Preferences: General",
		desc="Use AppIndicator",
		default=True,
	),
	OptionData(
		name="useLegacyStatusIcon",
		v3Name="useLegacyStatusIcon",
		flags=MAIN_CONF | NEED_RESTART,
		type="bool",
		where="Preferences: Status Icon",
		desc="Use Legacy Status Icon",
		default=True,
	),
	# ----------------- mainWin live info
	OptionData(
		name="mainWin.geo.x",
		v3Name="winX",
		flags=LIVE,
		type="int",
		where="MainWin: Move",
		desc="Window X",
		default=0,
	),
	OptionData(
		name="mainWin.geo.y",
		v3Name="winY",
		flags=LIVE,
		type="int",
		where="MainWin: Move",
		desc="Window Y",
		default=0,
	),
	OptionData(
		name="mainWin.geo.width",
		v3Name="winWidth",
		flags=LIVE,
		type="int",
		where="MainWin: Resize",
		desc="Window Width",
		default=480,
	),
	OptionData(
		name="mainWin.geo.height",
		v3Name="winHeight",
		flags=LIVE,
		type="int",
		where="MainWin: Resize",
		desc="Window Height",
		default=300,
	),
	OptionData(
		name="mainWin.keepAbove",
		v3Name="winKeepAbove",
		flags=LIVE,
		type="bool",
		where="MainWin: Menu",
		desc="On Top",
		default=True,
	),
	OptionData(
		name="mainWin.sticky",
		v3Name="winSticky",
		flags=LIVE,
		type="bool",
		where="MainWin: Menu",
		desc="On All Desktops",
		default=True,
	),
	OptionData(
		name="mainWin.maximized",
		v3Name="winMaximized",
		flags=LIVE,
		type="bool",
		where="MainWin: Window Controller: Maximize Window",
		desc="Window Maximized",
		default=False,
	),
	# ----------------- mainWin customize
	OptionData(
		name="mainWin.items",
		v3Name="mainWinItems",
		flags=CUSTOMIZE,
		type="list[tuple[str, bool]]",
		where="MainWin: Customize: Main Panel",
		desc="Items",
		default=[
			("toolbar", True),
			("labelBox", True),
			("monthCal", False),
			("weekCal", True),
			("dayCal", False),
			("monthPBar", False),
			("seasonPBar", True),
			("yearPBar", False),
		],
	),
	# -----------------= mainWin customize footer
	OptionData(
		name="mainWin.footer.items",
		v3Name="mainWinFooterItems",
		flags=CUSTOMIZE,
		type="list[str]",
		where="MainWin: Customize: (Footer)",
		desc="Footer Items",
		default=["pluginsText", "eventDayView", "statusBar"],
	),
	# ------------ pluginsText
	OptionData(
		name="mainWin.footer.pluginsText.enable",
		v3Name="pluginsTextEnable",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: (Footer): Plugins Text",
		desc="Enable",
		default=False,
	),
	OptionData(
		name="mainWin.footer.pluginsText.insideExpander",
		v3Name="pluginsTextInsideExpander",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: (Footer): Plugins Text",
		desc="Inside Expander",
		default=True,
	),
	OptionData(
		name="mainWin.footer.pluginsText.isExpanded",
		v3Name="pluginsTextIsExpanded",
		flags=LIVE,
		type="bool",
		where="MainWin: (Footer): Plugins Text",
		desc="Is Expanded",
		default=True,
	),
	# ------------ eventDayView
	OptionData(
		name="mainWin.footer.eventDayView.enable",
		v3Name="eventDayViewEnable",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: (Footer): Events of Day",
		desc="Enable",
		default=False,
	),
	OptionData(
		name="mainWin.footer.eventDayView.eventSep",
		v3Name="eventDayViewEventSep",
		flags=CUSTOMIZE,
		type="str",
		where="MainWin: Customize: (Footer): Events of Day",
		desc="Event Text Separator",
		default="\n",
	),
	OptionData(
		name="mainWin.footer.eventDayView.maxHeight",
		v3Name="eventViewMaxHeight",
		flags=CUSTOMIZE,
		type="int",
		valid="IntSpin(1, 9999, 1)",
		where="MainWin: Customize: (Footer): Events of Day",
		desc="Maximum Height",
		default=200,
	),
	# ------------ statusBar
	OptionData(
		name="statusBar.enable",
		v3Name="statusBarEnable",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: (Footer): Status Bar",
		desc="Enable",
		default=True,
	),
	OptionData(
		name="statusBar.dates.reverseOrder",
		v3Name="statusBarDatesReverseOrder",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: (Footer): Status Bar",
		desc="Reverse the order of dates",
		default=False,
	),
	OptionData(
		name="statusBar.dates.colorEnable",
		v3Name="statusBarDatesColorEnable",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: (Footer): Status Bar",
		desc="Dates Color",
		default=False,
	),
	OptionData(
		name="statusBar.dates.color",
		v3Name="statusBarDatesColor",
		flags=CUSTOMIZE,
		type="ColorType",
		where="MainWin: Customize: (Footer): Status Bar",
		desc="Dates Color",
		default=RGBA(255, 132, 255, 255),
	),
]
