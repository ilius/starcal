from os.path import join

from scal3.path import sourceDir

__all__ = [
	"bgColor",
	"boldYmLabel",
	"buttonIconEnable",
	"buttonIconSize",
	"customizePagePath",
	"eventViewMaxHeight",
	"fontCustom",
	"holidayColor",
	"labelBoxFont",
	"labelBoxFontEnable",
	"labelBoxMonthColorEnable",
	"labelBoxPrimaryFont",
	"labelBoxPrimaryFontEnable",
	"labelBoxYearColorEnable",
	"localTzHist",
	"mainWinItems",
	"mainWinRightPanelEnable",
	"mainWinRightPanelResizeOnToggle",
	"mainWinRightPanelSwap",
	"mainWinRightPanelWidth",
	"mainWinRightPanelWidthRatio",
	"mainWinRightPanelWidthRatioEnable",
	"mcalCursorLineWidthFactor",
	"mcalCursorRoundingFactor",
	"mcalEventIconSizeMax",
	"mcalGrid",
	"mcalGridColor",
	"mcalLeftMargin",
	"mcalTopMargin",
	"mcalTypeParams",
	"monthPBarCalType",
	"oldStyleProgressBar",
	"pluginsTextStatusIcon",
	"showDesktopWidget",
	"showMain",
	"statusBarDatesColorEnable",
	"statusBarDatesReverseOrder",
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
	"useAppIndicator",
	"useSystemIcons",
	"wcalCursorLineWidthFactor",
	"wcalCursorRoundingFactor",
	"wcalGrid",
	"wcalItems",
	"wcalPadding",
	"wcalTypeParams",
	"wcalUpperGradientColor",
	"wcalUpperGradientEnable",
	"wcal_eventsText_colorize",
	"wcal_eventsText_pastColor",
	"wcal_eventsText_pastColorEnable",
	"wcal_eventsText_showDesc",
	"wcal_toolbar_weekNum_negative",
	"winControllerButtons",
	"winControllerTheme",
	"winHeight",
	"winMaximized",
	"winSticky",
	"winTaskbar",
	"winWidth",
	"winX",
	"winY",
]


showMain = True  # Open main window on start (or only goto statusIcon)
showDesktopWidget = False  # Open desktop widget on start
winTaskbar = False
winX = 0
winY = 0
winWidth = 480
winHeight = 300
winKeepAbove = True
winSticky = True
winMaximized = False
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
mainWinItemsDefault = mainWinItems.copy()
mainWinFooterItems = [
	"pluginsText",
	"eventDayView",
	"statusBar",
]
# -----------------
useAppIndicator = True
showDigClockTr = True  # On Status Icon
showDigClockTb = True  # On Toolbar FIXME
fontCustomEnable = False
fontCustom = None
buttonIconEnable = True
buttonIconSize = 20  # not in params
useSystemIcons = False
oldStyleProgressBar = False
# ----------------- colors
bgColor = (26, 0, 1, 255)  # or None
borderColor = (123, 40, 0, 255)
borderTextColor = (255, 255, 255, 255)  # text of weekDays and weekNumbers
# mcalMenuCellBgColor = borderColor
textColor = (255, 255, 255, 255)
menuTextColor = None  # borderTextColor # FIXME
holidayColor = (255, 160, 0, 255)
inactiveColor = (255, 255, 255, 115)
todayCellColor = (0, 255, 0, 50)
cursorOutColor = (213, 207, 0, 255)
cursorBgColor = (41, 41, 41, 255)
# ----------------- statusIcon
statusIconImage = join(sourceDir, "status-icons", "dark-green.svg")
statusIconImageHoli = join(sourceDir, "status-icons", "dark-red.svg")
statusIconImageDefault = statusIconImage
statusIconImageHoliDefault = statusIconImageHoli
statusIconFontFamilyEnable = False
statusIconFontFamily = None
statusIconHolidayFontColorEnable = False
statusIconHolidayFontColor = None
statusIconLocalizeNumber = True
statusIconFixedSizeEnable = False
statusIconFixedSizeWH = (24, 24)
pluginsTextStatusIcon = False
# -----------------
maxDayCacheSize = 100  # maximum size of cells (days number)
maxWeekCacheSize = 12
# options: "HM$", "HMS", "hMS", "hms", "HM", "hm", "hM"
eventDayViewTimeFormat = "HM$"
eventWeekViewTimeFormat = "HM$"

preferencesPagePath = ""
customizePagePath = ""

localTzHist = []

# ------------ winController
winControllerEnable = True
winControllerTheme = "default"
winControllerButtons = [
	("sep", True),
	("rightPanel", True),
	("min", True),
	("max", True),
	("close", True),
	("sep", False),
	("sep", False),
	("sep", False),
]
winControllerButtonsDefault = winControllerButtons.copy()
winControllerIconSize = 24
winControllerBorder = 0
winControllerSpacing = 0
winControllerPressState = False
# ------------ rightPanel
mainWinRightPanelEnable = True
mainWinRightPanelSwap = False
mainWinRightPanelWidth = 200
mainWinRightPanelWidthRatio = 0.25
mainWinRightPanelWidthRatioEnable = True
mainWinRightPanelEventJustification = "left"
mainWinRightPanelPluginsJustification = "left"
mainWinRightPanelEventFontEnable = False
mainWinRightPanelEventFont = None
mainWinRightPanelEventTimeFontEnable = False
mainWinRightPanelEventTimeFont = None
mainWinRightPanelPluginsFontEnable = False
mainWinRightPanelPluginsFont = None
mainWinRightPanelBorderWidth = 7
mainWinRightPanelRatio = 0.5  # 0 <= value <= 1
mainWinRightPanelResizeOnToggle = True
mainWinRightPanelEventSep = "\n\n"
# ------------ monthcal
mcalLeftMargin = 30
mcalTopMargin = 30
mcalTypeParams = [
	{
		"pos": (0, -2),
		"font": None,
		"color": (220, 220, 220),
	},
	{
		"pos": (18, 5),
		"font": None,
		"color": (165, 255, 114),
	},
	{
		"pos": (-18, 4),
		"font": None,
		"color": (0, 200, 205),
	},
]
mcalGrid = False
mcalGridColor = (255, 252, 0, 82)
mcalCursorLineWidthFactor = 0.12
mcalCursorRoundingFactor = 0.50
mcalEventIconSizeMax = 26  # not in params
# ------------ weekcal
wcalTextSizeScale = 0.6  # between 0 and 1

wcalCursorLineWidthFactor = 0.12
wcalCursorRoundingFactor = 0.50
# --------------------

# wcalTextColor = (255, 255, 255)  # FIXME
wcalPadding = 10
wcalGrid = False
wcalGridColor = (255, 252, 0, 82)

wcalUpperGradientEnable = False
wcalUpperGradientColor = (255, 255, 255, 60)
# wcalShadowBottomColor = (255, 255, 255, 0)

wcal_eventsText_pastColorEnable = False
wcal_eventsText_pastColor = (100, 100, 100, 50)

wcal_eventsText_ongoingColorEnable = False
wcal_eventsText_ongoingColor = (80, 255, 80, 255)

wcal_toolbar_mainMenu_icon = "starcal.png"
wcal_toolbar_mainMenu_icon_default = wcal_toolbar_mainMenu_icon
wcal_toolbar_weekNum_negative = False
wcal_weekDays_width = 80
wcal_weekDays_expand = False
wcal_eventsCount_width = 80
wcal_eventsCount_expand = False
wcal_eventsIcon_width = 50
wcal_eventsText_showDesc = False
wcal_eventsText_colorize = True
wcal_pluginsText_firstLineOnly = False
wcal_daysOfMonth_width = 30
wcal_daysOfMonth_expand = False
wcal_daysOfMonth_dir = "ltr"  # ltr/rtl/auto
wcalTypeParams = [
	{"font": None},
	{"font": None},
	{"font": None},
]
wcalFont_eventsText = None
wcalFont_weekDays = None
wcalFont_pluginsText = None
wcalFont_eventsBox = None
wcal_moonStatus_width = 48
wcalItems: list[tuple[str, bool]] = [
	("toolbar", True),
	("weekDays", True),
	("pluginsText", True),
	("eventsIcon", True),
	("eventsText", True),
	("daysOfMonth", True),
]
wcalItemsDefault = wcalItems.copy()
# ------------ daycal
dcalWidgetButtonsEnable = False
dcalWidgetButtons = [
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

dcalWinX = 0
dcalWinY = 0
dcalWinWidth = 180
dcalWinHeight = 180
dcalWinBackgroundColor = (0, 10, 0)
dcalWinWidgetButtonsEnable = True
dcalWinWidgetButtons = [
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


dcalWeekdayLocalize = True
dcalWeekdayAbbreviate = False
dcalWeekdayUppercase = False

dcalWinWeekdayLocalize = True
dcalWinWeekdayAbbreviate = False
dcalWinWeekdayUppercase = False


dcalEventIconSize = 20
dcalEventTotalSizeRatio = 0.3
# 0.3 means %30 of window size (minimum of window height and width)

dcalWinEventIconSize = 20
dcalWinEventTotalSizeRatio = 0.3
# 0.3 means %30 of window size (minimum of window height and width)

dcalDayParams = [  # FIXME
	{
		"enable": True,
		"pos": (0, -12),
		"font": None,
		"color": (220, 220, 220),
	},
	{
		"enable": True,
		"pos": (125, 30),
		"font": None,
		"color": (165, 255, 114),
	},
	{
		"enable": True,
		"pos": (-125, 24),
		"font": None,
		"color": (0, 200, 205),
	},
]

dcalMonthParams = [  # FIXME
	{
		"enable": False,
		"pos": (0, -12),  # FIXME
		"xalign": "center",
		"yalign": "center",
		"font": None,
		"color": (220, 220, 220),
		"abbreviate": False,
		"uppercase": False,
	},
	{
		"enable": False,
		"pos": (125, 30),  # FIXME
		"xalign": "center",
		"yalign": "center",
		"font": None,
		"color": (165, 255, 114),
		"abbreviate": False,
		"uppercase": False,
	},
	{
		"enable": False,
		"pos": (-125, 24),  # FIXME
		"xalign": "center",
		"yalign": "center",
		"font": None,
		"color": (0, 200, 205),
		"abbreviate": False,
		"uppercase": False,
	},
]

dcalWeekdayParams = {
	"enable": False,
	"pos": (20, 10),
	"xalign": "right",
	"yalign": "buttom",
	"font": None,
	"color": (0, 200, 205),
}

dcalNavButtonsEnable = True
dcalNavButtonsGeo = {
	"auto_rtl": True,
	"size": 64,
	"spacing": 10,
	"pos": (0, 20),
	"xalign": "center",
	"yalign": "buttom",
}
dcalNavButtonsOpacity = 0.7

dcalWinDayParams = [
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

dcalWinMonthParams = [
	{
		"enable": False,
		"pos": (0, 5),  # FIXME
		"xalign": "left",
		"yalign": "center",
		"font": None,
		"color": (220, 220, 220),
		"abbreviate": False,
		"uppercase": False,
	},
	{
		"enable": False,
		"pos": (5, 0),  # FIXME
		"xalign": "right",
		"yalign": "top",
		"font": None,
		"color": (165, 255, 114),
		"abbreviate": False,
		"uppercase": False,
	},
	{
		"enable": False,
		"pos": (0, 0),  # FIXME
		"xalign": "right",
		"yalign": "buttom",
		"font": None,
		"color": (0, 200, 205),
		"abbreviate": False,
		"uppercase": False,
	},
]

dcalWinWeekdayParams = {
	"enable": False,
	"pos": (20, 10),
	"xalign": "right",
	"yalign": "buttom",
	"font": None,
	"color": (0, 200, 205),
}

dcalWinSeasonPieEnable = False
dcalWinSeasonPieGeo = {
	"size": 64,
	"thickness": 0.3,  # factor of radius, < 1
	"pos": (0, 0),
	"xalign": "right",
	"yalign": "top",
	"startAngle": 270,  # 0 <= startAngle <= 360
}
dcalWinSeasonPieSpringColor = (167, 252, 1, 180)
dcalWinSeasonPieSummerColor = (255, 254, 0, 180)
dcalWinSeasonPieAutumnColor = (255, 127, 0, 180)
dcalWinSeasonPieWinterColor = (1, 191, 255, 180)
dcalWinSeasonPieTextColor = (255, 255, 255, 180)

# ------------ pluginsText
pluginsTextEnable = False
pluginsTextInsideExpander = True
pluginsTextIsExpanded = True  # effects only if pluginsTextInsideExpander
# ------------ eventDayView
eventDayViewEnable = False
eventDayViewEventSep = "\n"
eventViewMaxHeight = 200
# ------------ progress bars
monthPBarCalType = -1
seasonPBar_southernHemisphere = False
wcal_moonStatus_southernHemisphere = False
# ------------ statusBar
statusBarEnable = True
statusBarDatesReverseOrder = False
statusBarDatesColorEnable = False
statusBarDatesColor = (255, 132, 255, 255)
# ------------
labelBoxBorderWidth = 0
labelBoxMenuActiveColor = (0, 255, 0, 255)
labelBoxYearColorEnable = False
labelBoxYearColor = (255, 132, 255, 255)
labelBoxMonthColorEnable = False
labelBoxMonthColor = (255, 132, 255, 255)
labelBoxFontEnable = False
labelBoxFont = None
labelBoxPrimaryFontEnable = False
labelBoxPrimaryFont = None
boldYmLabel = True
# ------------
# these 2 are loaded from json
ud__wcalToolbarData = None
ud__mainToolbarData = None


# ------------ TODO: to add to params:

# cellMenuXOffset: when we were using ImageMenuItem and CheckMenuItem,
# something between 48 and 56 for cellMenuXOffset was good
# but after migrating away from those 2, it's not needed anymore (so zero)

# menuIconSize: the size of icons in menu items, used only for svg icons
# should be compatible with gtk.IconSize.MENU used in newMenuItem
menuIconSize = 18

menuIconEdgePadding = 3
menuIconPadding = 7

menuCheckSize = 22
menuEventCheckIconSize = 20

# stackIconSize: the size of icons in MyStack pages/buttons,
# used only for svg icons
stackIconSize = 22
eventTreeIconSize = 22
eventTreeGroupIconSize = 24
imageInputIconSize = 32
treeIconSize = 22  # for cells of a general treeview
comboBoxIconSize = 20  # for cells of a general ComboBox
toolbarIconSize = 24
messageDialogIconSize = 48
rightPanelEventIconSize = 20
labelBoxIconSize = 20

wcalEventIconSizeMax = 26
cellMenuXOffset = 0
