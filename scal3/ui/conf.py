from __future__ import annotations

import typing

from scal3.color_utils import RGB, RGBA
from scal3.property import Property

if typing.TYPE_CHECKING:
	from typing import Any, Final

	from scal3.color_utils import ColorType
	from scal3.font import Font
	from scal3.ui.pytypes import (
		ButtonGeoDict,
		CalTypeParamsDict,
		CustomizableToolBoxDict,
		DayCalTypeDayParamsDict,
		DayCalTypeWMParamsDict,
		PieGeoDict,
		WeekCalDayNumParamsDict,
	)


__all__ = [
	"bgColor",
	"boldYmLabel",
	"borderColor",
	"borderTextColor",
	"buttonIconEnable",
	"buttonIconSize",
	"cellMenuXOffset",
	"comboBoxIconSize",
	"confParams",
	"confParamsCustomize",
	"confParamsLive",
	"cursorBgColor",
	"cursorOutColor",
	"customizePagePath",
	"dayCalWinParamsLive",
	"dcalDayParams",
	"dcalEventIconSize",
	"dcalEventTotalSizeRatio",
	"dcalMonthParams",
	"dcalNavButtonsEnable",
	"dcalNavButtonsGeo",
	"dcalNavButtonsOpacity",
	"dcalWeekdayAbbreviate",
	"dcalWeekdayLocalize",
	"dcalWeekdayParams",
	"dcalWeekdayUppercase",
	"dcalWidgetButtons",
	"dcalWidgetButtonsEnable",
	"dcalWinBackgroundColor",
	"dcalWinDayParams",
	"dcalWinEventIconSize",
	"dcalWinEventTotalSizeRatio",
	"dcalWinHeight",
	"dcalWinMonthParams",
	"dcalWinSeasonPieAutumnColor",
	"dcalWinSeasonPieEnable",
	"dcalWinSeasonPieGeo",
	"dcalWinSeasonPieSpringColor",
	"dcalWinSeasonPieSummerColor",
	"dcalWinSeasonPieTextColor",
	"dcalWinSeasonPieWinterColor",
	"dcalWinWeekdayAbbreviate",
	"dcalWinWeekdayLocalize",
	"dcalWinWeekdayParams",
	"dcalWinWeekdayUppercase",
	"dcalWinWidgetButtons",
	"dcalWinWidgetButtonsEnable",
	"dcalWinWidgetButtonsOpacity",
	"dcalWinWidgetButtonsSize",
	"dcalWinWidth",
	"dcalWinX",
	"dcalWinY",
	"eventDayViewEnable",
	"eventDayViewEventSep",
	"eventDayViewTimeFormat",
	"eventTreeGroupIconSize",
	"eventTreeIconSize",
	"eventViewMaxHeight",
	"eventWeekViewTimeFormat",
	"fontCustom",
	"fontCustomEnable",
	"holidayColor",
	"imageInputIconSize",
	"inactiveColor",
	"labelBoxBorderWidth",
	"labelBoxFont",
	"labelBoxFontEnable",
	"labelBoxIconSize",
	"labelBoxMenuActiveColor",
	"labelBoxMonthColor",
	"labelBoxMonthColorEnable",
	"labelBoxPrimaryFont",
	"labelBoxPrimaryFontEnable",
	"labelBoxYearColor",
	"labelBoxYearColorEnable",
	"localTzHist",
	"mainWinFooterItems",
	"mainWinItems",
	"mainWinRightPanelBorderWidth",
	"mainWinRightPanelEnable",
	"mainWinRightPanelEventFont",
	"mainWinRightPanelEventFontEnable",
	"mainWinRightPanelEventJustification",
	"mainWinRightPanelEventSep",
	"mainWinRightPanelEventTimeFont",
	"mainWinRightPanelEventTimeFontEnable",
	"mainWinRightPanelPluginsFont",
	"mainWinRightPanelPluginsFontEnable",
	"mainWinRightPanelPluginsJustification",
	"mainWinRightPanelRatio",
	"mainWinRightPanelResizeOnToggle",
	"mainWinRightPanelSwap",
	"mainWinRightPanelWidth",
	"mainWinRightPanelWidthRatio",
	"mainWinRightPanelWidthRatioEnable",
	"maxDayCacheSize",
	"maxWeekCacheSize",
	"mcalCornerMenuTextColor",
	"mcalCursorLineWidthFactor",
	"mcalCursorRoundingFactor",
	"mcalEventIconSizeMax",
	"mcalGrid",
	"mcalGridColor",
	"mcalLeftMargin",
	"mcalTopMargin",
	"mcalTypeParams",
	"menuCheckSize",
	"menuEventCheckIconSize",
	"menuIconEdgePadding",
	"menuIconPadding",
	"menuIconSize",
	"messageDialogIconSize",
	"monthPBarCalType",
	"needRestartList",
	"oldStyleProgressBar",
	"pluginsTextEnable",
	"pluginsTextInsideExpander",
	"pluginsTextIsExpanded",
	"pluginsTextStatusIcon",
	"preferencesPagePath",
	"rightPanelEventIconSize",
	"seasonPBar_southernHemisphere",
	"showDesktopWidget",
	"showDigClockTb",
	"showDigClockTr",
	"showMain",
	"stackIconSize",
	"statusBarDatesColor",
	"statusBarDatesColorEnable",
	"statusBarDatesReverseOrder",
	"statusBarEnable",
	"statusIconFixedSizeEnable",
	"statusIconFixedSizeWH",
	"statusIconFontFamily",
	"statusIconFontFamilyEnable",
	"statusIconHolidayFontColor",
	"statusIconHolidayFontColorEnable",
	"statusIconImage",
	"statusIconImageHoli",
	"statusIconLocalizeNumber",
	"textColor",
	"todayCellColor",
	"toolbarIconSize",
	"treeIconSize",
	"ud__mainToolbarData",
	"ud__wcalToolbarData",
	"useAppIndicator",
	"useSystemIcons",
	"wcalCursorLineWidthFactor",
	"wcalCursorRoundingFactor",
	"wcalEventIconSizeMax",
	"wcalFont_eventsBox",
	"wcalFont_eventsText",
	"wcalFont_pluginsText",
	"wcalFont_weekDays",
	"wcalGrid",
	"wcalGridColor",
	"wcalItems",
	"wcalPadding",
	"wcalTextSizeScale",
	"wcalTypeParams",
	"wcalUpperGradientColor",
	"wcalUpperGradientEnable",
	"wcal_daysOfMonth_dir",
	"wcal_daysOfMonth_expand",
	"wcal_daysOfMonth_width",
	"wcal_eventsCount_expand",
	"wcal_eventsCount_width",
	"wcal_eventsIcon_width",
	"wcal_eventsText_colorize",
	"wcal_eventsText_ongoingColor",
	"wcal_eventsText_ongoingColorEnable",
	"wcal_eventsText_pastColor",
	"wcal_eventsText_pastColorEnable",
	"wcal_eventsText_showDesc",
	"wcal_moonStatus_southernHemisphere",
	"wcal_moonStatus_width",
	"wcal_pluginsText_firstLineOnly",
	"wcal_toolbar_mainMenu_icon",
	"wcal_toolbar_weekNum_negative",
	"wcal_weekDays_expand",
	"wcal_weekDays_width",
	"winControllerBorder",
	"winControllerButtons",
	"winControllerEnable",
	"winControllerIconSize",
	"winControllerPressState",
	"winControllerSpacing",
	"winControllerTheme",
	"winHeight",
	"winKeepAbove",
	"winMaximized",
	"winSticky",
	"winTaskbar",
	"winWidth",
	"winX",
	"winY",
]

showMain: Final[Property[bool]] = Property(True)
winTaskbar: Final[Property[bool]] = Property(False)
useAppIndicator: Final[Property[bool]] = Property(True)
winX: Final[Property[int]] = Property(0)
winY: Final[Property[int]] = Property(0)
winWidth: Final[Property[int]] = Property(480)
winHeight: Final[Property[int]] = Property(300)
winKeepAbove: Final[Property[bool]] = Property(True)
winSticky: Final[Property[bool]] = Property(True)
winMaximized: Final[Property[bool]] = Property(False)
mainWinItems: Final[Property[list[tuple[str, bool]]]] = Property(
	[
		("toolbar", True),
		("labelBox", True),
		("monthCal", False),
		("weekCal", True),
		("dayCal", False),
		("monthPBar", False),
		("seasonPBar", True),
		("yearPBar", False),
	]
)
mainWinFooterItems: Final[Property[list[str]]] = Property(
	["pluginsText", "eventDayView", "statusBar"]
)
pluginsTextEnable: Final[Property[bool]] = Property(False)
pluginsTextInsideExpander: Final[Property[bool]] = Property(True)
pluginsTextIsExpanded: Final[Property[bool]] = Property(True)
eventDayViewEnable: Final[Property[bool]] = Property(False)
eventDayViewEventSep: Final[Property[str]] = Property("\n")
eventViewMaxHeight: Final[Property[int]] = Property(200)
statusBarEnable: Final[Property[bool]] = Property(True)
statusBarDatesReverseOrder: Final[Property[bool]] = Property(False)
statusBarDatesColorEnable: Final[Property[bool]] = Property(False)
statusBarDatesColor: Final[Property[ColorType]] = Property(
	RGBA(red=255, green=132, blue=255, alpha=255)
)
fontCustomEnable: Final[Property[bool]] = Property(False)
fontCustom: Final[Property[Font | None]] = Property(None)
buttonIconEnable: Final[Property[bool]] = Property(True)
useSystemIcons: Final[Property[bool]] = Property(False)
oldStyleProgressBar: Final[Property[bool]] = Property(False)
bgColor: Final[Property[ColorType]] = Property(RGBA(red=26, green=0, blue=1, alpha=255))
borderColor: Final[Property[ColorType]] = Property(
	RGBA(red=123, green=40, blue=0, alpha=255)
)
borderTextColor: Final[Property[ColorType]] = Property(
	RGBA(red=255, green=255, blue=255, alpha=255)
)
textColor: Final[Property[ColorType]] = Property(
	RGBA(red=255, green=255, blue=255, alpha=255)
)
holidayColor: Final[Property[ColorType]] = Property(
	RGBA(red=255, green=160, blue=0, alpha=255)
)
inactiveColor: Final[Property[ColorType]] = Property(
	RGBA(red=255, green=255, blue=255, alpha=115)
)
todayCellColor: Final[Property[ColorType]] = Property(
	RGBA(red=0, green=255, blue=0, alpha=50)
)
cursorOutColor: Final[Property[ColorType]] = Property(
	RGBA(red=213, green=207, blue=0, alpha=255)
)
cursorBgColor: Final[Property[ColorType]] = Property(
	RGBA(red=41, green=41, blue=41, alpha=255)
)
showDigClockTr: Final[Property[bool]] = Property(True)
statusIconImage: Final[Property[str]] = Property("status-icons/dark-green.svg")
statusIconImageHoli: Final[Property[str]] = Property("status-icons/dark-red.svg")
statusIconFontFamilyEnable: Final[Property[bool]] = Property(False)
statusIconFontFamily: Final[Property[str | None]] = Property(None)
statusIconHolidayFontColorEnable: Final[Property[bool]] = Property(False)
statusIconHolidayFontColor: Final[Property[ColorType | None]] = Property(None)
statusIconLocalizeNumber: Final[Property[bool]] = Property(True)
statusIconFixedSizeEnable: Final[Property[bool]] = Property(False)
statusIconFixedSizeWH: Final[Property[tuple[int, int]]] = Property((24, 24))
pluginsTextStatusIcon: Final[Property[bool]] = Property(False)
maxDayCacheSize: Final[Property[int]] = Property(100)
eventDayViewTimeFormat: Final[Property[str]] = Property("HM$")
cellMenuXOffset: Final[Property[int]] = Property(0)
winControllerEnable: Final[Property[bool]] = Property(True)
winControllerTheme: Final[Property[str]] = Property("default")
winControllerButtons: Final[Property[list[tuple[str, bool]]]] = Property(
	[
		("sep", True),
		("rightPanel", True),
		("min", True),
		("max", True),
		("close", True),
		("sep", False),
		("sep", False),
		("sep", False),
	]
)
winControllerIconSize: Final[Property[int]] = Property(24)
winControllerBorder: Final[Property[int]] = Property(0)
winControllerSpacing: Final[Property[int]] = Property(0)
winControllerPressState: Final[Property[bool]] = Property(False)
mainWinRightPanelEnable: Final[Property[bool]] = Property(True)
mainWinRightPanelRatio: Final[Property[float]] = Property(0.5)
mainWinRightPanelSwap: Final[Property[bool]] = Property(False)
mainWinRightPanelWidth: Final[Property[int]] = Property(200)
mainWinRightPanelWidthRatio: Final[Property[float]] = Property(0.25)
mainWinRightPanelWidthRatioEnable: Final[Property[bool]] = Property(True)
mainWinRightPanelEventFontEnable: Final[Property[bool]] = Property(False)
mainWinRightPanelEventFont: Final[Property[Font | None]] = Property(None)
mainWinRightPanelEventTimeFontEnable: Final[Property[bool]] = Property(False)
mainWinRightPanelEventTimeFont: Final[Property[Font | None]] = Property(None)
mainWinRightPanelEventJustification: Final[Property[str]] = Property("left")
mainWinRightPanelEventSep: Final[Property[str]] = Property("\n\n")
mainWinRightPanelPluginsFontEnable: Final[Property[bool]] = Property(False)
mainWinRightPanelPluginsFont: Final[Property[Font | None]] = Property(None)
mainWinRightPanelPluginsJustification: Final[Property[str]] = Property("left")
mainWinRightPanelResizeOnToggle: Final[Property[bool]] = Property(True)
mainWinRightPanelBorderWidth: Final[Property[int]] = Property(7)
mcalLeftMargin: Final[Property[int]] = Property(30)
mcalTopMargin: Final[Property[int]] = Property(30)
mcalTypeParams: Final[Property[list[CalTypeParamsDict]]] = Property(
	[
		{"pos": (0, -2), "font": None, "color": (220, 220, 220)},
		{"pos": (18, 5), "font": None, "color": (165, 255, 114)},
		{"pos": (-18, 4), "font": None, "color": (0, 200, 205)},
	]
)
mcalGrid: Final[Property[bool]] = Property(False)
mcalGridColor: Final[Property[ColorType]] = Property(
	RGBA(red=255, green=252, blue=0, alpha=82)
)
mcalCornerMenuTextColor: Final[Property[ColorType]] = Property(
	RGBA(red=255, green=255, blue=255, alpha=255)
)
mcalCursorLineWidthFactor: Final[Property[float]] = Property(0.12)
mcalCursorRoundingFactor: Final[Property[float]] = Property(0.5)
wcalTextSizeScale: Final[Property[float]] = Property(0.6)
wcalItems: Final[Property[list[tuple[str, bool]]]] = Property(
	[
		("toolbar", True),
		("weekDays", True),
		("pluginsText", True),
		("eventsIcon", True),
		("eventsText", True),
		("daysOfMonth", True),
	]
)
wcalGrid: Final[Property[bool]] = Property(False)
wcalGridColor: Final[Property[ColorType]] = Property(
	RGBA(red=255, green=252, blue=0, alpha=82)
)
wcalUpperGradientEnable: Final[Property[bool]] = Property(False)
wcalUpperGradientColor: Final[Property[ColorType]] = Property(
	RGBA(red=255, green=255, blue=255, alpha=60)
)
wcal_eventsText_pastColorEnable: Final[Property[bool]] = Property(False)
wcal_eventsText_pastColor: Final[Property[ColorType]] = Property(
	RGBA(red=100, green=100, blue=100, alpha=50)
)
wcal_eventsText_ongoingColorEnable: Final[Property[bool]] = Property(False)
wcal_eventsText_ongoingColor: Final[Property[ColorType]] = Property(
	RGBA(red=80, green=255, blue=80, alpha=255)
)
wcal_eventsText_showDesc: Final[Property[bool]] = Property(False)
wcal_eventsText_colorize: Final[Property[bool]] = Property(True)
wcalFont_eventsText: Final[Property[str | None]] = Property(None)
wcal_toolbar_weekNum_negative: Final[Property[bool]] = Property(False)
wcal_toolbar_mainMenu_icon: Final[Property[str]] = Property("starcal.png")
wcal_weekDays_width: Final[Property[int]] = Property(80)
wcal_weekDays_expand: Final[Property[bool]] = Property(False)
wcalFont_weekDays: Final[Property[str | None]] = Property(None)
wcalFont_pluginsText: Final[Property[str | None]] = Property(None)
wcal_pluginsText_firstLineOnly: Final[Property[bool]] = Property(False)
wcal_eventsIcon_width: Final[Property[int]] = Property(50)
wcalTypeParams: Final[Property[list[WeekCalDayNumParamsDict]]] = Property(
	[{"font": None}, {"font": None}, {"font": None}]
)
wcal_daysOfMonth_dir: Final[Property[str]] = Property("ltr")
wcal_daysOfMonth_width: Final[Property[int]] = Property(30)
wcal_daysOfMonth_expand: Final[Property[bool]] = Property(False)
wcal_eventsCount_width: Final[Property[int]] = Property(80)
wcal_eventsCount_expand: Final[Property[bool]] = Property(False)
wcalFont_eventsBox: Final[Property[str | None]] = Property(None)
wcal_moonStatus_width: Final[Property[int]] = Property(48)
wcal_moonStatus_southernHemisphere: Final[Property[bool]] = Property(False)
wcalCursorLineWidthFactor: Final[Property[float]] = Property(0.12)
wcalCursorRoundingFactor: Final[Property[float]] = Property(0.5)
dcalWidgetButtonsEnable: Final[Property[bool]] = Property(False)
dcalDayParams: Final[Property[list[DayCalTypeDayParamsDict]]] = Property(
	[
		{
			"pos": (0, -12),
			"font": None,
			"color": (220, 220, 220),
			"enable": True,
			"xalign": "center",
			"yalign": "center",
			"localize": False,
		},
		{
			"pos": (125, 30),
			"font": None,
			"color": (165, 255, 114),
			"enable": True,
			"xalign": "center",
			"yalign": "center",
			"localize": False,
		},
		{
			"pos": (-125, 24),
			"font": None,
			"color": (0, 200, 205),
			"enable": True,
			"xalign": "center",
			"yalign": "center",
			"localize": False,
		},
	]
)
dcalMonthParams: Final[Property[list[DayCalTypeWMParamsDict]]] = Property(
	[
		{
			"pos": (0, -12),
			"font": None,
			"color": (220, 220, 220),
			"enable": False,
			"xalign": "center",
			"yalign": "center",
			"abbreviate": False,
			"uppercase": False,
		},
		{
			"pos": (125, 30),
			"font": None,
			"color": (165, 255, 114),
			"enable": False,
			"xalign": "center",
			"yalign": "center",
			"abbreviate": False,
			"uppercase": False,
		},
		{
			"pos": (-125, 24),
			"font": None,
			"color": (0, 200, 205),
			"enable": False,
			"xalign": "center",
			"yalign": "center",
			"abbreviate": False,
			"uppercase": False,
		},
	]
)
dcalWeekdayParams: Final[Property[DayCalTypeWMParamsDict]] = Property(
	{
		"pos": (20, 10),
		"font": None,
		"color": (0, 200, 205),
		"enable": False,
		"xalign": "right",
		"yalign": "buttom",
		"abbreviate": False,
		"uppercase": False,
	}
)
dcalNavButtonsEnable: Final[Property[bool]] = Property(True)
dcalNavButtonsGeo: Final[Property[ButtonGeoDict]] = Property(
	{
		"auto_rtl": True,
		"size": 64,
		"spacing": 10,
		"pos": (0, 20),
		"xalign": "center",
		"yalign": "buttom",
	}
)
dcalNavButtonsOpacity: Final[Property[float]] = Property(0.7)
dcalWeekdayLocalize: Final[Property[bool]] = Property(True)
dcalWeekdayAbbreviate: Final[Property[bool]] = Property(False)
dcalWeekdayUppercase: Final[Property[bool]] = Property(False)
dcalEventIconSize: Final[Property[int]] = Property(20)
dcalEventTotalSizeRatio: Final[Property[float]] = Property(0.3)
showDesktopWidget: Final[Property[bool]] = Property(False)
dcalWinX: Final[Property[int]] = Property(0)
dcalWinY: Final[Property[int]] = Property(0)
dcalWinWidth: Final[Property[int]] = Property(180)
dcalWinHeight: Final[Property[int]] = Property(180)
dcalWinBackgroundColor: Final[Property[ColorType]] = Property(
	RGB(red=0, green=10, blue=0)
)
dcalWinWidgetButtonsEnable: Final[Property[bool]] = Property(True)
dcalWinWidgetButtonsSize: Final[Property[int]] = Property(16)
dcalWinWidgetButtonsOpacity: Final[Property[float]] = Property(1.0)
dcalWinWeekdayLocalize: Final[Property[bool]] = Property(True)
dcalWinWeekdayAbbreviate: Final[Property[bool]] = Property(False)
dcalWinWeekdayUppercase: Final[Property[bool]] = Property(False)
dcalWinDayParams: Final[Property[list[DayCalTypeDayParamsDict]]] = Property(
	[
		{
			"pos": (0, 5),
			"font": None,
			"color": (220, 220, 220),
			"enable": True,
			"xalign": "left",
			"yalign": "center",
			"localize": False,
		},
		{
			"pos": (5, 0),
			"font": None,
			"color": (165, 255, 114),
			"enable": True,
			"xalign": "right",
			"yalign": "top",
			"localize": False,
		},
		{
			"pos": (0, 0),
			"font": None,
			"color": (0, 200, 205),
			"enable": True,
			"xalign": "right",
			"yalign": "buttom",
			"localize": False,
		},
	]
)
dcalWinMonthParams: Final[Property[list[DayCalTypeWMParamsDict]]] = Property(
	[
		{
			"pos": (0, 5),
			"font": None,
			"color": (220, 220, 220),
			"enable": False,
			"xalign": "left",
			"yalign": "center",
			"abbreviate": False,
			"uppercase": False,
		},
		{
			"pos": (5, 0),
			"font": None,
			"enable": False,
			"color": (165, 255, 114),
			"xalign": "right",
			"yalign": "top",
			"abbreviate": False,
			"uppercase": False,
		},
		{
			"pos": (0, 0),
			"font": None,
			"color": (0, 200, 205),
			"enable": False,
			"xalign": "right",
			"yalign": "buttom",
			"abbreviate": False,
			"uppercase": False,
		},
	]
)
dcalWinWeekdayParams: Final[Property[DayCalTypeWMParamsDict]] = Property(
	{
		"pos": (20, 10),
		"font": None,
		"color": (0, 200, 205),
		"enable": False,
		"xalign": "right",
		"yalign": "buttom",
		"abbreviate": False,
		"uppercase": False,
	}
)
dcalWinEventIconSize: Final[Property[int]] = Property(20)
dcalWinEventTotalSizeRatio: Final[Property[float]] = Property(0.3)
dcalWinSeasonPieEnable: Final[Property[bool]] = Property(False)
dcalWinSeasonPieGeo: Final[Property[PieGeoDict]] = Property(
	{
		"size": 64,
		"thickness": 0.3,
		"pos": (0, 0),
		"xalign": "right",
		"yalign": "top",
		"startAngle": 270,
	}
)
dcalWinSeasonPieSpringColor: Final[Property[ColorType]] = Property(
	RGBA(red=167, green=252, blue=1, alpha=180)
)
dcalWinSeasonPieSummerColor: Final[Property[ColorType]] = Property(
	RGBA(red=255, green=254, blue=0, alpha=180)
)
dcalWinSeasonPieAutumnColor: Final[Property[ColorType]] = Property(
	RGBA(red=255, green=127, blue=0, alpha=180)
)
dcalWinSeasonPieWinterColor: Final[Property[ColorType]] = Property(
	RGBA(red=1, green=191, blue=255, alpha=180)
)
dcalWinSeasonPieTextColor: Final[Property[ColorType]] = Property(
	RGBA(red=255, green=255, blue=255, alpha=180)
)
monthPBarCalType: Final[Property[int]] = Property(-1)
seasonPBar_southernHemisphere: Final[Property[bool]] = Property(False)
labelBoxBorderWidth: Final[Property[int]] = Property(0)
labelBoxMenuActiveColor: Final[Property[ColorType]] = Property(
	RGBA(red=0, green=255, blue=0, alpha=255)
)
labelBoxYearColorEnable: Final[Property[bool]] = Property(False)
labelBoxYearColor: Final[Property[ColorType]] = Property(
	RGBA(red=255, green=132, blue=255, alpha=255)
)
labelBoxMonthColorEnable: Final[Property[bool]] = Property(False)
labelBoxMonthColor: Final[Property[ColorType]] = Property(
	RGBA(red=255, green=132, blue=255, alpha=255)
)
labelBoxFontEnable: Final[Property[bool]] = Property(False)
labelBoxFont: Final[Property[Font | None]] = Property(None)
labelBoxPrimaryFontEnable: Final[Property[bool]] = Property(False)
labelBoxPrimaryFont: Final[Property[Font | None]] = Property(None)
boldYmLabel: Final[Property[bool]] = Property(True)
ud__wcalToolbarData: Final[Property[CustomizableToolBoxDict | None]] = Property(None)
ud__mainToolbarData: Final[Property[CustomizableToolBoxDict | None]] = Property(None)
preferencesPagePath: Final[Property[str]] = Property("")
customizePagePath: Final[Property[str]] = Property("")
localTzHist: Final[Property[list[str]]] = Property([])
showDigClockTb: Final[Property[bool]] = Property(True)
menuIconPadding: Final[Property[int]] = Property(7)
eventTreeGroupIconSize: Final[Property[int]] = Property(24)
treeIconSize: Final[Property[int]] = Property(22)
labelBoxIconSize: Final[Property[int]] = Property(20)
stackIconSize: Final[Property[int]] = Property(22)
dcalWidgetButtons: Final[Property[list[dict[str, Any]]]] = Property(
	[
		{
			"imageName": "transform-move.svg",
			"onClick": "startMove",
			"pos": (0, 0),
			"xalign": "left",
			"yalign": "top",
			"autoDir": False,
		},
		{
			"imageName": "resize-small.svg",
			"onClick": "startResize",
			"pos": (1, 1),
			"xalign": "right",
			"yalign": "buttom",
			"autoDir": False,
		},
	]
)
dcalWinWidgetButtons: Final[Property[list[dict[str, Any]]]] = Property(
	[
		{
			"imageName": "transform-move.svg",
			"onClick": "startMove",
			"pos": (0, 0),
			"xalign": "left",
			"yalign": "top",
			"autoDir": False,
		},
		{
			"imageName": "resize-small.svg",
			"onClick": "startResize",
			"pos": (1, 1),
			"xalign": "right",
			"yalign": "buttom",
			"autoDir": False,
		},
		{
			"imageName": "document-edit.svg",
			"onClick": "openCustomize",
			"pos": (0, 1),
			"xalign": "left",
			"yalign": "buttom",
			"autoDir": False,
		},
	]
)
menuIconEdgePadding: Final[Property[int]] = Property(3)
rightPanelEventIconSize: Final[Property[int]] = Property(20)
eventTreeIconSize: Final[Property[int]] = Property(22)
menuEventCheckIconSize: Final[Property[int]] = Property(20)
toolbarIconSize: Final[Property[int]] = Property(24)
mcalEventIconSizeMax: Final[Property[int]] = Property(26)
messageDialogIconSize: Final[Property[int]] = Property(48)
menuCheckSize: Final[Property[int]] = Property(22)
menuIconSize: Final[Property[int]] = Property(18)
comboBoxIconSize: Final[Property[int]] = Property(20)
imageInputIconSize: Final[Property[int]] = Property(32)
maxWeekCacheSize: Final[Property[int]] = Property(12)
wcalPadding: Final[Property[int]] = Property(10)
buttonIconSize: Final[Property[int]] = Property(20)
wcalEventIconSizeMax: Final[Property[int]] = Property(26)
eventWeekViewTimeFormat: Final[Property[str]] = Property("HM$")


confParams: dict[str, Property] = {
	"showMain": showMain,
	"winTaskbar": winTaskbar,
	"useAppIndicator": useAppIndicator,
	"fontCustomEnable": fontCustomEnable,
	"fontCustom": fontCustom,
	"buttonIconEnable": buttonIconEnable,
	"useSystemIcons": useSystemIcons,
	"oldStyleProgressBar": oldStyleProgressBar,
	"bgColor": bgColor,
	"borderColor": borderColor,
	"borderTextColor": borderTextColor,
	"textColor": textColor,
	"holidayColor": holidayColor,
	"inactiveColor": inactiveColor,
	"todayCellColor": todayCellColor,
	"cursorOutColor": cursorOutColor,
	"cursorBgColor": cursorBgColor,
	"showDigClockTr": showDigClockTr,
	"statusIconImage": statusIconImage,
	"statusIconImageHoli": statusIconImageHoli,
	"statusIconFontFamilyEnable": statusIconFontFamilyEnable,
	"statusIconFontFamily": statusIconFontFamily,
	"statusIconHolidayFontColorEnable": statusIconHolidayFontColorEnable,
	"statusIconHolidayFontColor": statusIconHolidayFontColor,
	"statusIconLocalizeNumber": statusIconLocalizeNumber,
	"statusIconFixedSizeEnable": statusIconFixedSizeEnable,
	"statusIconFixedSizeWH": statusIconFixedSizeWH,
	"pluginsTextStatusIcon": pluginsTextStatusIcon,
	"maxDayCacheSize": maxDayCacheSize,
	"eventDayViewTimeFormat": eventDayViewTimeFormat,
	"cellMenuXOffset": cellMenuXOffset,
	"showDesktopWidget": showDesktopWidget,
	"preferencesPagePath": preferencesPagePath,
	"localTzHist": localTzHist,
}
confParamsLive: dict[str, Property] = {
	"winX": winX,
	"winY": winY,
	"winWidth": winWidth,
	"winHeight": winHeight,
	"winKeepAbove": winKeepAbove,
	"winSticky": winSticky,
	"winMaximized": winMaximized,
	"pluginsTextIsExpanded": pluginsTextIsExpanded,
	"bgColor": bgColor,
	"mainWinRightPanelRatio": mainWinRightPanelRatio,
	"wcal_toolbar_weekNum_negative": wcal_toolbar_weekNum_negative,
}
confParamsCustomize: dict[str, Property] = {
	"mainWinItems": mainWinItems,
	"mainWinFooterItems": mainWinFooterItems,
	"pluginsTextEnable": pluginsTextEnable,
	"pluginsTextInsideExpander": pluginsTextInsideExpander,
	"eventDayViewEnable": eventDayViewEnable,
	"eventDayViewEventSep": eventDayViewEventSep,
	"eventViewMaxHeight": eventViewMaxHeight,
	"statusBarEnable": statusBarEnable,
	"statusBarDatesReverseOrder": statusBarDatesReverseOrder,
	"statusBarDatesColorEnable": statusBarDatesColorEnable,
	"statusBarDatesColor": statusBarDatesColor,
	"winControllerEnable": winControllerEnable,
	"winControllerTheme": winControllerTheme,
	"winControllerButtons": winControllerButtons,
	"winControllerIconSize": winControllerIconSize,
	"winControllerBorder": winControllerBorder,
	"winControllerSpacing": winControllerSpacing,
	"winControllerPressState": winControllerPressState,
	"mainWinRightPanelEnable": mainWinRightPanelEnable,
	"mainWinRightPanelSwap": mainWinRightPanelSwap,
	"mainWinRightPanelWidth": mainWinRightPanelWidth,
	"mainWinRightPanelWidthRatio": mainWinRightPanelWidthRatio,
	"mainWinRightPanelWidthRatioEnable": mainWinRightPanelWidthRatioEnable,
	"mainWinRightPanelEventFontEnable": mainWinRightPanelEventFontEnable,
	"mainWinRightPanelEventFont": mainWinRightPanelEventFont,
	"mainWinRightPanelEventTimeFontEnable": mainWinRightPanelEventTimeFontEnable,
	"mainWinRightPanelEventTimeFont": mainWinRightPanelEventTimeFont,
	"mainWinRightPanelEventJustification": mainWinRightPanelEventJustification,
	"mainWinRightPanelEventSep": mainWinRightPanelEventSep,
	"mainWinRightPanelPluginsFontEnable": mainWinRightPanelPluginsFontEnable,
	"mainWinRightPanelPluginsFont": mainWinRightPanelPluginsFont,
	"mainWinRightPanelPluginsJustification": mainWinRightPanelPluginsJustification,
	"mainWinRightPanelResizeOnToggle": mainWinRightPanelResizeOnToggle,
	"mainWinRightPanelBorderWidth": mainWinRightPanelBorderWidth,
	"mcalLeftMargin": mcalLeftMargin,
	"mcalTopMargin": mcalTopMargin,
	"mcalTypeParams": mcalTypeParams,
	"mcalGrid": mcalGrid,
	"mcalGridColor": mcalGridColor,
	"mcalCornerMenuTextColor": mcalCornerMenuTextColor,
	"mcalCursorLineWidthFactor": mcalCursorLineWidthFactor,
	"mcalCursorRoundingFactor": mcalCursorRoundingFactor,
	"wcalTextSizeScale": wcalTextSizeScale,
	"wcalItems": wcalItems,
	"wcalGrid": wcalGrid,
	"wcalGridColor": wcalGridColor,
	"wcalUpperGradientEnable": wcalUpperGradientEnable,
	"wcalUpperGradientColor": wcalUpperGradientColor,
	"wcal_eventsText_pastColorEnable": wcal_eventsText_pastColorEnable,
	"wcal_eventsText_pastColor": wcal_eventsText_pastColor,
	"wcal_eventsText_ongoingColorEnable": wcal_eventsText_ongoingColorEnable,
	"wcal_eventsText_ongoingColor": wcal_eventsText_ongoingColor,
	"wcal_eventsText_showDesc": wcal_eventsText_showDesc,
	"wcal_eventsText_colorize": wcal_eventsText_colorize,
	"wcalFont_eventsText": wcalFont_eventsText,
	"wcal_toolbar_mainMenu_icon": wcal_toolbar_mainMenu_icon,
	"wcal_weekDays_width": wcal_weekDays_width,
	"wcal_weekDays_expand": wcal_weekDays_expand,
	"wcalFont_weekDays": wcalFont_weekDays,
	"wcalFont_pluginsText": wcalFont_pluginsText,
	"wcal_pluginsText_firstLineOnly": wcal_pluginsText_firstLineOnly,
	"wcal_eventsIcon_width": wcal_eventsIcon_width,
	"wcalTypeParams": wcalTypeParams,
	"wcal_daysOfMonth_dir": wcal_daysOfMonth_dir,
	"wcal_daysOfMonth_width": wcal_daysOfMonth_width,
	"wcal_daysOfMonth_expand": wcal_daysOfMonth_expand,
	"wcal_eventsCount_width": wcal_eventsCount_width,
	"wcal_eventsCount_expand": wcal_eventsCount_expand,
	"wcalFont_eventsBox": wcalFont_eventsBox,
	"wcal_moonStatus_width": wcal_moonStatus_width,
	"wcal_moonStatus_southernHemisphere": wcal_moonStatus_southernHemisphere,
	"wcalCursorLineWidthFactor": wcalCursorLineWidthFactor,
	"wcalCursorRoundingFactor": wcalCursorRoundingFactor,
	"dcalWidgetButtonsEnable": dcalWidgetButtonsEnable,
	"dcalDayParams": dcalDayParams,
	"dcalMonthParams": dcalMonthParams,
	"dcalWeekdayParams": dcalWeekdayParams,
	"dcalNavButtonsEnable": dcalNavButtonsEnable,
	"dcalNavButtonsGeo": dcalNavButtonsGeo,
	"dcalNavButtonsOpacity": dcalNavButtonsOpacity,
	"dcalWeekdayLocalize": dcalWeekdayLocalize,
	"dcalWeekdayAbbreviate": dcalWeekdayAbbreviate,
	"dcalWeekdayUppercase": dcalWeekdayUppercase,
	"dcalEventIconSize": dcalEventIconSize,
	"dcalEventTotalSizeRatio": dcalEventTotalSizeRatio,
	"dcalWinBackgroundColor": dcalWinBackgroundColor,
	"dcalWinWidgetButtonsEnable": dcalWinWidgetButtonsEnable,
	"dcalWinWidgetButtonsSize": dcalWinWidgetButtonsSize,
	"dcalWinWidgetButtonsOpacity": dcalWinWidgetButtonsOpacity,
	"dcalWinWeekdayLocalize": dcalWinWeekdayLocalize,
	"dcalWinWeekdayAbbreviate": dcalWinWeekdayAbbreviate,
	"dcalWinWeekdayUppercase": dcalWinWeekdayUppercase,
	"dcalWinDayParams": dcalWinDayParams,
	"dcalWinMonthParams": dcalWinMonthParams,
	"dcalWinWeekdayParams": dcalWinWeekdayParams,
	"dcalWinEventIconSize": dcalWinEventIconSize,
	"dcalWinEventTotalSizeRatio": dcalWinEventTotalSizeRatio,
	"dcalWinSeasonPieEnable": dcalWinSeasonPieEnable,
	"dcalWinSeasonPieGeo": dcalWinSeasonPieGeo,
	"dcalWinSeasonPieSpringColor": dcalWinSeasonPieSpringColor,
	"dcalWinSeasonPieSummerColor": dcalWinSeasonPieSummerColor,
	"dcalWinSeasonPieAutumnColor": dcalWinSeasonPieAutumnColor,
	"dcalWinSeasonPieWinterColor": dcalWinSeasonPieWinterColor,
	"dcalWinSeasonPieTextColor": dcalWinSeasonPieTextColor,
	"monthPBarCalType": monthPBarCalType,
	"seasonPBar_southernHemisphere": seasonPBar_southernHemisphere,
	"labelBoxBorderWidth": labelBoxBorderWidth,
	"labelBoxMenuActiveColor": labelBoxMenuActiveColor,
	"labelBoxYearColorEnable": labelBoxYearColorEnable,
	"labelBoxYearColor": labelBoxYearColor,
	"labelBoxMonthColorEnable": labelBoxMonthColorEnable,
	"labelBoxMonthColor": labelBoxMonthColor,
	"labelBoxFontEnable": labelBoxFontEnable,
	"labelBoxFont": labelBoxFont,
	"labelBoxPrimaryFontEnable": labelBoxPrimaryFontEnable,
	"labelBoxPrimaryFont": labelBoxPrimaryFont,
	"boldYmLabel": boldYmLabel,
	"ud__wcalToolbarData": ud__wcalToolbarData,
	"ud__mainToolbarData": ud__mainToolbarData,
	"customizePagePath": customizePagePath,
}
dayCalWinParamsLive: dict[str, Property] = {
	"dcalWinX": dcalWinX,
	"dcalWinY": dcalWinY,
	"dcalWinWidth": dcalWinWidth,
	"dcalWinHeight": dcalWinHeight,
}

needRestartList = [
	winTaskbar,
	useAppIndicator,
	buttonIconEnable,
	useSystemIcons,
	oldStyleProgressBar,
]
