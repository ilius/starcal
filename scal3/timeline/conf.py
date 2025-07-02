from __future__ import annotations

import typing

from scal3.color_utils import RGB
from scal3.property import Property

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

bgColor: Final[Property[ColorType | None]] = Property(None)
fgColor: Final[Property[ColorType | None]] = Property(None)
baseFontSize: Final[Property[float]] = Property(8)
changeHolidayBg: Final[Property[bool]] = Property(False)
changeHolidayBgMinDays: Final[Property[int]] = Property(1)
changeHolidayBgMaxDays: Final[Property[int]] = Property(60)
holidayBgBolor: Final[Property[ColorType]] = Property(RGB(red=60, green=35, blue=35))
basicButtonsSize: Final[Property[int]] = Property(22)
basicButtonsSpacing: Final[Property[float]] = Property(3)
basicButtonsOpacity: Final[Property[float]] = Property(1.0)
movementButtonsEnable: Final[Property[bool]] = Property(True)
movementButtonsSize: Final[Property[int]] = Property(22)
movementButtonsOpacity: Final[Property[float]] = Property(1.0)
majorStepMin: Final[Property[float]] = Property(50)
minorStepMin: Final[Property[float]] = Property(5)
maxLabelWidth: Final[Property[float]] = Property(60)
baseTickHeight: Final[Property[float]] = Property(1.0)
baseTickWidth: Final[Property[float]] = Property(0.5)
maxTickWidth: Final[Property[float]] = Property(40.0)
maxTickHeightRatio: Final[Property[float]] = Property(0.3)
labelYRatio: Final[Property[float]] = Property(1.1)
yearPrettyPower: Final[Property[bool]] = Property(True)
truncateTickLabel: Final[Property[bool]] = Property(False)
currentTimeMarkerHeightRatio: Final[Property[float]] = Property(0.3)
currentTimeMarkerWidth: Final[Property[float]] = Property(2)
currentTimeMarkerColor: Final[Property[ColorType]] = Property(
	RGB(red=255, green=100, blue=100)
)
showWeekStart: Final[Property[bool]] = Property(True)
showWeekStartMinDays: Final[Property[int]] = Property(1)
showWeekStartMaxDays: Final[Property[int]] = Property(60)
weekStartTickColor: Final[Property[ColorType]] = Property(RGB(red=0, green=200, blue=0))
boxLineWidth: Final[Property[float]] = Property(2)
boxInnerAlpha: Final[Property[float]] = Property(0.1)
boxEditBorderWidth: Final[Property[float]] = Property(10.0)
boxEditInnerLineWidth: Final[Property[float]] = Property(0.5)
boxEditHelperLineWidth: Final[Property[float]] = Property(0.3)
boxReverseGravity: Final[Property[bool]] = Property(False)
boxSkipPixelLimit: Final[Property[float]] = Property(0.1)
rotateBoxLabel: Final[Property[int]] = Property(-1)
enableAnimation: Final[Property[bool]] = Property(False)
movingStaticStepKeyboard: Final[Property[float]] = Property(20)
movingStaticStepMouse: Final[Property[float]] = Property(20)
movingUpdateTime: Final[Property[int]] = Property(10)
movingInitialVelocity: Final[Property[float]] = Property(0)
movingHandForceMouse: Final[Property[float]] = Property(1100)
movingHandForceKeyboard: Final[Property[float]] = Property(1100)
movingHandForceKeyboardSmall: Final[Property[float]] = Property(850)
movingHandForceButton: Final[Property[float]] = Property(1100)
movingFrictionForce: Final[Property[float]] = Property(600)
movingMaxVelocity: Final[Property[float]] = Property(1200)
movingKeyTimeoutFirst: Final[Property[float]] = Property(0.5)
movingKeyTimeout: Final[Property[float]] = Property(0.1)
scrollZoomStep: Final[Property[float]] = Property(1.2)
keyboardZoomStep: Final[Property[float]] = Property(1.2)
keys: Final[Property[dict[str, str]]] = Property(
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


confParams: dict[str, Property[Any]] = {
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
