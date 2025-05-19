from __future__ import annotations

import typing

from scal3.property import Property

if typing.TYPE_CHECKING:
	from typing import Any

	from scal3.color_utils import ColorType
	from scal3.font import Font
	from scal3.ui.pytypes import (
		ButtonGeoDict,
		CalTypeParamsDict,
		DayCalNameTypeParamsDict,
		DayCalTypeParamsDict,
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

showMain: Property[bool] = Property(True)
winTaskbar: Property[bool] = Property(False)
useAppIndicator: Property[bool] = Property(True)
winX: Property[int] = Property(0)
winY: Property[int] = Property(0)
winWidth: Property[int] = Property(480)
winHeight: Property[int] = Property(300)
winKeepAbove: Property[bool] = Property(True)
winSticky: Property[bool] = Property(True)
winMaximized: Property[bool] = Property(False)
mainWinItems: Property[list[tuple[str, bool]]] = Property(
	[
		("toolbar", True),
		("labelBox", True),
		("monthCal", False),
		("weekCal", True),
		("dayCal", False),
		("monthPBar", False),
		("seasonPBar", True),
		("yearPBar", False),
	],
)
mainWinFooterItems: Property[list[str]] = Property(
	["pluginsText", "eventDayView", "statusBar"],
)
pluginsTextEnable: Property[bool] = Property(False)
pluginsTextInsideExpander: Property[bool] = Property(True)
pluginsTextIsExpanded: Property[bool] = Property(True)
eventDayViewEnable: Property[bool] = Property(False)
eventDayViewEventSep: Property[str] = Property("\n")
eventViewMaxHeight: Property[int] = Property(200)
statusBarEnable: Property[bool] = Property(True)
statusBarDatesReverseOrder: Property[bool] = Property(False)
statusBarDatesColorEnable: Property[bool] = Property(False)
statusBarDatesColor: Property[ColorType] = Property((255, 132, 255, 255))
fontCustomEnable: Property[bool] = Property(False)
fontCustom: Property[Font | None] = Property(None)
buttonIconEnable: Property[bool] = Property(True)
useSystemIcons: Property[bool] = Property(False)
oldStyleProgressBar: Property[bool] = Property(False)
bgColor: Property[ColorType] = Property((26, 0, 1, 255))
borderColor: Property[ColorType] = Property((123, 40, 0, 255))
borderTextColor: Property[ColorType] = Property((255, 255, 255, 255))
textColor: Property[ColorType] = Property((255, 255, 255, 255))
holidayColor: Property[ColorType] = Property((255, 160, 0, 255))
inactiveColor: Property[ColorType] = Property((255, 255, 255, 115))
todayCellColor: Property[ColorType] = Property((0, 255, 0, 50))
cursorOutColor: Property[ColorType] = Property((213, 207, 0, 255))
cursorBgColor: Property[ColorType] = Property((41, 41, 41, 255))
showDigClockTr: Property[bool] = Property(True)
statusIconImage: Property[str] = Property("status-icons/dark-green.svg")
statusIconImageHoli: Property[str] = Property("status-icons/dark-red.svg")
statusIconFontFamilyEnable: Property[bool] = Property(False)
statusIconFontFamily: Property[str | None] = Property(None)
statusIconHolidayFontColorEnable: Property[bool] = Property(False)
statusIconHolidayFontColor: Property[ColorType | None] = Property(None)
statusIconLocalizeNumber: Property[bool] = Property(True)
statusIconFixedSizeEnable: Property[bool] = Property(False)
statusIconFixedSizeWH: Property[tuple[int, int]] = Property((24, 24))
pluginsTextStatusIcon: Property[bool] = Property(False)
maxDayCacheSize: Property[int] = Property(100)
eventDayViewTimeFormat: Property[str] = Property("HM$")
cellMenuXOffset: Property[int] = Property(0)
winControllerEnable: Property[bool] = Property(True)
winControllerTheme: Property[str] = Property("default")
winControllerButtons: Property[list[tuple[str, bool]]] = Property(
	[
		("sep", True),
		("rightPanel", True),
		("min", True),
		("max", True),
		("close", True),
		("sep", False),
		("sep", False),
		("sep", False),
	],
)
winControllerIconSize: Property[float] = Property(24)
winControllerBorder: Property[int] = Property(0)
winControllerSpacing: Property[int] = Property(0)
winControllerPressState: Property[bool] = Property(False)
mainWinRightPanelEnable: Property[bool] = Property(True)
mainWinRightPanelRatio: Property[float] = Property(0.5)
mainWinRightPanelSwap: Property[bool] = Property(False)
mainWinRightPanelWidth: Property[int] = Property(200)
mainWinRightPanelWidthRatio: Property[float] = Property(0.25)
mainWinRightPanelWidthRatioEnable: Property[bool] = Property(True)
mainWinRightPanelEventFontEnable: Property[bool] = Property(False)
mainWinRightPanelEventFont: Property[Font | None] = Property(None)
mainWinRightPanelEventTimeFontEnable: Property[bool] = Property(False)
mainWinRightPanelEventTimeFont: Property[Font | None] = Property(None)
mainWinRightPanelEventJustification: Property[str] = Property("left")
mainWinRightPanelEventSep: Property[str] = Property("\n\n")
mainWinRightPanelPluginsFontEnable: Property[bool] = Property(False)
mainWinRightPanelPluginsFont: Property[Font | None] = Property(None)
mainWinRightPanelPluginsJustification: Property[str] = Property("left")
mainWinRightPanelResizeOnToggle: Property[bool] = Property(True)
mainWinRightPanelBorderWidth: Property[int] = Property(7)
mcalLeftMargin: Property[float] = Property(30)
mcalTopMargin: Property[float] = Property(30)
mcalTypeParams: Property[list[CalTypeParamsDict]] = Property(
	[
		{"pos": (0, -2), "font": None, "color": (220, 220, 220)},
		{"pos": (18, 5), "font": None, "color": (165, 255, 114)},
		{"pos": (-18, 4), "font": None, "color": (0, 200, 205)},
	],
)
mcalGrid: Property[bool] = Property(False)
mcalGridColor: Property[ColorType] = Property((255, 252, 0, 82))
mcalCornerMenuTextColor: Property[ColorType] = Property((255, 255, 255, 255))
mcalCursorLineWidthFactor: Property[float] = Property(0.12)
mcalCursorRoundingFactor: Property[float] = Property(0.5)
wcalTextSizeScale: Property[float] = Property(0.6)
wcalItems: Property[list[tuple[str, bool]]] = Property(
	[
		("toolbar", True),
		("weekDays", True),
		("pluginsText", True),
		("eventsIcon", True),
		("eventsText", True),
		("daysOfMonth", True),
	],
)
wcalGrid: Property[bool] = Property(False)
wcalGridColor: Property[ColorType] = Property((255, 252, 0, 82))
wcalUpperGradientEnable: Property[bool] = Property(False)
wcalUpperGradientColor: Property[ColorType] = Property((255, 255, 255, 60))
wcal_eventsText_pastColorEnable: Property[bool] = Property(False)
wcal_eventsText_pastColor: Property[ColorType] = Property((100, 100, 100, 50))
wcal_eventsText_ongoingColorEnable: Property[bool] = Property(False)
wcal_eventsText_ongoingColor: Property[ColorType] = Property((80, 255, 80, 255))
wcal_eventsText_showDesc: Property[bool] = Property(False)
wcal_eventsText_colorize: Property[bool] = Property(True)
wcalFont_eventsText: Property[str | None] = Property(None)
wcal_toolbar_weekNum_negative: Property[bool] = Property(False)
wcal_toolbar_mainMenu_icon: Property[str] = Property("starcal.png")
wcal_weekDays_width: Property[float] = Property(80)
wcal_weekDays_expand: Property[bool] = Property(False)
wcalFont_weekDays: Property[str | None] = Property(None)
wcalFont_pluginsText: Property[str | None] = Property(None)
wcal_pluginsText_firstLineOnly: Property[bool] = Property(False)
wcal_eventsIcon_width: Property[float] = Property(50)
wcalTypeParams: Property[list[WeekCalDayNumParamsDict]] = Property(
	[{"font": None}, {"font": None}, {"font": None}],
)
wcal_daysOfMonth_dir: Property[str] = Property("ltr")
wcal_daysOfMonth_width: Property[float] = Property(30)
wcal_daysOfMonth_expand: Property[bool] = Property(False)
wcal_eventsCount_width: Property[float] = Property(80)
wcal_eventsCount_expand: Property[bool] = Property(False)
wcalFont_eventsBox: Property[str | None] = Property(None)
wcal_moonStatus_width: Property[float] = Property(48)
wcal_moonStatus_southernHemisphere: Property[bool] = Property(False)
wcalCursorLineWidthFactor: Property[float] = Property(0.12)
wcalCursorRoundingFactor: Property[float] = Property(0.5)
dcalWidgetButtonsEnable: Property[bool] = Property(False)
dcalDayParams: Property[list[DayCalTypeParamsDict]] = Property(
	[
		{
			"pos": (0, -12),
			"font": None,
			"color": (220, 220, 220),
			"enable": True,
			"xalign": "center",
			"yalign": "center",
		},
		{
			"pos": (125, 30),
			"font": None,
			"color": (165, 255, 114),
			"enable": True,
			"xalign": "center",
			"yalign": "center",
		},
		{
			"pos": (-125, 24),
			"font": None,
			"color": (0, 200, 205),
			"enable": True,
			"xalign": "center",
			"yalign": "center",
		},
	],
)
dcalMonthParams: Property[list[DayCalNameTypeParamsDict]] = Property(
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
	],
)
dcalWeekdayParams: Property[DayCalTypeParamsDict] = Property(
	{
		"pos": (20, 10),
		"font": None,
		"color": (0, 200, 205),
		"enable": False,
		"xalign": "right",
		"yalign": "buttom",
	},
)
dcalNavButtonsEnable: Property[bool] = Property(True)
dcalNavButtonsGeo: Property[ButtonGeoDict] = Property(
	{
		"auto_rtl": True,
		"size": 64.0,
		"spacing": 10.0,
		"pos": (0, 20),
		"xalign": "center",
		"yalign": "buttom",
	},
)
dcalNavButtonsOpacity: Property[float] = Property(0.7)
dcalWeekdayLocalize: Property[bool] = Property(True)
dcalWeekdayAbbreviate: Property[bool] = Property(False)
dcalWeekdayUppercase: Property[bool] = Property(False)
dcalEventIconSize: Property[float] = Property(20.0)
dcalEventTotalSizeRatio: Property[float] = Property(0.3)
showDesktopWidget: Property[bool] = Property(False)
dcalWinX: Property[int] = Property(0)
dcalWinY: Property[int] = Property(0)
dcalWinWidth: Property[float] = Property(180.0)
dcalWinHeight: Property[float] = Property(180.0)
dcalWinBackgroundColor: Property[ColorType] = Property((0, 10, 0))
dcalWinWidgetButtonsEnable: Property[bool] = Property(True)
dcalWinWidgetButtonsSize: Property[float] = Property(16)
dcalWinWidgetButtonsOpacity: Property[float] = Property(1.0)
dcalWinWeekdayLocalize: Property[bool] = Property(True)
dcalWinWeekdayAbbreviate: Property[bool] = Property(False)
dcalWinWeekdayUppercase: Property[bool] = Property(False)
dcalWinDayParams: Property[list[DayCalTypeParamsDict]] = Property(
	[
		{
			"pos": (0, 5),
			"font": None,
			"color": (220, 220, 220),
			"enable": True,
			"xalign": "left",
			"yalign": "center",
		},
		{
			"pos": (5, 0),
			"font": None,
			"color": (165, 255, 114),
			"enable": True,
			"xalign": "right",
			"yalign": "top",
		},
		{
			"pos": (0, 0),
			"font": None,
			"color": (0, 200, 205),
			"enable": True,
			"xalign": "right",
			"yalign": "buttom",
		},
	],
)
dcalWinMonthParams: Property[list[DayCalNameTypeParamsDict]] = Property(
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
	],
)
dcalWinWeekdayParams: Property[DayCalTypeParamsDict] = Property(
	{
		"pos": (20, 10),
		"font": None,
		"color": (0, 200, 205),
		"enable": False,
		"xalign": "right",
		"yalign": "buttom",
	},
)
dcalWinEventIconSize: Property[float] = Property(20.0)
dcalWinEventTotalSizeRatio: Property[float] = Property(0.3)
dcalWinSeasonPieEnable: Property[bool] = Property(False)
dcalWinSeasonPieGeo: Property[PieGeoDict] = Property(
	{
		"size": 64,
		"thickness": 0.3,
		"pos": (0, 0),
		"xalign": "right",
		"yalign": "top",
		"startAngle": 270,
	},
)
dcalWinSeasonPieSpringColor: Property[ColorType] = Property((167, 252, 1, 180))
dcalWinSeasonPieSummerColor: Property[ColorType] = Property((255, 254, 0, 180))
dcalWinSeasonPieAutumnColor: Property[ColorType] = Property((255, 127, 0, 180))
dcalWinSeasonPieWinterColor: Property[ColorType] = Property((1, 191, 255, 180))
dcalWinSeasonPieTextColor: Property[ColorType] = Property((255, 255, 255, 180))
monthPBarCalType: Property[int] = Property(-1)
seasonPBar_southernHemisphere: Property[bool] = Property(False)
labelBoxBorderWidth: Property[int] = Property(0)
labelBoxMenuActiveColor: Property[ColorType] = Property((0, 255, 0, 255))
labelBoxYearColorEnable: Property[bool] = Property(False)
labelBoxYearColor: Property[ColorType] = Property((255, 132, 255, 255))
labelBoxMonthColorEnable: Property[bool] = Property(False)
labelBoxMonthColor: Property[ColorType] = Property((255, 132, 255, 255))
labelBoxFontEnable: Property[bool] = Property(False)
labelBoxFont: Property[Font | None] = Property(None)
labelBoxPrimaryFontEnable: Property[bool] = Property(False)
labelBoxPrimaryFont: Property[Font | None] = Property(None)
boldYmLabel: Property[bool] = Property(True)
ud__wcalToolbarData: Property[dict | None] = Property(None)
ud__mainToolbarData: Property[dict | None] = Property(None)
preferencesPagePath: Property[str] = Property("")
customizePagePath: Property[str] = Property("")
localTzHist: Property[list[str]] = Property([])
showDigClockTb: Property[bool] = Property(True)
menuIconPadding: Property[int] = Property(7)
eventTreeGroupIconSize: Property[float] = Property(24)
treeIconSize: Property[float] = Property(22)
labelBoxIconSize: Property[float] = Property(20)
stackIconSize: Property[float] = Property(22)
dcalWidgetButtons: Property[list[dict[str, Any]]] = Property(
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
	],
)
dcalWinWidgetButtons: Property[list[dict[str, Any]]] = Property(
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
	],
)
menuIconEdgePadding: Property[int] = Property(3)
rightPanelEventIconSize: Property[float] = Property(20)
eventTreeIconSize: Property[float] = Property(22)
menuEventCheckIconSize: Property[float] = Property(20)
toolbarIconSize: Property[float] = Property(24)
mcalEventIconSizeMax: Property[float] = Property(26)
messageDialogIconSize: Property[float] = Property(48)
menuCheckSize: Property[float] = Property(22)
menuIconSize: Property[float] = Property(18)
comboBoxIconSize: Property[float] = Property(20)
imageInputIconSize: Property[float] = Property(32)
maxWeekCacheSize: Property[int] = Property(12)
wcalPadding: Property[int] = Property(10)
buttonIconSize: Property[float] = Property(20)
wcalEventIconSizeMax: Property[float] = Property(26)
eventWeekViewTimeFormat: Property[str] = Property("HM$")


confParams = {
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
confParamsLive = {
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
confParamsCustomize = {
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
dayCalWinParamsLive = {
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
