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

from scal3.ui.options._base import CUSTOMIZE, LIVE, OptionData

__all__ = ["confOptionsData"]

confOptionsData: list[OptionData] = [
	# ------------ Window Controller
	OptionData(
		name="winController.enable",
		v3Name="winControllerEnable",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: Window Controller",
		desc="Enable",
		default=True,
	),
	OptionData(
		name="winController.theme",
		v3Name="winControllerTheme",
		flags=CUSTOMIZE,
		type="str",
		where="MainWin: Customize: Window Controller",
		desc="Theme",
		default="default",
	),
	OptionData(
		name="winController.buttons",
		v3Name="winControllerButtons",
		flags=CUSTOMIZE,
		type="list[tuple[str, bool]]",
		where="MainWin: Customize: Window Controller",
		desc="Buttons",
		default=[
			("sep", True),
			("rightPanel", True),
			("min", True),
			("max", True),
			("close", True),
			("sep", False),
			("sep", False),
			("sep", False),
		],
	),
	OptionData(
		name="winController.iconSize",
		v3Name="winControllerIconSize",
		flags=CUSTOMIZE,
		type="int",
		valid="IntSpin(5, 128, 1)",
		where="MainWin: Customize: Window Controller",
		desc="Icon Size",
		default=24,
	),
	OptionData(
		name="winController.border",
		v3Name="winControllerBorder",
		flags=CUSTOMIZE,
		type="int",
		valid="IntSpin(0, 99, 1)",
		where="MainWin: Customize: Window Controller",
		desc="Buttons Border",
		default=0,
	),
	OptionData(
		name="winController.spacing",
		v3Name="winControllerSpacing",
		flags=CUSTOMIZE,
		type="int",
		valid="IntSpin(0, 99, 1)",
		where="MainWin: Customize: Window Controller",
		desc="Space between buttons",
		default=0,
	),
	OptionData(
		name="winController.pressState",
		v3Name="winControllerPressState",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: Window Controller",
		desc="Change icon on button press",
		default=False,
	),
	# ------------ rightPanel
	OptionData(
		name="rightPanel.enable",
		v3Name="mainWinRightPanelEnable",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: Right Panel",
		desc="Enable",
		default=True,
	),
	OptionData(
		name="rightPanel.heightRatio",
		v3Name="mainWinRightPanelRatio",
		flags=LIVE,
		type="float",
		where="MainWin: Right Panel",
		desc="Ration of height of upper half to the whole",
		default=0.5,
	),
	OptionData(
		name="rightPanel.swap",
		v3Name="mainWinRightPanelSwap",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Right Panel: Context menu",
		desc="Swap Plugins Text and Events Text",
		default=False,
	),
	OptionData(
		name="rightPanel.width",
		v3Name="mainWinRightPanelWidth",
		flags=CUSTOMIZE,
		type="int",
		valid="IntSpin(1, 9999, 10)",
		where="MainWin: Customize: Right Panel: Sizes",
		desc="Width: Fixed width",
		default=200,
	),
	OptionData(
		name="rightPanel.widthRatio",
		v3Name="mainWinRightPanelWidthRatio",
		flags=CUSTOMIZE,
		type="float",
		valid="FloatSpin(0, 1, 0.01, 3)",
		where="MainWin: Customize: Right Panel: Sizes",
		desc="Width: Relative to window",
		default=0.25,
	),
	OptionData(
		name="rightPanel.widthRatioEnable",
		v3Name="mainWinRightPanelWidthRatioEnable",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: Right Panel: Sizes",
		desc="Width: Relative to window",
		default=True,
	),
	OptionData(
		name="rightPanel.event.fontEnable",
		v3Name="mainWinRightPanelEventFontEnable",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: Right Panel: Events Text",
		desc="Font",
		default=False,
	),
	OptionData(
		name="rightPanel.event.font",
		v3Name="mainWinRightPanelEventFont",
		flags=CUSTOMIZE,
		type="Font | None",
		where="MainWin: Customize: Right Panel: Events Text",
		desc="Font",
		default=None,
	),
	OptionData(
		"rightPanel.event.timeFontEnable",
		v3Name="mainWinRightPanelEventTimeFontEnable",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: Right Panel: Events Text",
		desc="Time Font",
		default=False,
	),
	OptionData(
		name="rightPanel.event.timeFont",
		v3Name="mainWinRightPanelEventTimeFont",
		flags=CUSTOMIZE,
		type="Font | None",
		where="MainWin: Customize: Right Panel: Events Text",
		desc="Time Font",
		default=None,
	),
	OptionData(
		name="rightPanel.event.justification",
		v3Name="mainWinRightPanelEventJustification",
		flags=CUSTOMIZE,
		type="str",  # left, center, right
		where="MainWin: Customize: Right Panel: Events Text",
		desc="Text Alignment",
		default="left",
	),
	OptionData(
		name="rightPanel.event.sep",
		v3Name="mainWinRightPanelEventSep",
		flags=CUSTOMIZE,
		type="str",
		where="MainWin: Customize: Right Panel: Events Text",
		desc="Event Text Separator",
		default="\n\n",
	),
	OptionData(
		name="rightPanel.plugins.fontEnable",
		v3Name="mainWinRightPanelPluginsFontEnable",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: Right Panel: Plugins Text",
		desc="Font",
		default=False,
	),
	OptionData(
		name="rightPanel.plugins.font",
		v3Name="mainWinRightPanelPluginsFont",
		flags=CUSTOMIZE,
		type="Font | None",
		where="MainWin: Customize: Right Panel: Plugins Text",
		desc="Font",
		default=None,
	),
	OptionData(
		name="rightPanel.plugins.justification",
		v3Name="mainWinRightPanelPluginsJustification",
		flags=CUSTOMIZE,
		type="str",  # left, center, right
		where="MainWin: Customize: Right Panel: Plugins Text",
		desc="Text Alignment",
		default="left",
	),
	OptionData(
		name="rightPanel.resizeOnToggle",
		v3Name="mainWinRightPanelResizeOnToggle",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: Right Panel",
		desc="Resize on show/hide from window controller",
		default=True,
	),
	OptionData(
		name="rightPanel.border",
		v3Name="mainWinRightPanelBorderWidth",
		flags=CUSTOMIZE,
		type="int",
		valid="IntSpin(0, 999, 1)",
		where="MainWin: Customize: Right Panel",
		desc="Border Width",
		default=7,
	),
]
