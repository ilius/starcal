from __future__ import annotations

from scal3.property import Property

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

bgColor = Property(None)
fgColor = Property(None)
baseFontSize: Property[int] = Property(8)
changeHolidayBg: Property[bool] = Property(False)
changeHolidayBgMinDays: Property[int] = Property(1)
changeHolidayBgMaxDays: Property[int] = Property(60)
holidayBgBolor = Property((60, 35, 35))
basicButtonsSize: Property[int] = Property(22)
basicButtonsSpacing: Property[int] = Property(3)
basicButtonsOpacity: Property[float] = Property(1.0)
movementButtonsEnable: Property[bool] = Property(True)
movementButtonsSize: Property[int] = Property(22)
movementButtonsOpacity: Property[float] = Property(1.0)
majorStepMin: Property[int] = Property(50)
minorStepMin: Property[int] = Property(5)
maxLabelWidth: Property[int] = Property(60)
baseTickHeight: Property[float] = Property(1.0)
baseTickWidth: Property[float] = Property(0.5)
maxTickWidth: Property[float] = Property(40.0)
maxTickHeightRatio: Property[float] = Property(0.3)
labelYRatio: Property[float] = Property(1.1)
yearPrettyPower: Property[bool] = Property(True)
truncateTickLabel: Property[bool] = Property(False)
currentTimeMarkerHeightRatio: Property[float] = Property(0.3)
currentTimeMarkerWidth: Property[int] = Property(2)
currentTimeMarkerColor = Property((255, 100, 100))
showWeekStart: Property[bool] = Property(True)
showWeekStartMinDays: Property[int] = Property(1)
showWeekStartMaxDays: Property[int] = Property(60)
weekStartTickColor = Property((0, 200, 0))
boxLineWidth: Property[float] = Property(2)
boxInnerAlpha: Property[float] = Property(0.1)
boxEditBorderWidth: Property[float] = Property(10.0)
boxEditInnerLineWidth: Property[float] = Property(0.5)
boxEditHelperLineWidth: Property[float] = Property(0.3)
boxReverseGravity: Property[bool] = Property(False)
boxSkipPixelLimit: Property[bool] = Property(0.1)
rotateBoxLabel: Property[int] = Property(-1)
enableAnimation: Property[bool] = Property(False)
movingStaticStepKeyboard: Property[int] = Property(20)
movingStaticStepMouse: Property[int] = Property(20)
movingUpdateTime: Property[float] = Property(10)
movingInitialVelocity: Property[float] = Property(0)
movingHandForceMouse: Property[int] = Property(1100)
movingHandForceKeyboard: Property[int] = Property(1100)
movingHandForceKeyboardSmall: Property[int] = Property(850)
movingHandForceButton: Property[int] = Property(1100)
movingFrictionForce: Property[int] = Property(600)
movingMaxVelocity: Property[int] = Property(1200)
movingKeyTimeoutFirst: Property[float] = Property(0.5)
movingKeyTimeout: Property[float] = Property(0.1)
scrollZoomStep: Property[float] = Property(1.2)
keyboardZoomStep: Property[float] = Property(1.2)
keys: Property[dict[str, str]] = Property(
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
	},
)


confParams = {
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
