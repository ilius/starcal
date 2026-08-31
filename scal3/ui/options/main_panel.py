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
from scal3.ui.options._base import CUSTOMIZE, OptionData

confOptionsData: list[OptionData] = [
	# ------------ progress bars
	OptionData(
		name="monthPBar.calType",
		v3Name="monthPBarCalType",
		flags=CUSTOMIZE,
		type="int",
		where="MainWin: Customize: Main Panel: Month Progress Bar",
		desc="Calendar Type",
		default=-1,
	),
	OptionData(
		name="seasonPBar.southernHemisphere",
		v3Name="seasonPBar_southernHemisphere",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: Main Panel: Season Progress Bar",
		desc="Southern Hemisphere",
		default=False,
	),
	# ------------
	OptionData(
		name="yearMonthBar.border",
		v3Name="labelBoxBorderWidth",
		flags=CUSTOMIZE,
		type="int",
		valid="IntSpin(0, 99, 1)",
		where="MainWin: Customize: Main Panel: Year & Month Bar",
		desc="Border Width",
		default=0,
	),
	OptionData(
		name="yearMonthBar.menuActiveColor",
		v3Name="labelBoxMenuActiveColor",
		flags=CUSTOMIZE,
		type="ColorType",
		where="MainWin: Customize: Main Panel: Year & Month Bar",
		desc="Active menu item color",
		default=RGBA(0, 255, 0, 255),
	),
	OptionData(
		name="yearMonthBar.yearColorEnable",
		v3Name="labelBoxYearColorEnable",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: Main Panel: Year & Month Bar",
		desc="Year Color",
		default=False,
	),
	OptionData(
		name="yearMonthBar.yearColor",
		v3Name="labelBoxYearColor",
		flags=CUSTOMIZE,
		type="ColorType",
		where="MainWin: Customize: Main Panel: Year & Month Bar",
		desc="Year Color",
		default=RGBA(255, 132, 255, 255),
	),
	OptionData(
		name="yearMonthBar.monthColorEnable",
		v3Name="labelBoxMonthColorEnable",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: Main Panel: Year & Month Bar",
		desc="Month Color",
		default=False,
	),
	OptionData(
		name="yearMonthBar.monthColor",
		v3Name="labelBoxMonthColor",
		flags=CUSTOMIZE,
		type="ColorType",
		where="MainWin: Customize: Main Panel: Year & Month Bar",
		desc="Month Color",
		default=RGBA(255, 132, 255, 255),
	),
	OptionData(
		name="yearMonthBar.fontEnable",
		v3Name="labelBoxFontEnable",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: Main Panel: Year & Month Bar",
		desc="Font",
		default=False,
	),
	OptionData(
		name="yearMonthBar.font",
		v3Name="labelBoxFont",
		flags=CUSTOMIZE,
		type="Font | None",
		where="MainWin: Customize: Main Panel: Year & Month Bar",
		desc="Font",
		default=None,
	),
	OptionData(
		name="yearMonthBar.primaryFontEnable",
		v3Name="labelBoxPrimaryFontEnable",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: Main Panel: Year & Month Bar",
		desc="Primary Calendar Font",
		default=False,
	),
	OptionData(
		name="yearMonthBar.primaryFont",
		v3Name="labelBoxPrimaryFont",
		flags=CUSTOMIZE,
		type="Font | None",
		where="MainWin: Customize: Main Panel: Year & Month Bar",
		desc="Primary Calendar Font",
		default=None,
	),
	OptionData(
		name="yearMonthBar.boldYearMonth",
		v3Name="boldYmLabel",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: Main Panel: Year & Month Bar",
		desc="Bold Font",
		default=True,
	),
	# ------------
	OptionData(
		name="weekCal.toolbar.items",
		v3Name="ud__wcalToolbarData",
		flags=CUSTOMIZE,
		type="CustomizableToolBoxDict | None",
		where="MainWin: Customize: Main Panel: Week Calendar: Columns/; Toolbar",
		desc="Toolbar Buttons",
		default=None,
	),
	OptionData(
		name="mainWin.toolbar.items",
		v3Name="ud__mainToolbarData",
		flags=CUSTOMIZE,
		type="CustomizableToolBoxDict | None",
		where="MainWin: Customize: Main Panel: Toolbar",
		desc="Toolbar Buttons",
		default=None,
	),
]
