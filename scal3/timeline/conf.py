from __future__ import annotations

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

bgColor = None
fgColor = None
baseFontSize: int = 8
changeHolidayBg: bool = False
changeHolidayBgMinDays: int = 1
changeHolidayBgMaxDays: int = 60
holidayBgBolor = (60, 35, 35)
basicButtonsSize: int = 22
basicButtonsSpacing: int = 3
basicButtonsOpacity: float = 1.0
movementButtonsEnable: bool = True
movementButtonsSize: int = 22
movementButtonsOpacity: float = 1.0
majorStepMin: int = 50
minorStepMin: int = 5
maxLabelWidth: int = 60
baseTickHeight: float = 1.0
baseTickWidth: float = 0.5
maxTickWidth: float = 40.0
maxTickHeightRatio: float = 0.3
labelYRatio: float = 1.1
yearPrettyPower: bool = True
truncateTickLabel: bool = False
currentTimeMarkerHeightRatio: float = 0.3
currentTimeMarkerWidth: int = 2
currentTimeMarkerColor = (255, 100, 100)
showWeekStart: bool = True
showWeekStartMinDays: int = 1
showWeekStartMaxDays: int = 60
weekStartTickColor = (0, 200, 0)
boxLineWidth: float = 2
boxInnerAlpha: float = 0.1
boxEditBorderWidth: float = 10.0
boxEditInnerLineWidth: float = 0.5
boxEditHelperLineWidth: float = 0.3
boxReverseGravity: bool = False
boxSkipPixelLimit: bool = 0.1
rotateBoxLabel: int = -1
enableAnimation: bool = False
movingStaticStepKeyboard: int = 20
movingStaticStepMouse: int = 20
movingUpdateTime: float = 10
movingInitialVelocity: float = 0
movingHandForceMouse: int = 1100
movingHandForceKeyboard: int = 1100
movingHandForceKeyboardSmall: int = 850
movingHandForceButton: int = 1100
movingFrictionForce: int = 600
movingMaxVelocity: int = 1200
movingKeyTimeoutFirst: float = 0.5
movingKeyTimeout: float = 0.1
scrollZoomStep: float = 1.2
keyboardZoomStep: float = 1.2
keys: dict[str, str] = {
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
