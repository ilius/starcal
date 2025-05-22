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

from typing import Any, NamedTuple

__all__ = ["NOT_SET", "confParamsData"]


class NOT_SET:
	pass


# TODO: switch to NamedTuple
ColorType = tuple[int, int, int] | tuple[int, int, int, int]


class Param(NamedTuple):
	name: str
	v3Name: str
	type: str
	# flags: int
	# where: str = ""
	# desc: str = ""
	default: Any = NOT_SET


confParamsData = [
	Param(
		name="bgColor",
		type="ColorType",
		v3Name="bgColor",
		default=None,
	),
	Param(
		name="fgColor",
		type="ColorType",
		v3Name="fgColor",
		default=None,
	),
	Param(
		name="",
		type="int",
		v3Name="baseFontSize",
		default=8,
	),
	Param(
		name="",
		type="bool",
		v3Name="changeHolidayBg",
		default=False,
	),
	Param(
		name="",
		type="int",
		v3Name="changeHolidayBgMinDays",
		default=1,
	),
	Param(
		name="",
		type="int",
		v3Name="changeHolidayBgMaxDays",
		default=60,
	),
	Param(
		name="",
		type="ColorType",
		v3Name="holidayBgBolor",
		default=(60, 35, 35),
	),
	# ---------------------
	Param(
		name="",
		type="int",
		v3Name="basicButtonsSize",
		default=22,
	),
	Param(
		name="",
		type="int",
		v3Name="basicButtonsSpacing",
		default=3,
	),
	Param(
		name="",
		type="float",
		v3Name="basicButtonsOpacity",
		default=1.0,
		# 0.0 <= value <= 1.0
	),
	Param(
		name="",
		type="bool",
		v3Name="movementButtonsEnable",
		default=True,
	),
	Param(
		name="",
		type="int",
		v3Name="movementButtonsSize",
		default=22,
	),
	Param(
		name="",
		type="float",
		v3Name="movementButtonsOpacity",
		default=1.0,
		# 0.0 <= value <= 1.0
	),
	# ---------------------
	Param(
		name="",
		type="int",
		v3Name="majorStepMin",
		default=50,  # with label
	),
	Param(
		name="",
		type="int",
		v3Name="minorStepMin",
		default=5,  # with or without label
	),
	Param(
		name="",
		type="int",
		v3Name="maxLabelWidth",
		default=60,  # or the same majorStepMin
	),
	Param(
		name="",
		type="float",
		v3Name="baseTickHeight",
		default=1.0,  # pixel
	),
	Param(
		name="",
		type="float",
		v3Name="baseTickWidth",
		default=0.5,  # pixel
	),
	Param(
		name="",
		type="float",
		v3Name="maxTickWidth",
		default=40.0,  # pixel,
	),
	Param(
		name="",
		type="float",
		v3Name="maxTickHeightRatio",
		default=0.3,  # 0 < value < 1
	),
	Param(
		name="",
		type="float",
		v3Name="labelYRatio",
		default=1.1,
	),
	Param(
		name="",
		type="bool",
		v3Name="yearPrettyPower",
		default=True,
	),
	Param(
		name="",
		type="bool",
		v3Name="truncateTickLabel",
		default=False,
	),
	Param(
		name="",
		type="float",
		v3Name="currentTimeMarkerHeightRatio",
		default=0.3,
	),
	Param(
		name="",
		type="int",
		v3Name="currentTimeMarkerWidth",
		default=2,
	),
	Param(
		name="",
		type="ColorType",
		v3Name="currentTimeMarkerColor",
		default=(255, 100, 100),
	),
	# TODO: change timeline background according to daylight
	# sunLightEnable = False
	# sunLightH = 10
	Param(
		name="",
		type="bool",
		v3Name="showWeekStart",
		default=True,
	),
	Param(
		name="",
		type="int",
		v3Name="showWeekStartMinDays",
		default=1,
	),
	Param(
		name="",
		type="int",
		v3Name="showWeekStartMaxDays",
		default=60,
	),
	Param(
		name="",
		type="ColorType",
		v3Name="weekStartTickColor",
		default=(0, 200, 0),
	),
	# ---------------------
	Param(
		name="",
		type="float",
		v3Name="boxLineWidth",
		default=2,
	),
	Param(
		name="",
		type="float",
		v3Name="boxInnerAlpha",
		default=0.1,  # 0 <= boxInnerAlpha <= 1
	),
	Param(
		name="",
		type="float",
		v3Name="boxEditBorderWidth",
		default=10.0,  # pixel
	),
	Param(
		name="",
		type="float",
		v3Name="boxEditInnerLineWidth",
		default=0.5,  # pixel
	),
	Param(
		name="",
		type="float",
		v3Name="boxEditHelperLineWidth",
		default=0.3,  # pixel
	),
	Param(
		name="",
		type="bool",
		v3Name="boxReverseGravity",
		default=False,
	),
	Param(
		name="",
		type="float",
		v3Name="boxSkipPixelLimit",
		default=0.1,  # pixel
	),
	Param(
		name="",
		type="int",
		v3Name="rotateBoxLabel",
		default=-1,
		# rotateBoxLabel: 0, 1 or -1
		# 0: no rotation
		# 1: 90 deg CCW (if needed)
		# -1: 90 deg CW (if needed)
	),
	# ---------------------
	Param(
		name="",
		type="bool",
		v3Name="enableAnimation",
		default=False,
	),
	# movingStaticStep* is used only when enableAnimation==False
	# number of pixels on each step (keyboard / mouse event)
	Param(
		name="",
		type="int",
		v3Name="movingStaticStepKeyboard",
		default=20,  # pixel
	),
	Param(
		name="",
		type="int",
		v3Name="movingStaticStepMouse",
		default=20,  # pixel
	),
	Param(
		name="",
		type="float",
		v3Name="movingUpdateTime",
		default=10,  # miliseconds
	),
	# movingInitialVelocity: pixel/second, initial speed/velocity when moving time range
	Param(
		name="",
		type="float",
		v3Name="movingInitialVelocity",
		default=0,
	),
	# Force is the same as Acceleration, assuming Mass == 1
	Param(
		name="",
		type="int",
		v3Name="movingHandForceMouse",
		default=1100,  # pixel / second^2
	),
	Param(
		name="",
		type="int",
		v3Name="movingHandForceKeyboard",
		default=1100,  # pixel / second^2
	),
	# movingHandForceKeyboardSmall is when press Shift with Left/Right arrow
	Param(
		name="",
		type="int",
		v3Name="movingHandForceKeyboardSmall",
		default=850,  # pixel / second^2
	),
	Param(
		name="",
		type="int",
		v3Name="movingHandForceButton",
		default=1100,
	),
	# movingHandForce > movingFrictionForce
	Param(
		name="",
		type="int",
		v3Name="movingFrictionForce",
		default=600,  # pixel / second^2
	),
	Param(
		name="",
		type="int",
		v3Name="movingMaxVelocity",
		default=1200,  # pixel / second
	),
	Param(
		name="",
		type="float",
		v3Name="movingKeyTimeoutFirst",
		default=0.5,  # second
	),
	Param(
		name="",
		type="float",
		v3Name="movingKeyTimeout",
		default=0.1,  # seconds
	),
	# ---------------------
	Param(
		name="",
		type="float",
		v3Name="scrollZoomStep",
		default=1.2,  # > 1.0
	),
	Param(
		name="",
		type="float",
		v3Name="keyboardZoomStep",
		default=1.2,  # > 1.0
	),
	# ---------------------
	Param(
		name="",
		type="dict[str, str]",
		v3Name="keys",
		default={
			"space": "moveToNow",
			"home": "moveToNow",
			"right": "moveRight",
			"left": "moveLeft",
			"down": "moveStop",
			"q": "close",
			"escape": "close",
			"plus": "zoomIn",
			"equal": "zoomIn",
			"kp_add": "zoomIn",
			"minus": "zoomOut",
			"kp_subtract": "zoomOut",
		},
	),
]
