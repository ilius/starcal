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
from scal3.ui.options._base import LIVE, MAIN_CONF, NEED_RESTART, OptionData

__all__ = ["confOptionsData"]

confOptionsData: list[OptionData] = [
	# ----------------- Preferences: Appearance
	OptionData(
		name="fontCustomEnable",
		v3Name="fontCustomEnable",
		flags=MAIN_CONF,
		type="bool",
		where="Preferences: Appearance",
		desc="Application Font",
		default=False,
	),
	OptionData(
		name="fontCustom",
		v3Name="fontCustom",
		flags=MAIN_CONF,
		type="Font | None ",
		where="Preferences: Appearance",
		desc="Application Font",
		default=None,
	),
	OptionData(
		name="buttonIconEnable",
		v3Name="buttonIconEnable",
		flags=MAIN_CONF | NEED_RESTART,
		type="bool",
		where="Preferences: Appearance",
		desc="Show icons in buttons",
		default=True,
	),
	OptionData(
		name="useSystemIcons",
		v3Name="useSystemIcons",
		flags=MAIN_CONF | NEED_RESTART,
		type="bool",
		where="Preferences: Appearance",
		desc="Use System Icons",
		default=False,
	),
	OptionData(
		name="oldStyleProgressBar",
		v3Name="oldStyleProgressBar",
		flags=MAIN_CONF | NEED_RESTART,
		type="bool",
		where="Preferences: Appearance",
		desc="Old-style Progress Bar",
		default=False,
	),
	# ----------------- Preferences: Appearance: Colors
	OptionData(
		name="bgColor",
		v3Name="bgColor",
		flags=MAIN_CONF | LIVE,
		type="ColorType",
		where="Preferences: Appearance: Colors",
		desc="Background",
		default=RGBA(26, 0, 1, 255),
	),
	OptionData(
		name="borderColor",
		v3Name="borderColor",
		flags=MAIN_CONF,
		type="ColorType",
		where="Preferences: Appearance: Colors",
		desc="Border",
		default=RGBA(123, 40, 0, 255),
	),
	OptionData(
		name="borderTextColor",
		v3Name="borderTextColor",
		flags=MAIN_CONF,
		type="ColorType",
		where="Preferences: Appearance: Colors",
		desc="Border Font",
		default=RGBA(255, 255, 255, 255),
	),
	OptionData(
		name="textColor",
		v3Name="textColor",
		flags=MAIN_CONF,
		type="ColorType",
		where="Preferences: Appearance: Colors",
		desc="Normal Text",
		default=RGBA(255, 255, 255, 255),
	),
	OptionData(
		name="holidayColor",
		v3Name="holidayColor",
		flags=MAIN_CONF,
		type="ColorType",
		where="Preferences: Appearance: Colors",
		desc="Holidays Font",
		default=RGBA(255, 160, 0, 255),
	),
	OptionData(
		name="inactiveColor",
		v3Name="inactiveColor",
		flags=MAIN_CONF,
		type="ColorType",
		where="Preferences: Appearance: Colors",
		desc="Inactive Day Font",
		default=RGBA(255, 255, 255, 115),
	),
	OptionData(
		name="todayCellColor",
		v3Name="todayCellColor",
		flags=MAIN_CONF,
		type="ColorType",
		where="Preferences: Appearance: Colors",
		desc="Today",
		default=RGBA(0, 255, 0, 50),
	),
	OptionData(
		"cursorOutColor",
		v3Name="cursorOutColor",
		flags=MAIN_CONF,
		type="ColorType",
		where="Preferences: Appearance: Colors",
		desc="Cursor",
		default=RGBA(213, 207, 0, 255),
	),
	OptionData(
		name="cursorBgColor",
		v3Name="cursorBgColor",
		flags=MAIN_CONF,
		type="ColorType",
		where="Preferences: Appearance: Colors",
		desc="Cursor BG",
		default=RGBA(41, 41, 41, 255),
	),
]
