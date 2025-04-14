# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.

from __future__ import annotations

from scal3 import logger

log = logger.get()

import os
import os.path
import typing
from contextlib import suppress
from os.path import isdir, isfile, join
from time import perf_counter
from typing import Any

from scal3 import core, event_lib, locale_man
from scal3.cal_types import calTypes
from scal3.event_notification_thread import EventNotificationManager
from scal3.event_tags import eventTags
from scal3.event_update_queue import EventUpdateQueue
from scal3.font import Font
from scal3.json_utils import (
	loadJsonConf,
	saveJsonConf,
)
from scal3.locale_man import tr as _
from scal3.path import confDir, pixDir, sourceDir, svgDir, sysConfDir
from scal3.ui_funcs import checkEnabledNamesItems
from scal3.ui_params import (
	CUSTOMIZE,
	LIVE,
	MAIN_CONF,
	NEED_RESTART,
	confParamsData,
	getParamNamesWithFlag,
)

if typing.TYPE_CHECKING:
	from scal3.s_object import SObj

# -------------------------------------------------------

__all__ = [
	"Font",
	"bgColor",
	"boldYmLabel",
	"buttonIconEnable",
	"buttonIconSize",
	"cellMenuXOffset",
	"cells",
	"checkMainWinItems",
	"checkNeedRestart",
	"checkWinControllerButtons",
	"customizePagePath",
	"dayCalWin",
	"disableRedraw",
	"dragGetCalType",
	"duplicateGroupTitle",
	"eventAccounts",
	"eventGroups",
	"eventManDialog",
	"eventNotif",
	"eventSearchWin",
	"eventTags",
	"eventTrash",
	"eventUpdateQueue",
	"eventViewMaxHeight",
	"eventWeekViewTimeFormat",
	"focusTime",
	"fontCustom",
	"fontDefault",
	"getActiveMonthCalParams",
	"getEvent",
	"getFont",
	"holidayColor",
	"init",
	"initFonts",
	"iterAllEvents",
	"labelBoxFont",
	"labelBoxFontEnable",
	"labelBoxMonthColorEnable",
	"labelBoxPrimaryFont",
	"labelBoxPrimaryFontEnable",
	"labelBoxYearColorEnable",
	"labelMenuDelay",
	"lastLiveConfChangeTime",
	"localTzHist",
	"mainWin",
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
	"menuCheckSize",
	"menuIconEdgePadding",
	"menuIconSize",
	"monthPBarCalType",
	"monthRMenuNum",
	"moveEventToTrash",
	"ntpServers",
	"oldStyleProgressBar",
	"pluginsTextStatusIcon",
	"prefWindow",
	"saveConf",
	"saveConfCustomize",
	"saveLiveConf",
	"saveLiveConfDelay",
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
	"timeLineWin",
	"timeout_repeat",
	"toolbarIconSize",
	"updateFocusTime",
	"useAppIndicator",
	"useSystemIcons",
	"wcalCursorLineWidthFactor",
	"wcalCursorRoundingFactor",
	"wcalEventIconSizeMax",
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
	"withFS",
	"yearWheelWin",
]


sysConfPath = join(sysConfDir, "ui.json")  # also includes LIVE config

confPath = join(confDir, "ui.json")

confPathCustomize = join(confDir, "ui-customize.json")

confPathLive = join(confDir, "ui-live.json")


confParams = getParamNamesWithFlag(MAIN_CONF)
confParamsLive = getParamNamesWithFlag(LIVE)
confParamsCustomize = getParamNamesWithFlag(CUSTOMIZE)
# print(f"confParams = {sorted(confParams)}")
# print(f"confParamsLive = {sorted(confParamsLive)}")
# print(f"confParamsCustomize = {sorted(confParamsCustomize)}")


fontParams = ["fontDefault"] + [p.v3Name for p in confParamsData if p.type == Font]

confDecoders = dict.fromkeys(fontParams, Font.fromList)
confEncoders = {
	# param: Font.to_json for param in fontParams
}


def loadConf() -> None:
	loadJsonConf(
		__name__,
		sysConfPath,
		decoders=confDecoders,
	)
	loadJsonConf(
		__name__,
		confPath,
		decoders=confDecoders,
	)
	loadJsonConf(
		__name__,
		confPathCustomize,
		decoders=confDecoders,
	)
	loadJsonConf(
		__name__,
		confPathLive,
		decoders=confDecoders,
	)


def saveConf() -> None:
	saveJsonConf(
		__name__,
		confPath,
		confParams,
		encoders=confEncoders,
	)


def saveConfCustomize() -> None:
	saveJsonConf(
		__name__,
		confPathCustomize,
		confParamsCustomize,
		encoders=confEncoders,
	)


def saveLiveConf() -> None:  # rename to saveConfLive FIXME
	log.debug(f"saveLiveConf: {winX=}, {winY=}, {winWidth=}")
	saveJsonConf(
		__name__,
		confPathLive,
		confParamsLive,
		encoders=confEncoders,
	)


def saveLiveConfLoop() -> None:  # rename to saveConfLiveLoop FIXME
	tm = perf_counter()
	if tm - lastLiveConfChangeTime > saveLiveConfDelay:
		saveLiveConf()
		return False  # Finish loop
	return True  # Continue loop


# -------------------------------------------------------


# -----------------------------------------------------------------------

# moved to cells.:
# getMonthPlus, changeDate, gotoJd, gotoJd, jdPlus, monthPlus, yearPlus


def getFont(
	scale=1.0,
	family=True,
	bold=False,
) -> tuple[str | None, bool, bool, float]:
	f = fontCustom if fontCustomEnable else fontDefaultInit
	return Font(
		family=f.family if family else None,
		bold=f.bold or bold,
		italic=f.italic,
		size=f.size * scale,
	)


def initFonts(fontDefaultNew: Font) -> None:
	global fontDefault, fontCustom
	fontDefault = fontDefaultNew
	if not fontCustom:
		fontCustom = fontDefault
	# --------
	# ---
	if mcalTypeParams[0]["font"] is None:
		mcalTypeParams[0]["font"] = getFont(1.0, family=False)
	# ---
	for item in mcalTypeParams[1:]:
		if item["font"] is None:
			item["font"] = getFont(0.6, family=False)
	# ------
	if dcalDayParams[0]["font"] is None:
		dcalDayParams[0]["font"] = getFont(10.0, family=False)
	# ---
	for item in dcalDayParams[1:]:
		if item["font"] is None:
			item["font"] = getFont(3.0, family=False)
	# ------
	if dcalMonthParams[0]["font"] is None:
		dcalMonthParams[0]["font"] = getFont(5.0, family=False)
	# ---
	for item in dcalMonthParams[1:]:
		if item["font"] is None:
			item["font"] = getFont(2.0, family=False)
	# ------
	if dcalWinDayParams[0]["font"] is None:
		dcalWinDayParams[0]["font"] = getFont(5.0, family=False)
	# ---
	for item in dcalWinDayParams[1:]:
		if item["font"] is None:
			item["font"] = getFont(2.0, family=False)
	# ------
	if dcalWinMonthParams[0]["font"] is None:
		dcalWinMonthParams[0]["font"] = getFont(2.5, family=False)
	# ---
	for item in dcalWinMonthParams[1:]:
		if item["font"] is None:
			item["font"] = getFont(1.5, family=False)
	# ------
	if dcalWeekdayParams["font"] is None:
		dcalWeekdayParams["font"] = getFont(1.0, family=False)
	if dcalWinWeekdayParams["font"] is None:
		dcalWinWeekdayParams["font"] = getFont(1.0, family=False)


# ----------------------------------------------------------------------


def checkNeedRestart() -> bool:
	for key in needRestartPref:
		if needRestartPref[key] != evalParam(key):
			log.info(
				f"checkNeedRestart: {key!r}, "
				f"{needRestartPref[key]!r}, {evalParam(key)!r}",
			)
			return True
	return False


def checkMainWinItems() -> None:
	global mainWinItems
	mainWinItems = checkEnabledNamesItems(
		mainWinItems,
		mainWinItemsDefault,
	)
	# TODO: make sure there are no duplicates, by removing duplicates


def checkWinControllerButtons() -> None:
	global winControllerButtons
	winControllerButtons = checkEnabledNamesItems(
		winControllerButtons,
		winControllerButtonsDefault,
	)
	# "sep" button can have duplicates


# ----------------------------------------------------------------------


def moveEventToTrash(
	group: event_lib.EventGroup,
	event: event_lib.Event,
	sender,  # write BaseCalType based on BaseCalObj
	save: bool = True,
) -> int:
	eventIndex = group.remove(event)
	eventTrash.add(event)  # or append? FIXME
	if save:
		group.save()
		eventTrash.save()
	eventUpdateQueue.put("-", event, sender)
	return eventIndex


def getEvent(groupId: int, eventId: int) -> event_lib.Event:
	return eventGroups[groupId][eventId]


def duplicateGroupTitle(group: event_lib.EventGroup) -> None:
	title = group.title
	usedTitles = {g.title for g in eventGroups}
	parts = title.split("#")
	try:
		index = int(parts[-1])
		title = "#".join(parts[:-1])
	except (IndexError, ValueError):
		# log.exception("")
		index = 1

	def makeTitle(n: int) -> str:
		return title + "#" + _(n)

	newTitle, index = makeTitle(index), index + 1
	while newTitle in usedTitles:
		newTitle, index = makeTitle(index), index + 1

	group.title = newTitle


# ----------------------------------------------------------------------


def init() -> None:
	global fs, eventAccounts, eventGroups, eventTrash, eventNotif
	core.init()

	fs = core.fs
	event_lib.init(fs)
	# Load accounts, groups and trash? FIXME
	eventAccounts = event_lib.EventAccountsHolder.load(fs)
	eventGroups = event_lib.EventGroupsHolder.load(fs)
	eventTrash = event_lib.EventTrash.load(fs)
	eventNotif = EventNotificationManager(eventGroups)


def withFS(obj: SObj) -> SObj:
	obj.fs = fs
	return obj


# ----------------------------------------------------------------------

localTzHist = []

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

wcalTypeParams = [
	{"font": None},
	{"font": None},
	{"font": None},
]

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

# ------------------------------


def getActiveMonthCalParams():
	return list(
		zip(
			calTypes.active,
			mcalTypeParams,
			strict=False,
		),
	)


# --------------------------------

fs: event_lib.FileSystem | None = None
eventAccounts: list[event_lib.Account] = []
eventGroups: list[event_lib.EventGroup] = []
eventTrash: event_lib.EventTrash | None = None
eventNotif: EventNotificationManager | None = None


def iterAllEvents():  # dosen"t include orphan events
	for group in eventGroups:
		for event in group:
			yield event
	for event in eventTrash:
		yield event


eventUpdateQueue = EventUpdateQueue()

# -------------------
# BUILD CACHE AFTER SETTING calTypes.primary
maxDayCacheSize = 100  # maximum size of cells (days number)
maxWeekCacheSize = 12

cells = None  # FIXME: CellCacheType based on CellCache
# ---------------------------
# appLogo = join(pixDir, "starcal.png")
appLogo = join(svgDir, "starcal.svg")
appIcon = join(pixDir, "starcal-48.png")
# ---------------------------
# themeDir = join(sourceDir, "themes")
# theme = None

# _________________________ Options _________________________ #

# these 2 are loaded from json
ud__wcalToolbarData = None
ud__mainToolbarData = None

winWidth = 480
winHeight = 300

winTaskbar = False
useAppIndicator = True
showDigClockTb = True  # On Toolbar FIXME
showDigClockTr = True  # On Status Icon
# ----
bgColor = (26, 0, 1, 255)  # or None
borderColor = (123, 40, 0, 255)
borderTextColor = (255, 255, 255, 255)  # text of weekDays and weekNumbers
# mcalMenuCellBgColor = borderColor
textColor = (255, 255, 255, 255)
menuTextColor = None  # borderTextColor # FIXME
holidayColor = (255, 160, 0, 255)
inactiveColor = (255, 255, 255, 115)
todayCellColor = (0, 255, 0, 50)
# ----------
cursorOutColor = (213, 207, 0, 255)
cursorBgColor = (41, 41, 41, 255)
# ----------
# menuIconSize: the size of icons in menu items, used only for svg icons
# should be compatible with gtk.IconSize.MENU used in newMenuItem
menuIconSize = 18

menuIconEdgePadding = 3
menuIconPadding = 7

menuCheckSize = 22
menuEventCheckIconSize = 20

buttonIconEnable = True
buttonIconSize = 20

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
mcalEventIconSizeMax = 26

useSystemIcons = False

oldStyleProgressBar = False

# ----------
# cellMenuXOffset: when we were using ImageMenuItem and CheckMenuItem,
# something between 48 and 56 for cellMenuXOffset was good
# but after migrating away from those 2, it's not needed anymore (so zero)
cellMenuXOffset = 0
# ----------
wcalCursorLineWidthFactor = 0.12
wcalCursorRoundingFactor = 0.50
# ---
mcalCursorLineWidthFactor = 0.12
mcalCursorRoundingFactor = 0.50
# ---
mcalGrid = False
mcalGridColor = (255, 252, 0, 82)
# ----------
mcalLeftMargin = 30
mcalTopMargin = 30
# --------------------
wcalTextSizeScale = 0.6  # between 0 and 1
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
wcalFont_eventsText = None
wcalFont_weekDays = None
wcalFont_pluginsText = None
wcalFont_eventsBox = None
wcal_moonStatus_width = 48

# --------------------
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

# --------------------

dcalWeekdayLocalize = True
dcalWeekdayAbbreviate = False
dcalWeekdayUppercase = False

dcalWinWeekdayLocalize = True
dcalWinWeekdayAbbreviate = False
dcalWinWeekdayUppercase = False

# --------------------

dcalEventIconSize = 20
dcalEventTotalSizeRatio = 0.3
# 0.3 means %30 of window size (minimum of window height and width)

dcalWinEventIconSize = 20
dcalWinEventTotalSizeRatio = 0.3
# 0.3 means %30 of window size (minimum of window height and width)

# --------------------

statusBarDatesReverseOrder = False
statusBarDatesColorEnable = False
statusBarDatesColor = (255, 132, 255, 255)

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


# --------------------

boldYmLabel = True

# delay for shift up/down items of menu for right click on YearLabel
labelMenuDelay = 0.1

# --------------------

preferencesPagePath = ""
customizePagePath = ""

# --------------------

statusIconImage = join(sourceDir, "status-icons", "dark-green.svg")
statusIconImageHoli = join(sourceDir, "status-icons", "dark-red.svg")
(
	statusIconImageDefault,
	statusIconImageHoliDefault,
) = (
	statusIconImage,
	statusIconImageHoli,
)
statusIconFontFamilyEnable = False
statusIconFontFamily = None
statusIconHolidayFontColorEnable = False
statusIconHolidayFontColor = None
statusIconLocalizeNumber = True
statusIconFixedSizeEnable = False
statusIconFixedSizeWH = (24, 24)
# --------------------
pluginsTextStatusIcon = False
pluginsTextInsideExpander = True
pluginsTextIsExpanded = True  # effects only if pluginsTextInsideExpander
eventViewMaxHeight = 200
# --------------------
dragGetCalType = core.GREGORIAN  # apply in Pref FIXME
# dragGetDateFormat = "%Y/%m/%d"
dragRecMode = core.GREGORIAN  # apply in Pref FIXME
# --------------------
monthRMenuNum = True
# monthRMenu

_wmDir = join(svgDir, "wm")
winControllerThemeList = [
	name for name in os.listdir(_wmDir) if isdir(join(_wmDir, name))
]

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
winControllerButtonsDefault = winControllerButtons[:]
winControllerIconSize = 24
winControllerBorder = 0
winControllerSpacing = 0
winControllerPressState = False
# --------------------
winKeepAbove = True
winSticky = True
winMaximized = False
winX = 0
winY = 0
# ---
fontDefault = Font(family="Sans", size=12)
fontDefaultInit = fontDefault
fontCustom = None
fontCustomEnable = False
# ---------------------
showMain = True  # Open main window on start (or only goto statusIcon)
showDesktopWidget = False  # Open desktop widget on start
# ---------------------
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

mainWinItemsDefault = mainWinItems[:]

mainWinFooterItems = [
	"pluginsText",
	"eventDayView",
	"statusBar",
]

winControllerEnable = True
statusBarEnable = True
pluginsTextEnable = False
eventDayViewEnable = False
mainWinRightPanelEnable = True


wcalItems: list[tuple[str, bool]] = [
	("toolbar", True),
	("weekDays", True),
	("pluginsText", True),
	("eventsIcon", True),
	("eventsText", True),
	("daysOfMonth", True),
]

wcalItemsDefault = wcalItems.copy()

# --------------------

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
eventDayViewEventSep = "\n"


# options: "HM$", "HMS", "hMS", "hms", "HM", "hm", "hM"
eventDayViewTimeFormat = "HM$"
eventWeekViewTimeFormat = "HM$"


# --------------------

monthPBarCalType = -1

# --------------------

seasonPBar_southernHemisphere = False
wcal_moonStatus_southernHemisphere = False

# --------------------

ntpServers = (
	"pool.ntp.org",
	"ir.pool.ntp.org",
	"asia.pool.ntp.org",
	"europe.pool.ntp.org",
	"north-america.pool.ntp.org",
	"oceania.pool.ntp.org",
	"south-america.pool.ntp.org",
	"ntp.ubuntu.com",
)


# ---------------------

disableRedraw = False
# when set disableRedraw=True, widgets will not re-draw their contents

focusTime = 0
lastLiveConfChangeTime = 0


saveLiveConfDelay = 0.5  # seconds
timeout_initial = 200
timeout_repeat = 50


def updateFocusTime(*_args):
	global focusTime
	focusTime = perf_counter()


def evalParam(param: str) -> Any:
	parts = param.split(".")
	if not parts:
		raise ValueError(f"invalid {param = }")

	if len(parts) == 1:
		return globals()[param]

	value = globals()
	for part in parts:
		if isinstance(value, dict):
			value = value[part]
		else:
			value = getattr(value, part)

	return value


# --------------------------------------------------------

loadConf()

# --------------------------------------------------------

needRestartPref = {
	name: evalParam(name) for name in getParamNamesWithFlag(NEED_RESTART)
}
needRestartPref.update(locale_man.getNeedRestartParams())


if not isfile(statusIconImage):
	statusIconImage = statusIconImageDefault
if not isfile(statusIconImageHoli):
	statusIconImageHoli = statusIconImageHoliDefault


_localTzName = str(locale_man.localTz)
if localTzHist:
	if localTzHist[0] != _localTzName:
		with suppress(ValueError):
			localTzHist.remove(_localTzName)
		localTzHist.insert(0, _localTzName)
		if len(localTzHist) > 10:
			localTzHist = localTzHist[:10]
		saveConf()
else:
	localTzHist.insert(0, _localTzName)
	saveConf()


menuTextColor = menuTextColor or borderTextColor

# ----------------------------------

# move to gtk_ud ? FIXME
mainWin = None
prefWindow = None
eventManDialog = None
eventSearchWin = None
timeLineWin = None
dayCalWin = None
yearWheelWin = None
weekCalWin = None
