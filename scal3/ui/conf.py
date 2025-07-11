from __future__ import annotations

import typing

from scal3.color_utils import RGB, RGBA
from scal3.option import ListOption, Option

if typing.TYPE_CHECKING:
	from typing import Annotated, Any, Final

	from scal3.color_utils import ColorType
	from scal3.font import Font
	from scal3.ui.pytypes import (
		ButtonGeoDict,
		CalTypeOptionsDict,
		CustomizableToolBoxDict,
		DayCalTypeDayOptionsDict,
		DayCalTypeWMOptionsDict,
		FloatSpin,
		IntSpin,
		PieGeoDict,
		WeekCalDayNumOptionsDict,
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
	"confOptions",
	"confOptionsCustomize",
	"confOptionsLive",
	"cursorBgColor",
	"cursorOutColor",
	"customizePagePath",
	"dayCalWinOptionsLive",
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

showMain: Final[Option[bool]] = Option(True)
winTaskbar: Final[Option[bool]] = Option(False)
useAppIndicator: Final[Option[bool]] = Option(True)
winX: Final[Option[int]] = Option(0)
winY: Final[Option[int]] = Option(0)
winWidth: Final[Option[int]] = Option(480)
winHeight: Final[Option[int]] = Option(300)
winKeepAbove: Final[Option[bool]] = Option(True)
winSticky: Final[Option[bool]] = Option(True)
winMaximized: Final[Option[bool]] = Option(False)
mainWinItems: Final[ListOption[tuple[str, bool]]] = ListOption(
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
mainWinFooterItems: Final[ListOption[str]] = ListOption(
	["pluginsText", "eventDayView", "statusBar"]
)
pluginsTextEnable: Final[Option[bool]] = Option(False)
pluginsTextInsideExpander: Final[Option[bool]] = Option(True)
pluginsTextIsExpanded: Final[Option[bool]] = Option(True)
eventDayViewEnable: Final[Option[bool]] = Option(False)
eventDayViewEventSep: Final[Option[str]] = Option("\n")
eventViewMaxHeight: Final[Annotated[Option[int], IntSpin(1, 9999, 1)]] = Option(200)
statusBarEnable: Final[Option[bool]] = Option(True)
statusBarDatesReverseOrder: Final[Option[bool]] = Option(False)
statusBarDatesColorEnable: Final[Option[bool]] = Option(False)
statusBarDatesColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=132, blue=255, alpha=255)
)
fontCustomEnable: Final[Option[bool]] = Option(False)
fontCustom: Final[Option[Font | None]] = Option(None)
buttonIconEnable: Final[Option[bool]] = Option(True)
useSystemIcons: Final[Option[bool]] = Option(False)
oldStyleProgressBar: Final[Option[bool]] = Option(False)
bgColor: Final[Option[ColorType]] = Option(RGBA(red=26, green=0, blue=1, alpha=255))
borderColor: Final[Option[ColorType]] = Option(
	RGBA(red=123, green=40, blue=0, alpha=255)
)
borderTextColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=255, blue=255, alpha=255)
)
textColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=255, blue=255, alpha=255)
)
holidayColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=160, blue=0, alpha=255)
)
inactiveColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=255, blue=255, alpha=115)
)
todayCellColor: Final[Option[ColorType]] = Option(
	RGBA(red=0, green=255, blue=0, alpha=50)
)
cursorOutColor: Final[Option[ColorType]] = Option(
	RGBA(red=213, green=207, blue=0, alpha=255)
)
cursorBgColor: Final[Option[ColorType]] = Option(
	RGBA(red=41, green=41, blue=41, alpha=255)
)
showDigClockTr: Final[Option[bool]] = Option(True)
statusIconImage: Final[Option[str]] = Option("status-icons/dark-green.svg")
statusIconImageHoli: Final[Option[str]] = Option("status-icons/dark-red.svg")
statusIconFontFamilyEnable: Final[Option[bool]] = Option(False)
statusIconFontFamily: Final[Option[str | None]] = Option(None)
statusIconHolidayFontColorEnable: Final[Option[bool]] = Option(False)
statusIconHolidayFontColor: Final[Option[ColorType | None]] = Option(None)
statusIconLocalizeNumber: Final[Option[bool]] = Option(True)
statusIconFixedSizeEnable: Final[Option[bool]] = Option(False)
statusIconFixedSizeWH: Final[Option[tuple[int, int]]] = Option((24, 24))
pluginsTextStatusIcon: Final[Option[bool]] = Option(False)
maxDayCacheSize: Final[Annotated[Option[int], IntSpin(100, 9999, 10)]] = Option(100)
eventDayViewTimeFormat: Final[Option[str]] = Option("HM$")
cellMenuXOffset: Final[Annotated[Option[int], IntSpin(0, 999, 1)]] = Option(0)
winControllerEnable: Final[Option[bool]] = Option(True)
winControllerTheme: Final[Option[str]] = Option("default")
winControllerButtons: Final[ListOption[tuple[str, bool]]] = ListOption(
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
winControllerIconSize: Final[Annotated[Option[int], IntSpin(5, 128, 1)]] = Option(24)
winControllerBorder: Final[Annotated[Option[int], IntSpin(0, 99, 1)]] = Option(0)
winControllerSpacing: Final[Annotated[Option[int], IntSpin(0, 99, 1)]] = Option(0)
winControllerPressState: Final[Option[bool]] = Option(False)
mainWinRightPanelEnable: Final[Option[bool]] = Option(True)
mainWinRightPanelRatio: Final[Option[float]] = Option(0.5)
mainWinRightPanelSwap: Final[Option[bool]] = Option(False)
mainWinRightPanelWidth: Final[Annotated[Option[int], IntSpin(1, 9999, 10)]] = Option(
	200
)
mainWinRightPanelWidthRatio: Final[Annotated[Option[float], FloatSpin(0, 1, 0.01)]] = (
	Option(0.25)
)
mainWinRightPanelWidthRatioEnable: Final[Option[bool]] = Option(True)
mainWinRightPanelEventFontEnable: Final[Option[bool]] = Option(False)
mainWinRightPanelEventFont: Final[Option[Font | None]] = Option(None)
mainWinRightPanelEventTimeFontEnable: Final[Option[bool]] = Option(False)
mainWinRightPanelEventTimeFont: Final[Option[Font | None]] = Option(None)
mainWinRightPanelEventJustification: Final[Option[str]] = Option("left")
mainWinRightPanelEventSep: Final[Option[str]] = Option("\n\n")
mainWinRightPanelPluginsFontEnable: Final[Option[bool]] = Option(False)
mainWinRightPanelPluginsFont: Final[Option[Font | None]] = Option(None)
mainWinRightPanelPluginsJustification: Final[Option[str]] = Option("left")
mainWinRightPanelResizeOnToggle: Final[Option[bool]] = Option(True)
mainWinRightPanelBorderWidth: Final[Annotated[Option[int], IntSpin(0, 999, 1)]] = (
	Option(7)
)
mcalLeftMargin: Final[Annotated[Option[int], IntSpin(0, 999, 1)]] = Option(30)
mcalTopMargin: Final[Annotated[Option[int], IntSpin(0, 999, 1)]] = Option(30)
mcalTypeParams: Final[ListOption[CalTypeOptionsDict]] = ListOption(
	[
		{"pos": (0, -2), "font": None, "color": (220, 220, 220)},
		{"pos": (18, 5), "font": None, "color": (165, 255, 114)},
		{"pos": (-18, 4), "font": None, "color": (0, 200, 205)},
	]
)
mcalGrid: Final[Option[bool]] = Option(False)
mcalGridColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=252, blue=0, alpha=82)
)
mcalCornerMenuTextColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=255, blue=255, alpha=255)
)
mcalCursorLineWidthFactor: Final[Annotated[Option[float], FloatSpin(0, 1, 0.1)]] = (
	Option(0.12)
)
mcalCursorRoundingFactor: Final[Annotated[Option[float], FloatSpin(0, 1, 0.1)]] = (
	Option(0.5)
)
wcalTextSizeScale: Final[Annotated[Option[float], FloatSpin(0.01, 1, 0.1)]] = Option(
	0.6
)
wcalItems: Final[ListOption[tuple[str, bool]]] = ListOption(
	[
		("toolbar", True),
		("weekDays", True),
		("pluginsText", True),
		("eventsIcon", True),
		("eventsText", True),
		("daysOfMonth", True),
	]
)
wcalGrid: Final[Option[bool]] = Option(False)
wcalGridColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=252, blue=0, alpha=82)
)
wcalUpperGradientEnable: Final[Option[bool]] = Option(False)
wcalUpperGradientColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=255, blue=255, alpha=60)
)
wcal_eventsText_pastColorEnable: Final[Option[bool]] = Option(False)
wcal_eventsText_pastColor: Final[Option[ColorType]] = Option(
	RGBA(red=100, green=100, blue=100, alpha=50)
)
wcal_eventsText_ongoingColorEnable: Final[Option[bool]] = Option(False)
wcal_eventsText_ongoingColor: Final[Option[ColorType]] = Option(
	RGBA(red=80, green=255, blue=80, alpha=255)
)
wcal_eventsText_showDesc: Final[Option[bool]] = Option(False)
wcal_eventsText_colorize: Final[Option[bool]] = Option(True)
wcalFont_eventsText: Final[Option[str | None]] = Option(None)
wcal_toolbar_weekNum_negative: Final[Option[bool]] = Option(False)
wcal_toolbar_mainMenu_icon: Final[Option[str]] = Option("starcal.png")
wcal_weekDays_width: Final[Option[int]] = Option(80)
wcal_weekDays_expand: Final[Option[bool]] = Option(False)
wcalFont_weekDays: Final[Option[str | None]] = Option(None)
wcalFont_pluginsText: Final[Option[str | None]] = Option(None)
wcal_pluginsText_firstLineOnly: Final[Option[bool]] = Option(False)
wcal_eventsIcon_width: Final[Option[int]] = Option(50)
wcalTypeParams: Final[ListOption[WeekCalDayNumOptionsDict]] = ListOption(
	[{"font": None}, {"font": None}, {"font": None}]
)
wcal_daysOfMonth_dir: Final[Option[str]] = Option("ltr")
wcal_daysOfMonth_width: Final[Option[int]] = Option(30)
wcal_daysOfMonth_expand: Final[Option[bool]] = Option(False)
wcal_eventsCount_width: Final[Option[int]] = Option(80)
wcal_eventsCount_expand: Final[Option[bool]] = Option(False)
wcalFont_eventsBox: Final[Option[str | None]] = Option(None)
wcal_moonStatus_width: Final[Option[int]] = Option(48)
wcal_moonStatus_southernHemisphere: Final[Option[bool]] = Option(False)
wcalCursorLineWidthFactor: Final[Annotated[Option[float], FloatSpin(0, 1, 0.1)]] = (
	Option(0.12)
)
wcalCursorRoundingFactor: Final[Annotated[Option[float], FloatSpin(0, 1, 0.1)]] = (
	Option(0.5)
)
dcalWidgetButtonsEnable: Final[Option[bool]] = Option(False)
dcalDayParams: Final[ListOption[DayCalTypeDayOptionsDict]] = ListOption(
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
dcalMonthParams: Final[ListOption[DayCalTypeWMOptionsDict]] = ListOption(
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
dcalWeekdayParams: Final[Option[DayCalTypeWMOptionsDict]] = Option(
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
dcalNavButtonsEnable: Final[Option[bool]] = Option(True)
dcalNavButtonsGeo: Final[Option[ButtonGeoDict]] = Option(
	{
		"auto_rtl": True,
		"size": 64,
		"spacing": 10,
		"pos": (0, 20),
		"xalign": "center",
		"yalign": "buttom",
	}
)
dcalNavButtonsOpacity: Final[Option[float]] = Option(0.7)
dcalWeekdayLocalize: Final[Option[bool]] = Option(True)
dcalWeekdayAbbreviate: Final[Option[bool]] = Option(False)
dcalWeekdayUppercase: Final[Option[bool]] = Option(False)
dcalEventIconSize: Final[Option[int]] = Option(20)
dcalEventTotalSizeRatio: Final[Option[float]] = Option(0.3)
showDesktopWidget: Final[Option[bool]] = Option(False)
dcalWinX: Final[Option[int]] = Option(0)
dcalWinY: Final[Option[int]] = Option(0)
dcalWinWidth: Final[Option[int]] = Option(180)
dcalWinHeight: Final[Option[int]] = Option(180)
dcalWinBackgroundColor: Final[Option[ColorType]] = Option(RGB(red=0, green=10, blue=0))
dcalWinWidgetButtonsEnable: Final[Option[bool]] = Option(True)
dcalWinWidgetButtonsSize: Final[Option[int]] = Option(16)
dcalWinWidgetButtonsOpacity: Final[Option[float]] = Option(1.0)
dcalWinWeekdayLocalize: Final[Option[bool]] = Option(True)
dcalWinWeekdayAbbreviate: Final[Option[bool]] = Option(False)
dcalWinWeekdayUppercase: Final[Option[bool]] = Option(False)
dcalWinDayParams: Final[ListOption[DayCalTypeDayOptionsDict]] = ListOption(
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
dcalWinMonthParams: Final[ListOption[DayCalTypeWMOptionsDict]] = ListOption(
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
dcalWinWeekdayParams: Final[Option[DayCalTypeWMOptionsDict]] = Option(
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
dcalWinEventIconSize: Final[Option[int]] = Option(20)
dcalWinEventTotalSizeRatio: Final[Option[float]] = Option(0.3)
dcalWinSeasonPieEnable: Final[Option[bool]] = Option(False)
dcalWinSeasonPieGeo: Final[Option[PieGeoDict]] = Option(
	{
		"size": 64,
		"thickness": 0.3,
		"pos": (0, 0),
		"xalign": "right",
		"yalign": "top",
		"startAngle": 270,
	}
)
dcalWinSeasonPieSpringColor: Final[Option[ColorType]] = Option(
	RGBA(red=167, green=252, blue=1, alpha=180)
)
dcalWinSeasonPieSummerColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=254, blue=0, alpha=180)
)
dcalWinSeasonPieAutumnColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=127, blue=0, alpha=180)
)
dcalWinSeasonPieWinterColor: Final[Option[ColorType]] = Option(
	RGBA(red=1, green=191, blue=255, alpha=180)
)
dcalWinSeasonPieTextColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=255, blue=255, alpha=180)
)
monthPBarCalType: Final[Option[int]] = Option(-1)
seasonPBar_southernHemisphere: Final[Option[bool]] = Option(False)
labelBoxBorderWidth: Final[Annotated[Option[int], IntSpin(0, 99, 1)]] = Option(0)
labelBoxMenuActiveColor: Final[Option[ColorType]] = Option(
	RGBA(red=0, green=255, blue=0, alpha=255)
)
labelBoxYearColorEnable: Final[Option[bool]] = Option(False)
labelBoxYearColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=132, blue=255, alpha=255)
)
labelBoxMonthColorEnable: Final[Option[bool]] = Option(False)
labelBoxMonthColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=132, blue=255, alpha=255)
)
labelBoxFontEnable: Final[Option[bool]] = Option(False)
labelBoxFont: Final[Option[Font | None]] = Option(None)
labelBoxPrimaryFontEnable: Final[Option[bool]] = Option(False)
labelBoxPrimaryFont: Final[Option[Font | None]] = Option(None)
boldYmLabel: Final[Option[bool]] = Option(True)
ud__wcalToolbarData: Final[Option[CustomizableToolBoxDict | None]] = Option(None)
ud__mainToolbarData: Final[Option[CustomizableToolBoxDict | None]] = Option(None)
preferencesPagePath: Final[Option[str]] = Option("")
customizePagePath: Final[Option[str]] = Option("")
localTzHist: Final[ListOption[str]] = ListOption([])
showDigClockTb: Final[Option[bool]] = Option(True)
menuIconPadding: Final[Option[int]] = Option(7)
eventTreeGroupIconSize: Final[Option[int]] = Option(24)
treeIconSize: Final[Option[int]] = Option(22)
labelBoxIconSize: Final[Option[int]] = Option(20)
stackIconSize: Final[Option[int]] = Option(22)
dcalWidgetButtons: Final[ListOption[dict[str, Any]]] = ListOption(
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
dcalWinWidgetButtons: Final[ListOption[dict[str, Any]]] = ListOption(
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
menuIconEdgePadding: Final[Option[int]] = Option(3)
rightPanelEventIconSize: Final[Annotated[Option[int], IntSpin(5, 128, 1)]] = Option(20)
eventTreeIconSize: Final[Option[int]] = Option(22)
menuEventCheckIconSize: Final[Option[int]] = Option(20)
toolbarIconSize: Final[Option[int]] = Option(24)
mcalEventIconSizeMax: Final[Option[int]] = Option(26)
messageDialogIconSize: Final[Option[int]] = Option(48)
menuCheckSize: Final[Option[int]] = Option(22)
menuIconSize: Final[Option[int]] = Option(18)
comboBoxIconSize: Final[Option[int]] = Option(20)
imageInputIconSize: Final[Option[int]] = Option(32)
maxWeekCacheSize: Final[Option[int]] = Option(12)
wcalPadding: Final[Option[int]] = Option(10)
buttonIconSize: Final[Option[int]] = Option(20)
wcalEventIconSizeMax: Final[Option[int]] = Option(26)
eventWeekViewTimeFormat: Final[Option[str]] = Option("HM$")


confOptions: dict[str, Option[Any]] = {
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
confOptionsLive: dict[str, Option[Any]] = {
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
confOptionsCustomize: dict[str, Option[Any]] = {
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
dayCalWinOptionsLive: dict[str, Option[Any]] = {
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
