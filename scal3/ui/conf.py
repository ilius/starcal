from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
	from scal3.font import Font


__all__ = [
	"bgColor",
	"boldYmLabel",
	"borderColor",
	"borderTextColor",
	"buttonIconEnable",
	"buttonIconSize",
	"cellMenuXOffset",
	"comboBoxIconSize",
	"cursorBgColor",
	"cursorOutColor",
	"customizePagePath",
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

showMain: bool = True
winTaskbar: bool = False
useAppIndicator: bool = True
winX: int = 0
winY: int = 0
winWidth: int = 480
winHeight: int = 300
winKeepAbove: bool = True
winSticky: bool = True
winMaximized: bool = False
mainWinItems: list[tuple[str, bool]] = [
	("toolbar", True),
	("labelBox", True),
	("monthCal", False),
	("weekCal", True),
	("dayCal", False),
	("monthPBar", False),
	("seasonPBar", True),
	("yearPBar", False),
]
mainWinFooterItems: list[str] = ["pluginsText", "eventDayView", "statusBar"]
pluginsTextEnable: bool = False
pluginsTextInsideExpander: bool = True
pluginsTextIsExpanded: bool = True
eventDayViewEnable: bool = False
eventDayViewEventSep: str = "\n"
eventViewMaxHeight: int = 200
statusBarEnable: bool = True
statusBarDatesReverseOrder: bool = False
statusBarDatesColorEnable: bool = False
statusBarDatesColor = (255, 132, 255, 255)
fontCustomEnable: bool = False
fontCustom: Font | None = None
buttonIconEnable: bool = True
useSystemIcons: bool = False
oldStyleProgressBar: bool = False
bgColor = (26, 0, 1, 255)
borderColor = (123, 40, 0, 255)
borderTextColor = (255, 255, 255, 255)
textColor = (255, 255, 255, 255)
holidayColor = (255, 160, 0, 255)
inactiveColor = (255, 255, 255, 115)
todayCellColor = (0, 255, 0, 50)
cursorOutColor = (213, 207, 0, 255)
cursorBgColor = (41, 41, 41, 255)
showDigClockTr: bool = True
statusIconImage: str = "status-icons/dark-green.svg"
statusIconImageHoli: str = "status-icons/dark-red.svg"
statusIconFontFamilyEnable: bool = False
statusIconFontFamily: str | None = None
statusIconHolidayFontColorEnable: bool = False
statusIconHolidayFontColor = None
statusIconLocalizeNumber: bool = True
statusIconFixedSizeEnable: bool = False
statusIconFixedSizeWH: tuple[int, int] = (24, 24)
pluginsTextStatusIcon: bool = False
maxDayCacheSize: int = 100
eventDayViewTimeFormat: str = "HM$"
cellMenuXOffset: int = 0
winControllerEnable: bool = True
winControllerTheme: str = "default"
winControllerButtons: list[tuple[str, bool]] = [
	("sep", True),
	("rightPanel", True),
	("min", True),
	("max", True),
	("close", True),
	("sep", False),
	("sep", False),
	("sep", False),
]
winControllerIconSize: int = 24
winControllerBorder: int = 0
winControllerSpacing: int = 0
winControllerPressState: bool = False
mainWinRightPanelEnable: bool = True
mainWinRightPanelRatio: float = 0.5
mainWinRightPanelSwap: bool = False
mainWinRightPanelWidth: int = 200
mainWinRightPanelWidthRatio: float = 0.25
mainWinRightPanelWidthRatioEnable: bool = True
mainWinRightPanelEventFontEnable: bool = False
mainWinRightPanelEventFont: Font | None = None
mainWinRightPanelEventTimeFontEnable: bool = False
mainWinRightPanelEventTimeFont: Font | None = None
mainWinRightPanelEventJustification: str = "left"
mainWinRightPanelEventSep: str = "\n\n"
mainWinRightPanelPluginsFontEnable: bool = False
mainWinRightPanelPluginsFont: Font | None = None
mainWinRightPanelPluginsJustification: str = "left"
mainWinRightPanelResizeOnToggle: bool = True
mainWinRightPanelBorderWidth: int = 7
mcalLeftMargin: int = 30
mcalTopMargin: int = 30
mcalTypeParams: list[dict] = [
	{"pos": (0, -2), "font": None, "color": (220, 220, 220)},
	{"pos": (18, 5), "font": None, "color": (165, 255, 114)},
	{"pos": (-18, 4), "font": None, "color": (0, 200, 205)},
]
mcalGrid: bool = False
mcalGridColor = (255, 252, 0, 82)
mcalCornerMenuTextColor = (255, 255, 255, 255)
mcalCursorLineWidthFactor: float = 0.12
mcalCursorRoundingFactor: float = 0.5
wcalTextSizeScale: float = 0.6
wcalItems: list[tuple[str, bool]] = [
	("toolbar", True),
	("weekDays", True),
	("pluginsText", True),
	("eventsIcon", True),
	("eventsText", True),
	("daysOfMonth", True),
]
wcalGrid: bool = False
wcalGridColor = (255, 252, 0, 82)
wcalUpperGradientEnable: bool = False
wcalUpperGradientColor = (255, 255, 255, 60)
wcal_eventsText_pastColorEnable: bool = False
wcal_eventsText_pastColor = (100, 100, 100, 50)
wcal_eventsText_ongoingColorEnable: bool = False
wcal_eventsText_ongoingColor = (80, 255, 80, 255)
wcal_eventsText_showDesc: bool = False
wcal_eventsText_colorize: bool = True
wcalFont_eventsText: str | None = None
wcal_toolbar_weekNum_negative: bool = False
wcal_toolbar_mainMenu_icon: str = "starcal.png"
wcal_weekDays_width: int = 80
wcal_weekDays_expand: bool = False
wcalFont_weekDays: str | None = None
wcalFont_pluginsText: str | None = None
wcal_pluginsText_firstLineOnly: bool = False
wcal_eventsIcon_width: int = 50
wcalTypeParams: list[dict] = [{"font": None}, {"font": None}, {"font": None}]
wcal_daysOfMonth_dir: str = "ltr"
wcal_daysOfMonth_width: int = 30
wcal_daysOfMonth_expand: bool = False
wcal_eventsCount_width: int = 80
wcal_eventsCount_expand: bool = False
wcalFont_eventsBox: str | None = None
wcal_moonStatus_width: int = 48
wcal_moonStatus_southernHemisphere: bool = False
wcalCursorLineWidthFactor: float = 0.12
wcalCursorRoundingFactor: float = 0.5
dcalWidgetButtonsEnable: bool = False
dcalDayParams: list[dict] = [
	{
		"enable": True,
		"pos": (0, -12),
		"xalign": "center",
		"yalign": "center",
		"font": None,
		"color": (220, 220, 220),
	},
	{
		"enable": True,
		"pos": (125, 30),
		"xalign": "center",
		"yalign": "center",
		"font": None,
		"color": (165, 255, 114),
	},
	{
		"enable": True,
		"pos": (-125, 24),
		"xalign": "center",
		"yalign": "center",
		"font": None,
		"color": (0, 200, 205),
	},
]
dcalMonthParams: list[dict] = [
	{
		"enable": False,
		"pos": (0, -12),
		"xalign": "center",
		"yalign": "center",
		"font": None,
		"color": (220, 220, 220),
		"abbreviate": False,
		"uppercase": False,
	},
	{
		"enable": False,
		"pos": (125, 30),
		"xalign": "center",
		"yalign": "center",
		"font": None,
		"color": (165, 255, 114),
		"abbreviate": False,
		"uppercase": False,
	},
	{
		"enable": False,
		"pos": (-125, 24),
		"xalign": "center",
		"yalign": "center",
		"font": None,
		"color": (0, 200, 205),
		"abbreviate": False,
		"uppercase": False,
	},
]
dcalWeekdayParams: list[dict] = {
	"enable": False,
	"pos": (20, 10),
	"xalign": "right",
	"yalign": "buttom",
	"font": None,
	"color": (0, 200, 205),
}
dcalNavButtonsEnable: bool = True
dcalNavButtonsGeo: list[dict] = {
	"auto_rtl": True,
	"size": 64.0,
	"spacing": 10.0,
	"pos": (0, 20),
	"xalign": "center",
	"yalign": "buttom",
}
dcalNavButtonsOpacity: float = 0.7
dcalWeekdayLocalize: bool = True
dcalWeekdayAbbreviate: bool = False
dcalWeekdayUppercase: bool = False
dcalEventIconSize: float = 20.0
dcalEventTotalSizeRatio: float = 0.3
showDesktopWidget: bool = False
dcalWinX: int = 0
dcalWinY: int = 0
dcalWinWidth: float = 180.0
dcalWinHeight: float = 180.0
dcalWinBackgroundColor = (0, 10, 0)
dcalWinWidgetButtonsEnable: bool = True
dcalWinWeekdayLocalize: bool = True
dcalWinWeekdayAbbreviate: bool = False
dcalWinWeekdayUppercase: bool = False
dcalWinDayParams: list[dict] = [
	{
		"pos": (0, 5),
		"xalign": "left",
		"yalign": "center",
		"font": None,
		"color": (220, 220, 220),
	},
	{
		"pos": (5, 0),
		"xalign": "right",
		"yalign": "top",
		"font": None,
		"color": (165, 255, 114),
	},
	{
		"pos": (0, 0),
		"xalign": "right",
		"yalign": "buttom",
		"font": None,
		"color": (0, 200, 205),
	},
]
dcalWinMonthParams: list[dict] = [
	{
		"enable": False,
		"pos": (0, 5),
		"xalign": "left",
		"yalign": "center",
		"font": None,
		"color": (220, 220, 220),
		"abbreviate": False,
		"uppercase": False,
	},
	{
		"enable": False,
		"pos": (5, 0),
		"xalign": "right",
		"yalign": "top",
		"font": None,
		"color": (165, 255, 114),
		"abbreviate": False,
		"uppercase": False,
	},
	{
		"enable": False,
		"pos": (0, 0),
		"xalign": "right",
		"yalign": "buttom",
		"font": None,
		"color": (0, 200, 205),
		"abbreviate": False,
		"uppercase": False,
	},
]
dcalWinWeekdayParams: list[dict] = {
	"enable": False,
	"pos": (20, 10),
	"xalign": "right",
	"yalign": "buttom",
	"font": None,
	"color": (0, 200, 205),
}
dcalWinEventIconSize: float = 20.0
dcalWinEventTotalSizeRatio: float = 0.3
dcalWinSeasonPieEnable: bool = False
dcalWinSeasonPieGeo: list[dict] = {
	"size": 64,
	"thickness": 0.3,
	"pos": (0, 0),
	"xalign": "right",
	"yalign": "top",
	"startAngle": 270,
}
dcalWinSeasonPieSpringColor = (167, 252, 1, 180)
dcalWinSeasonPieSummerColor = (255, 254, 0, 180)
dcalWinSeasonPieAutumnColor = (255, 127, 0, 180)
dcalWinSeasonPieWinterColor = (1, 191, 255, 180)
dcalWinSeasonPieTextColor = (255, 255, 255, 180)
monthPBarCalType: int = -1
seasonPBar_southernHemisphere: bool = False
labelBoxBorderWidth: int = 0
labelBoxMenuActiveColor = (0, 255, 0, 255)
labelBoxYearColorEnable: bool = False
labelBoxYearColor = (255, 132, 255, 255)
labelBoxMonthColorEnable: bool = False
labelBoxMonthColor = (255, 132, 255, 255)
labelBoxFontEnable: bool = False
labelBoxFont: Font | None = None
labelBoxPrimaryFontEnable: bool = False
labelBoxPrimaryFont: Font | None = None
boldYmLabel: bool = True
ud__wcalToolbarData: dict | None = None
ud__mainToolbarData: dict | None = None
preferencesPagePath: str = ""
customizePagePath: str = ""
localTzHist: list[str] = []
showDigClockTb: bool = True
menuIconPadding: int = 7
eventTreeGroupIconSize: int = 24
treeIconSize: int = 22
labelBoxIconSize: int = 20
stackIconSize: int = 22
dcalWidgetButtons: list[dict] = [
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
dcalWinWidgetButtons: list[dict] = [
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
		"iconSize": 16,
		"onClick": "openCustomize",
		"pos": (0, 1),
		"xalign": "left",
		"yalign": "buttom",
		"autoDir": False,
	},
]
menuIconEdgePadding: int = 3
rightPanelEventIconSize: int = 20
eventTreeIconSize: int = 22
menuEventCheckIconSize: int = 20
toolbarIconSize: int = 24
mcalEventIconSizeMax: int = 26
messageDialogIconSize: int = 48
menuCheckSize: int = 22
menuIconSize: int = 18
comboBoxIconSize: int = 20
imageInputIconSize: int = 32
maxWeekCacheSize: int = 12
wcalPadding: int = 10
buttonIconSize: int = 20
wcalEventIconSizeMax: int = 26
eventWeekViewTimeFormat: str = "HM$"

statusIconImageDefault = statusIconImage
wcal_toolbar_mainMenu_icon_default = wcal_toolbar_mainMenu_icon
statusIconImageHoliDefault = statusIconImageHoli
winControllerButtonsDefault = winControllerButtons.copy()
mainWinItemsDefault = mainWinItems.copy()
wcalItemsDefault = wcalItems.copy()
