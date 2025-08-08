from __future__ import annotations

import typing

from scal3.color_utils import RGB, RGBA
from scal3.option import ListOption, Option

if typing.TYPE_CHECKING:
	from typing import Any, Final

	from scal3.color_utils import ColorType
	from scal3.font import Font
	from scal3.ui.pytypes import (
		ButtonGeoDict,
		CalTypeOptionsDict,
		CustomizableToolBoxDict,
		DayCalTypeDayOptionsDict,
		DayCalTypeWMOptionsDict,
		DayCalWidgetButtonDict,
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


"""Open main window on start
Preferences: General"""
showMain: Final[Option[bool]] = Option(True)

"""Window in Taskbar
Preferences: General"""
winTaskbar: Final[Option[bool]] = Option(False)

"""Use AppIndicator
Preferences: General"""
useAppIndicator: Final[Option[bool]] = Option(True)

"""Window X
MainWin: Move"""
winX: Final[Option[int]] = Option(0)

"""Window Y
MainWin: Move"""
winY: Final[Option[int]] = Option(0)

"""Window Width
MainWin: Resize"""
winWidth: Final[Option[int]] = Option(480)

"""Window Height
MainWin: Resize"""
winHeight: Final[Option[int]] = Option(300)

"""On Top
MainWin: Menu"""
winKeepAbove: Final[Option[bool]] = Option(True)

"""On All Desktops
MainWin: Menu"""
winSticky: Final[Option[bool]] = Option(True)

"""Window Maximized
MainWin: Window Controller: Maximize Window"""
winMaximized: Final[Option[bool]] = Option(False)

"""Items
MainWin: Customize: Main Panel"""
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

"""Footer Items
MainWin: Customize: (Footer)"""
mainWinFooterItems: Final[ListOption[str]] = ListOption(
	["pluginsText", "eventDayView", "statusBar"]
)

"""Enable
MainWin: Customize: (Footer): Plugins Text"""
pluginsTextEnable: Final[Option[bool]] = Option(False)

"""Inside Expander
MainWin: Customize: (Footer): Plugins Text"""
pluginsTextInsideExpander: Final[Option[bool]] = Option(True)

"""Is Expanded
MainWin: (Footer): Plugins Text"""
pluginsTextIsExpanded: Final[Option[bool]] = Option(True)

"""Enable
MainWin: Customize: (Footer): Events of Day"""
eventDayViewEnable: Final[Option[bool]] = Option(False)

"""Event Text Separator
MainWin: Customize: (Footer): Events of Day"""
eventDayViewEventSep: Final[Option[str]] = Option("\n")

"""Maximum Height
MainWin: Customize: (Footer): Events of Day
Valid: IntSpin(1, 9999, 1)"""
eventViewMaxHeight: Final[Option[int]] = Option(200)

"""Enable
MainWin: Customize: (Footer): Status Bar"""
statusBarEnable: Final[Option[bool]] = Option(True)

"""Reverse the order of dates
MainWin: Customize: (Footer): Status Bar"""
statusBarDatesReverseOrder: Final[Option[bool]] = Option(False)

"""Dates Color
MainWin: Customize: (Footer): Status Bar"""
statusBarDatesColorEnable: Final[Option[bool]] = Option(False)

"""Dates Color
MainWin: Customize: (Footer): Status Bar"""
statusBarDatesColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=132, blue=255, alpha=255)
)

"""Application Font
Preferences: Appearance"""
fontCustomEnable: Final[Option[bool]] = Option(False)

"""Application Font
Preferences: Appearance"""
fontCustom: Final[Option[Font | None]] = Option(None)

"""Show icons in buttons
Preferences: Appearance"""
buttonIconEnable: Final[Option[bool]] = Option(True)

"""Use System Icons
Preferences: Appearance"""
useSystemIcons: Final[Option[bool]] = Option(False)

"""Old-style Progress Bar
Preferences: Appearance"""
oldStyleProgressBar: Final[Option[bool]] = Option(False)

"""Background
Preferences: Appearance: Colors"""
bgColor: Final[Option[ColorType]] = Option(RGBA(red=26, green=0, blue=1, alpha=255))

"""Border
Preferences: Appearance: Colors"""
borderColor: Final[Option[ColorType]] = Option(
	RGBA(red=123, green=40, blue=0, alpha=255)
)

"""Border Font
Preferences: Appearance: Colors"""
borderTextColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=255, blue=255, alpha=255)
)

"""Normal Text
Preferences: Appearance: Colors"""
textColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=255, blue=255, alpha=255)
)

"""Holidays Font
Preferences: Appearance: Colors"""
holidayColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=160, blue=0, alpha=255)
)

"""Inactive Day Font
Preferences: Appearance: Colors"""
inactiveColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=255, blue=255, alpha=115)
)

"""Today
Preferences: Appearance: Colors"""
todayCellColor: Final[Option[ColorType]] = Option(
	RGBA(red=0, green=255, blue=0, alpha=50)
)

"""Cursor
Preferences: Appearance: Colors"""
cursorOutColor: Final[Option[ColorType]] = Option(
	RGBA(red=213, green=207, blue=0, alpha=255)
)

"""Cursor BG
Preferences: Appearance: Colors"""
cursorBgColor: Final[Option[ColorType]] = Option(
	RGBA(red=41, green=41, blue=41, alpha=255)
)

"""Show Digital Clock: On Status Icon
Preferences: ... (not usable)"""
showDigClockTr: Final[Option[bool]] = Option(True)

"""Normal Days: Icon Path
Preferences: Appearance: Status Icon"""
statusIconImage: Final[Option[str]] = Option("status-icons/dark-green.svg")

"""Holidays: Icon Path
Preferences: Appearance: Status Icon"""
statusIconImageHoli: Final[Option[str]] = Option("status-icons/dark-red.svg")

"""[ ] Change font family to
Preferences: Appearance: Status Icon"""
statusIconFontFamilyEnable: Final[Option[bool]] = Option(False)

"""Font family
Preferences: Appearance: Status Icon"""
statusIconFontFamily: Final[Option[str | None]] = Option(None)

"""Holiday font color
Preferences: Appearance: Status Icon"""
statusIconHolidayFontColorEnable: Final[Option[bool]] = Option(False)

"""Holiday font color
Preferences: Appearance: Status Icon"""
statusIconHolidayFontColor: Final[Option[ColorType | None]] = Option(None)

"""Localize the number
Preferences: Appearance: Status Icon"""
statusIconLocalizeNumber: Final[Option[bool]] = Option(True)

"""[ ] Fixed Size
Preferences: Appearance: Status Icon"""
statusIconFixedSizeEnable: Final[Option[bool]] = Option(False)

"""Fixed Size (width, height)
Preferences: Appearance: Status Icon"""
statusIconFixedSizeWH: Final[Option[tuple[int, int]]] = Option((24, 24))

"""Show in Status Icon (for today)
Preferences: Plugins"""
pluginsTextStatusIcon: Final[Option[bool]] = Option(False)

"""Days maximum cache size
Preferences: Advanced
Valid: IntSpin(100, 9999, 10)"""
maxDayCacheSize: Final[Option[int]] = Option(100)

"""Event Time Format
Preferences: Advanced"""
eventDayViewTimeFormat: Final[Option[str]] = Option("HM$")

"""Horizontal offset for day right-click menu
Preferences: Advanced
Valid: IntSpin(0, 999, 1)"""
cellMenuXOffset: Final[Option[int]] = Option(0)

"""Enable
MainWin: Customize: Window Controller"""
winControllerEnable: Final[Option[bool]] = Option(True)

"""Theme
MainWin: Customize: Window Controller"""
winControllerTheme: Final[Option[str]] = Option("default")

"""Buttons
MainWin: Customize: Window Controller"""
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

"""Icon Size
MainWin: Customize: Window Controller
Valid: IntSpin(5, 128, 1)"""
winControllerIconSize: Final[Option[int]] = Option(24)

"""Buttons Border
MainWin: Customize: Window Controller
Valid: IntSpin(0, 99, 1)"""
winControllerBorder: Final[Option[int]] = Option(0)

"""Space between buttons
MainWin: Customize: Window Controller
Valid: IntSpin(0, 99, 1)"""
winControllerSpacing: Final[Option[int]] = Option(0)

"""Change icon on button press
MainWin: Customize: Window Controller"""
winControllerPressState: Final[Option[bool]] = Option(False)

"""Enable
MainWin: Customize: Right Panel"""
mainWinRightPanelEnable: Final[Option[bool]] = Option(True)

"""Ration of height of upper half to the whole
MainWin: Right Panel"""
mainWinRightPanelRatio: Final[Option[float]] = Option(0.5)

"""Swap Plugins Text and Events Text
MainWin: Right Panel: Context menu"""
mainWinRightPanelSwap: Final[Option[bool]] = Option(False)

"""Width: Fixed width
MainWin: Customize: Right Panel: Sizes
Valid: IntSpin(1, 9999, 10)"""
mainWinRightPanelWidth: Final[Option[int]] = Option(200)

"""Width: Relative to window
MainWin: Customize: Right Panel: Sizes
Valid: FloatSpin(0, 1, 0.01, 3)"""
mainWinRightPanelWidthRatio: Final[Option[float]] = Option(0.25)

"""Width: Relative to window
MainWin: Customize: Right Panel: Sizes"""
mainWinRightPanelWidthRatioEnable: Final[Option[bool]] = Option(True)

"""Font
MainWin: Customize: Right Panel: Events Text"""
mainWinRightPanelEventFontEnable: Final[Option[bool]] = Option(False)

"""Font
MainWin: Customize: Right Panel: Events Text"""
mainWinRightPanelEventFont: Final[Option[Font | None]] = Option(None)

"""Time Font
MainWin: Customize: Right Panel: Events Text"""
mainWinRightPanelEventTimeFontEnable: Final[Option[bool]] = Option(False)

"""Time Font
MainWin: Customize: Right Panel: Events Text"""
mainWinRightPanelEventTimeFont: Final[Option[Font | None]] = Option(None)

"""Text Alignment
MainWin: Customize: Right Panel: Events Text"""
mainWinRightPanelEventJustification: Final[Option[str]] = Option("left")

"""Event Text Separator
MainWin: Customize: Right Panel: Events Text"""
mainWinRightPanelEventSep: Final[Option[str]] = Option("\n\n")

"""Font
MainWin: Customize: Right Panel: Plugins Text"""
mainWinRightPanelPluginsFontEnable: Final[Option[bool]] = Option(False)

"""Font
MainWin: Customize: Right Panel: Plugins Text"""
mainWinRightPanelPluginsFont: Final[Option[Font | None]] = Option(None)

"""Text Alignment
MainWin: Customize: Right Panel: Plugins Text"""
mainWinRightPanelPluginsJustification: Final[Option[str]] = Option("left")

"""Resize on show/hide from window controller
MainWin: Customize: Right Panel"""
mainWinRightPanelResizeOnToggle: Final[Option[bool]] = Option(True)

"""Border Width
MainWin: Customize: Right Panel
Valid: IntSpin(0, 999, 1)"""
mainWinRightPanelBorderWidth: Final[Option[int]] = Option(7)

"""Left Margin
MainWin: Customize: Month Calendar
Valid: IntSpin(0, 999, 1)"""
mcalLeftMargin: Final[Option[int]] = Option(30)

"""Top Margin
MainWin: Customize: Month Calendar
Valid: IntSpin(0, 999, 1)"""
mcalTopMargin: Final[Option[int]] = Option(30)

"""Calendar Types Options
MainWin: Customize: Month Calendar"""
mcalTypeParams: Final[ListOption[CalTypeOptionsDict]] = ListOption(
	[
		{"pos": (0, -2), "font": None, "color": (220, 220, 220)},
		{"pos": (18, 5), "font": None, "color": (165, 255, 114)},
		{"pos": (-18, 4), "font": None, "color": (0, 200, 205)},
	]
)

"""Grid
MainWin: Customize: Month Calendar"""
mcalGrid: Final[Option[bool]] = Option(False)

"""Grid Color
MainWin: Customize: Month Calendar"""
mcalGridColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=252, blue=0, alpha=82)
)

"""Corner Menu Text Color
MainWin: Customize: Month Calendar"""
mcalCornerMenuTextColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=255, blue=255, alpha=255)
)

"""Line Width Factor
MainWin: Customize: Month Calendar: Cursor
Valid: FloatSpin(0, 1, 0.1, 2)"""
mcalCursorLineWidthFactor: Final[Option[float]] = Option(0.12)

"""Rounding Factor
MainWin: Customize: Month Calendar: Cursor
Valid: FloatSpin(0, 1, 0.1, 2)"""
mcalCursorRoundingFactor: Final[Option[float]] = Option(0.5)

"""Text Size Scale
MainWin: Customize: Week Calendar
Valid: FloatSpin(0.01, 1, 0.1, 3)"""
wcalTextSizeScale: Final[Option[float]] = Option(0.6)

"""Items
MainWin: Customize: Week Calendar"""
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

"""Grid
MainWin: Customize: Week Calendar"""
wcalGrid: Final[Option[bool]] = Option(False)

"""Grid Color
MainWin: Customize: Week Calendar"""
wcalGridColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=252, blue=0, alpha=82)
)

"""Row's Upper Gradient
MainWin: Customize: Week Calendar"""
wcalUpperGradientEnable: Final[Option[bool]] = Option(False)

"""Row's Upper Gradient
MainWin: Customize: Week Calendar"""
wcalUpperGradientColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=255, blue=255, alpha=60)
)

"""Past Event Color
MainWin: Customize: Week Calendar: Columns: Events Text"""
wcal_eventsText_pastColorEnable: Final[Option[bool]] = Option(False)

"""Past Event Color
MainWin: Customize: Week Calendar: Columns: Events Text"""
wcal_eventsText_pastColor: Final[Option[ColorType]] = Option(
	RGBA(red=100, green=100, blue=100, alpha=50)
)

"""Ongoing Event Color
MainWin: Customize: Week Calendar: Columns: Events Text"""
wcal_eventsText_ongoingColorEnable: Final[Option[bool]] = Option(False)

"""Ongoing Event Color
MainWin: Customize: Week Calendar: Columns: Events Text"""
wcal_eventsText_ongoingColor: Final[Option[ColorType]] = Option(
	RGBA(red=80, green=255, blue=80, alpha=255)
)

"""Show Description
MainWin: Customize: Week Calendar: Columns: Events Text"""
wcal_eventsText_showDesc: Final[Option[bool]] = Option(False)

"""Use color of event group for event text
MainWin: Customize: Week Calendar: Columns: """
wcal_eventsText_colorize: Final[Option[bool]] = Option(True)

"""Font Family
MainWin: Customize: Week Calendar: Columns: """
wcalFont_eventsText: Final[Option[str | None]] = Option(None)

"""Week number is negated by clicking
MainWin: Week Calendar: Toolbar"""
wcal_toolbar_weekNum_negative: Final[Option[bool]] = Option(False)

"""Icon
MainWin: Customize: Week Calendar: Columns: Toolbar: Main Menu"""
wcal_toolbar_mainMenu_icon: Final[Option[str]] = Option("starcal.png")

"""Width
MainWin: Customize: Week Calendar: Columns: Week Days"""
wcal_weekDays_width: Final[Option[int]] = Option(80)

"""Expand
MainWin: Customize: Week Calendar: Columns: Week Days"""
wcal_weekDays_expand: Final[Option[bool]] = Option(False)

"""Font Family
MainWin: Customize: Week Calendar: Columns: Week Days"""
wcalFont_weekDays: Final[Option[str | None]] = Option(None)

"""Font Family
MainWin: Customize: Week Calendar: Columns: Plugins Text"""
wcalFont_pluginsText: Final[Option[str | None]] = Option(None)

"""Only first line of text
MainWin: Customize: Week Calendar: Columns: Plugins Text"""
wcal_pluginsText_firstLineOnly: Final[Option[bool]] = Option(False)

"""Width
MainWin: Customize: Week Calendar: Columns: Events Icon"""
wcal_eventsIcon_width: Final[Option[int]] = Option(50)

"""Font (for each calendar type)
MainWin: Customize: Week Calendar: Columns: Days of Month"""
wcalTypeParams: Final[ListOption[WeekCalDayNumOptionsDict]] = ListOption(
	[{"font": None}, {"font": None}, {"font": None}]
)

"""Direction
MainWin: Customize: Week Calendar: Columns: Days of Month"""
wcal_daysOfMonth_dir: Final[Option[str]] = Option("ltr")

"""Width
MainWin: Customize: Week Calendar: Columns: Days of Month"""
wcal_daysOfMonth_width: Final[Option[int]] = Option(30)

"""Width
MainWin: Customize: Week Calendar: Columns: """
wcal_daysOfMonth_expand: Final[Option[bool]] = Option(False)

"""Width
MainWin: Customize: Week Calendar: Columns: """
wcal_eventsCount_width: Final[Option[int]] = Option(80)

"""Expand
MainWin: Customize: Week Calendar: Columns: """
wcal_eventsCount_expand: Final[Option[bool]] = Option(False)

"""Font Family
MainWin: Customize: Week Calendar: Columns: Events Box"""
wcalFont_eventsBox: Final[Option[str | None]] = Option(None)

"""Width
MainWin: Customize: Week Calendar: Columns: Moon Status"""
wcal_moonStatus_width: Final[Option[int]] = Option(48)

"""Southern Hemisphere
MainWin: Customize: Week Calendar: Columns: Moon Status"""
wcal_moonStatus_southernHemisphere: Final[Option[bool]] = Option(False)

"""Line Width Factor
MainWin: Customize: Week Calendar: Cursor
Valid: FloatSpin(0, 1, 0.1, 2)"""
wcalCursorLineWidthFactor: Final[Option[float]] = Option(0.12)

"""Rounding Factor
MainWin: Customize: Week Calendar: Cursor
Valid: FloatSpin(0, 1, 0.1, 2)"""
wcalCursorRoundingFactor: Final[Option[float]] = Option(0.5)

"""Widget buttons
MainWin: Customize: Day Calendar: Buttons"""
dcalWidgetButtonsEnable: Final[Option[bool]] = Option(False)

"""[Enable, Position, Alignment, Font, Color]
MainWin: Customize: Day Calendar: {Calendar Type}"""
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

"""[Enable, Position, Alignment, Font, Color]
MainWin: Customize: Day Calendar: {Calendar Type}: Month Name"""
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

"""[Enable, Position, Alignment, Font, Color]
MainWin: Customize: Day Calendar: Week Day"""
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

"""Navigation buttons
MainWin: Customize: Day Calendar: Buttons"""
dcalNavButtonsEnable: Final[Option[bool]] = Option(True)

"""Navigation Buttons
MainWin: Customize: Day Calendar: Buttons"""
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

"""Navigation Buttons Opacity
MainWin: Customize: Day Calendar: Buttons"""
dcalNavButtonsOpacity: Final[Option[float]] = Option(0.7)

"""Localize
MainWin: Customize: Day Calendar: Week Day"""
dcalWeekdayLocalize: Final[Option[bool]] = Option(True)

"""Abbreviate
MainWin: Customize: Day Calendar: Week Day"""
dcalWeekdayAbbreviate: Final[Option[bool]] = Option(False)

"""Uppercase
MainWin: Customize: Day Calendar: Week Day"""
dcalWeekdayUppercase: Final[Option[bool]] = Option(False)

"""Icon Size
MainWin: Customize: Day Calendar: Events"""
dcalEventIconSize: Final[Option[int]] = Option(20)

"""Total Size Ratio
MainWin: Customize: Day Calendar: Events"""
dcalEventTotalSizeRatio: Final[Option[float]] = Option(0.3)

"""Open desktop widget on start
Preferences: General"""
showDesktopWidget: Final[Option[bool]] = Option(False)

"""Geometry: X
DayCalWin: Move"""
dcalWinX: Final[Option[int]] = Option(0)

"""Geometry: Y
DayCalWin: Move"""
dcalWinY: Final[Option[int]] = Option(0)

"""Geometry: Width
DayCalWin: Resize"""
dcalWinWidth: Final[Option[int]] = Option(180)

"""Geometry: Height
DayCalWin: Resize"""
dcalWinHeight: Final[Option[int]] = Option(180)

"""Background Color
DayCalWin: Customize"""
dcalWinBackgroundColor: Final[Option[ColorType]] = Option(RGB(red=0, green=10, blue=0))

"""Widget buttons
DayCalWin: Customize: Buttons"""
dcalWinWidgetButtonsEnable: Final[Option[bool]] = Option(True)

"""Widget buttons Size
DayCalWin: Customize: Buttons"""
dcalWinWidgetButtonsSize: Final[Option[int]] = Option(16)

"""Widget buttons Opacity
DayCalWin: Customize: Buttons"""
dcalWinWidgetButtonsOpacity: Final[Option[float]] = Option(1.0)

"""Localize
DayCalWin: Customize: Week Day"""
dcalWinWeekdayLocalize: Final[Option[bool]] = Option(True)

"""Abbreviate
DayCalWin: Customize: Week Day"""
dcalWinWeekdayAbbreviate: Final[Option[bool]] = Option(False)

"""Uppercase
DayCalWin: Customize: Week Day"""
dcalWinWeekdayUppercase: Final[Option[bool]] = Option(False)

"""[Enable, Position, Alignment, Font, Color]
DayCalWin: Customize: {Calendar Type}"""
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

"""[Enable, Position, Alignment, Font, Color]
DayCalWin: Customize: {Calendar Type}: Month Name"""
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

"""[Enable, Position, Alignment, Font, Color]
DayCalWin: Customize: Week Day"""
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

"""Icon Size
DayCalWin: Customize: Events"""
dcalWinEventIconSize: Final[Option[int]] = Option(20)

"""Total Size Ratio
DayCalWin: Customize: Events"""
dcalWinEventTotalSizeRatio: Final[Option[float]] = Option(0.3)

"""Enable
DayCalWin: Customize: Season Pie"""
dcalWinSeasonPieEnable: Final[Option[bool]] = Option(False)

"""Geometry
DayCalWin: Customize: Season Pie"""
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

"""Spring Color
DayCalWin: Customize: Season Pie"""
dcalWinSeasonPieSpringColor: Final[Option[ColorType]] = Option(
	RGBA(red=167, green=252, blue=1, alpha=180)
)

"""Summer Color
DayCalWin: Customize: Season Pie"""
dcalWinSeasonPieSummerColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=254, blue=0, alpha=180)
)

"""Autumn Color
DayCalWin: Customize: Season Pie"""
dcalWinSeasonPieAutumnColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=127, blue=0, alpha=180)
)

"""Winter Color
DayCalWin: Customize: Season Pie"""
dcalWinSeasonPieWinterColor: Final[Option[ColorType]] = Option(
	RGBA(red=1, green=191, blue=255, alpha=180)
)

"""Text Color
DayCalWin: Customize: Season Pie"""
dcalWinSeasonPieTextColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=255, blue=255, alpha=180)
)

"""Calendar Type
MainWin: Customize: Main Panel: Month Progress Bar"""
monthPBarCalType: Final[Option[int]] = Option(-1)

"""Southern Hemisphere
MainWin: Customize: Main Panel: Season Progress Bar"""
seasonPBar_southernHemisphere: Final[Option[bool]] = Option(False)

"""Border Width
MainWin: Customize: Main Panel: Year & Month Bar
Valid: IntSpin(0, 99, 1)"""
labelBoxBorderWidth: Final[Option[int]] = Option(0)

"""Active menu item color
MainWin: Customize: Main Panel: Year & Month Bar"""
labelBoxMenuActiveColor: Final[Option[ColorType]] = Option(
	RGBA(red=0, green=255, blue=0, alpha=255)
)

"""Year Color
MainWin: Customize: Main Panel: Year & Month Bar"""
labelBoxYearColorEnable: Final[Option[bool]] = Option(False)

"""Year Color
MainWin: Customize: Main Panel: Year & Month Bar"""
labelBoxYearColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=132, blue=255, alpha=255)
)

"""Month Color
MainWin: Customize: Main Panel: Year & Month Bar"""
labelBoxMonthColorEnable: Final[Option[bool]] = Option(False)

"""Month Color
MainWin: Customize: Main Panel: Year & Month Bar"""
labelBoxMonthColor: Final[Option[ColorType]] = Option(
	RGBA(red=255, green=132, blue=255, alpha=255)
)

"""Font
MainWin: Customize: Main Panel: Year & Month Bar"""
labelBoxFontEnable: Final[Option[bool]] = Option(False)

"""Font
MainWin: Customize: Main Panel: Year & Month Bar"""
labelBoxFont: Final[Option[Font | None]] = Option(None)

"""Primary Calendar Font
MainWin: Customize: Main Panel: Year & Month Bar"""
labelBoxPrimaryFontEnable: Final[Option[bool]] = Option(False)

"""Primary Calendar Font
MainWin: Customize: Main Panel: Year & Month Bar"""
labelBoxPrimaryFont: Final[Option[Font | None]] = Option(None)

"""Bold Font
MainWin: Customize: Main Panel: Year & Month Bar"""
boldYmLabel: Final[Option[bool]] = Option(True)

"""Toolbar Buttons
MainWin: Customize: Main Panel: Week Calendar: Columns/; Toolbar"""
ud__wcalToolbarData: Final[Option[CustomizableToolBoxDict | None]] = Option(None)

"""Toolbar Buttons
MainWin: Customize: Main Panel: Toolbar"""
ud__mainToolbarData: Final[Option[CustomizableToolBoxDict | None]] = Option(None)

"""Preferences Page Path
Preferences"""
preferencesPagePath: Final[Option[str]] = Option("")

"""Customize Page Path
Customize"""
customizePagePath: Final[Option[str]] = Option("")

"""Local Timezone History"""
localTzHist: Final[ListOption[str]] = ListOption([])

"""Show Digital Clock: On Toolbar
Preferences: ... (not usable)"""
showDigClockTb: Final[Option[bool]] = Option(True)

"""Menu Icon Padding"""
menuIconPadding: Final[Option[int]] = Option(7)

"""Event Tree Group Icon Size"""
eventTreeGroupIconSize: Final[Option[int]] = Option(24)

"""Tree Icon Size"""
treeIconSize: Final[Option[int]] = Option(22)

labelBoxIconSize: Final[Option[int]] = Option(20)

stackIconSize: Final[Option[int]] = Option(22)

dcalWidgetButtons: Final[ListOption[DayCalWidgetButtonDict]] = ListOption(
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

dcalWinWidgetButtons: Final[ListOption[DayCalWidgetButtonDict]] = ListOption(
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

"""
Valid: IntSpin(5, 128, 1)"""
rightPanelEventIconSize: Final[Option[int]] = Option(20)

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
