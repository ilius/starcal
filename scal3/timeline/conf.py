from __future__ import annotations

import typing

from scal3.color_utils import RGB
from scal3.option import Option, StrDictOption

if typing.TYPE_CHECKING:
	from typing import Any, Final

	from scal3.color_utils import ColorType
__all__ = [
	"baseFontSize",
	"baseTickHeight",
	"baseTickWidth",
	"basicButtonsOpacity",
	"basicButtonsSize",
	"basicButtonsSpacing",
	"bgColor",
	"boxEditBorderWidth",
	"boxEditHelperLineWidth",
	"boxEditInnerLineWidth",
	"boxInnerAlpha",
	"boxLineWidth",
	"boxReverseGravity",
	"boxSkipPixelLimit",
	"changeHolidayBg",
	"changeHolidayBgMaxDays",
	"changeHolidayBgMinDays",
	"confParams",
	"currentTimeMarkerColor",
	"currentTimeMarkerHeightRatio",
	"currentTimeMarkerWidth",
	"enableAnimation",
	"fgColor",
	"holidayBgBolor",
	"keyboardZoomStep",
	"keys",
	"labelYRatio",
	"majorStepMin",
	"maxLabelWidth",
	"maxTickHeightRatio",
	"maxTickWidth",
	"minorStepMin",
	"movementButtonsEnable",
	"movementButtonsOpacity",
	"movementButtonsSize",
	"movingFrictionForce",
	"movingHandForceButton",
	"movingHandForceKeyboard",
	"movingHandForceKeyboardSmall",
	"movingHandForceMouse",
	"movingInitialVelocity",
	"movingKeyTimeout",
	"movingKeyTimeoutFirst",
	"movingMaxVelocity",
	"movingStaticStepKeyboard",
	"movingStaticStepMouse",
	"movingUpdateTime",
	"rotateBoxLabel",
	"scrollZoomStep",
	"showWeekStart",
	"showWeekStartMaxDays",
	"showWeekStartMinDays",
	"truncateTickLabel",
	"weekStartTickColor",
	"yearPrettyPower",
]

bgColor: Final[Option[ColorType | None]] = Option(None)
fgColor: Final[Option[ColorType | None]] = Option(None)
baseFontSize: Final[Option[float]] = Option(8)
changeHolidayBg: Final[Option[bool]] = Option(False)
changeHolidayBgMinDays: Final[Option[int]] = Option(1)
changeHolidayBgMaxDays: Final[Option[int]] = Option(60)
holidayBgBolor: Final[Option[ColorType]] = Option(RGB(red=60, green=35, blue=35))
basicButtonsSize: Final[Option[int]] = Option(22)
basicButtonsSpacing: Final[Option[float]] = Option(3)
basicButtonsOpacity: Final[Option[float]] = Option(1.0)
movementButtonsEnable: Final[Option[bool]] = Option(True)
movementButtonsSize: Final[Option[int]] = Option(22)
movementButtonsOpacity: Final[Option[float]] = Option(1.0)
majorStepMin: Final[Option[float]] = Option(50)
minorStepMin: Final[Option[float]] = Option(5)
maxLabelWidth: Final[Option[float]] = Option(60)
baseTickHeight: Final[Option[float]] = Option(1.0)
baseTickWidth: Final[Option[float]] = Option(0.5)
maxTickWidth: Final[Option[float]] = Option(40.0)
maxTickHeightRatio: Final[Option[float]] = Option(0.3)
labelYRatio: Final[Option[float]] = Option(1.1)
yearPrettyPower: Final[Option[bool]] = Option(True)
truncateTickLabel: Final[Option[bool]] = Option(False)
currentTimeMarkerHeightRatio: Final[Option[float]] = Option(0.3)
currentTimeMarkerWidth: Final[Option[float]] = Option(2)
currentTimeMarkerColor: Final[Option[ColorType]] = Option(
	RGB(red=255, green=100, blue=100)
)
showWeekStart: Final[Option[bool]] = Option(True)
showWeekStartMinDays: Final[Option[int]] = Option(1)
showWeekStartMaxDays: Final[Option[int]] = Option(60)
weekStartTickColor: Final[Option[ColorType]] = Option(RGB(red=0, green=200, blue=0))
boxLineWidth: Final[Option[float]] = Option(2)
boxInnerAlpha: Final[Option[float]] = Option(0.1)
boxEditBorderWidth: Final[Option[float]] = Option(10.0)
boxEditInnerLineWidth: Final[Option[float]] = Option(0.5)
boxEditHelperLineWidth: Final[Option[float]] = Option(0.3)
boxReverseGravity: Final[Option[bool]] = Option(False)
boxSkipPixelLimit: Final[Option[float]] = Option(0.1)
rotateBoxLabel: Final[Option[int]] = Option(-1)
enableAnimation: Final[Option[bool]] = Option(False)
movingStaticStepKeyboard: Final[Option[float]] = Option(20)
movingStaticStepMouse: Final[Option[float]] = Option(20)
movingUpdateTime: Final[Option[int]] = Option(10)
movingInitialVelocity: Final[Option[float]] = Option(0)
movingHandForceMouse: Final[Option[float]] = Option(1100)
movingHandForceKeyboard: Final[Option[float]] = Option(1100)
movingHandForceKeyboardSmall: Final[Option[float]] = Option(850)
movingHandForceButton: Final[Option[float]] = Option(1100)
movingFrictionForce: Final[Option[float]] = Option(600)
movingMaxVelocity: Final[Option[float]] = Option(1200)
movingKeyTimeoutFirst: Final[Option[float]] = Option(0.5)
movingKeyTimeout: Final[Option[float]] = Option(0.1)
scrollZoomStep: Final[Option[float]] = Option(1.2)
keyboardZoomStep: Final[Option[float]] = Option(1.2)
keys: Final[StrDictOption[str]] = StrDictOption(
	{
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
	}
)


confParams: dict[str, Option[Any]] = {
	"baseFontSize": baseFontSize,
	"baseTickHeight": baseTickHeight,
	"baseTickWidth": baseTickWidth,
	"basicButtonsOpacity": basicButtonsOpacity,
	"basicButtonsSize": basicButtonsSize,
	"basicButtonsSpacing": basicButtonsSpacing,
	"bgColor": bgColor,
	"boxEditBorderWidth": boxEditBorderWidth,
	"boxEditHelperLineWidth": boxEditHelperLineWidth,
	"boxEditInnerLineWidth": boxEditInnerLineWidth,
	"boxInnerAlpha": boxInnerAlpha,
	"boxLineWidth": boxLineWidth,
	"boxReverseGravity": boxReverseGravity,
	"boxSkipPixelLimit": boxSkipPixelLimit,
	"changeHolidayBg": changeHolidayBg,
	"changeHolidayBgMaxDays": changeHolidayBgMaxDays,
	"changeHolidayBgMinDays": changeHolidayBgMinDays,
	"currentTimeMarkerColor": currentTimeMarkerColor,
	"currentTimeMarkerHeightRatio": currentTimeMarkerHeightRatio,
	"currentTimeMarkerWidth": currentTimeMarkerWidth,
	"enableAnimation": enableAnimation,
	"fgColor": fgColor,
	"holidayBgBolor": holidayBgBolor,
	"keyboardZoomStep": keyboardZoomStep,
	"keys": keys,
	"labelYRatio": labelYRatio,
	"majorStepMin": majorStepMin,
	"maxLabelWidth": maxLabelWidth,
	"maxTickHeightRatio": maxTickHeightRatio,
	"maxTickWidth": maxTickWidth,
	"minorStepMin": minorStepMin,
	"movementButtonsEnable": movementButtonsEnable,
	"movementButtonsOpacity": movementButtonsOpacity,
	"movementButtonsSize": movementButtonsSize,
	"movingFrictionForce": movingFrictionForce,
	"movingHandForceButton": movingHandForceButton,
	"movingHandForceKeyboard": movingHandForceKeyboard,
	"movingHandForceKeyboardSmall": movingHandForceKeyboardSmall,
	"movingHandForceMouse": movingHandForceMouse,
	"movingInitialVelocity": movingInitialVelocity,
	"movingKeyTimeout": movingKeyTimeout,
	"movingKeyTimeoutFirst": movingKeyTimeoutFirst,
	"movingMaxVelocity": movingMaxVelocity,
	"movingStaticStepKeyboard": movingStaticStepKeyboard,
	"movingStaticStepMouse": movingStaticStepMouse,
	"movingUpdateTime": movingUpdateTime,
	"rotateBoxLabel": rotateBoxLabel,
	"scrollZoomStep": scrollZoomStep,
	"showWeekStart": showWeekStart,
	"showWeekStartMaxDays": showWeekStartMaxDays,
	"showWeekStartMinDays": showWeekStartMinDays,
	"truncateTickLabel": truncateTickLabel,
	"weekStartTickColor": weekStartTickColor,
	"yearPrettyPower": yearPrettyPower,
}
