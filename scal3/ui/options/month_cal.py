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

__all__ = ["confOptionsData"]

confOptionsData: list[OptionData] = [
	# ------------ Month Calendar
	OptionData(
		name="monthCal.leftMargin",
		v3Name="mcalLeftMargin",
		flags=CUSTOMIZE,
		type="int",
		valid="IntSpin(0, 999, 1)",
		where="MainWin: Customize: Month Calendar",
		desc="Left Margin",
		default=30,
	),
	OptionData(
		name="monthCal.topMargin",
		v3Name="mcalTopMargin",
		flags=CUSTOMIZE,
		type="int",
		valid="IntSpin(0, 999, 1)",
		where="MainWin: Customize: Month Calendar",
		desc="Top Margin",
		default=30,
	),
	OptionData(
		name="monthCal.typeOptions",
		v3Name="mcalTypeParams",
		flags=CUSTOMIZE,
		type="list[CalTypeOptionsDict]",
		where="MainWin: Customize: Month Calendar",
		desc="Calendar Types Options",
		default=[
			{"pos": (0, -2), "font": None, "color": (220, 220, 220)},
			{"pos": (18, 5), "font": None, "color": (165, 255, 114)},
			{"pos": (-18, 4), "font": None, "color": (0, 200, 205)},
		],
	),
	OptionData(
		name="monthCal.grid",
		v3Name="mcalGrid",
		flags=CUSTOMIZE,
		type="bool",
		where="MainWin: Customize: Month Calendar",
		desc="Grid",
		default=False,
	),
	OptionData(
		name="monthCal.gridColor",
		v3Name="mcalGridColor",
		flags=CUSTOMIZE,
		type="ColorType",
		where="MainWin: Customize: Month Calendar",
		desc="Grid Color",
		default=RGBA(255, 252, 0, 82),
	),
	OptionData(
		name="monthCal.cornerMenuTextColor",
		v3Name="mcalCornerMenuTextColor",
		flags=CUSTOMIZE,
		type="ColorType",
		where="MainWin: Customize: Month Calendar",
		desc="Corner Menu Text Color",
		default=RGBA(255, 255, 255, 255),
	),
	OptionData(
		name="monthCal.cursorLineWidthFactor",
		v3Name="mcalCursorLineWidthFactor",
		flags=CUSTOMIZE,
		type="float",
		valid="FloatSpin(0, 1, 0.1, 2)",
		where="MainWin: Customize: Month Calendar: Cursor",
		desc="Line Width Factor",
		default=0.12,
	),
	OptionData(
		name="monthCal.cursorRoundingFactor",
		v3Name="mcalCursorRoundingFactor",
		flags=CUSTOMIZE,
		type="float",
		valid="FloatSpin(0, 1, 0.1, 2)",
		where="MainWin: Customize: Month Calendar: Cursor",
		desc="Rounding Factor",
		default=0.5,
	),
]
