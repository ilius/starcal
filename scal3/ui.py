#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from scal3 import logger
log = logger.get()

from time import time as now

import sys
import os
import os.path
from os.path import dirname, join, isfile, isdir, splitext, isabs
from collections import OrderedDict
from collections import namedtuple
from dataclasses import dataclass
from cachetools import LRUCache
from contextlib import suppress

from typing import (
	Any,
	Optional,
	Tuple,
	List,
	Sequence,
	Dict,
	Callable,
	TypeVar,
)

from scal3.utils import toBytes
from scal3.json_utils import *
from scal3.path import *
from scal3.types_starcal import CellType, CompiledTimeFormat

from scal3 import cal_types
from scal3.cal_types import calTypes, jd_to

from scal3 import locale_man
from scal3.locale_man import tr as _
from scal3.locale_man import numDecode


from scal3 import core

from scal3 import event_lib
from scal3.event_update_queue import EventUpdateQueue

uiName = ""


#######################################################

sysConfPath = join(sysConfDir, "ui.json")  # also includes LIVE config

confPath = join(confDir, "ui.json")

confPathCustomize = join(confDir, "ui-customize.json")

confPathLive = join(confDir, "ui-live.json")

confParams = (
	"showMain",
	"showDesktopWidget",
	"winTaskbar",
	"useAppIndicator",
	"showDigClockTr",
	"fontCustomEnable",
	"fontCustom",
	"buttonIconEnable",
	"useSystemIcons",
	"bgColor",
	"borderColor",
	"cursorOutColor",
	"cursorBgColor",
	"todayCellColor",
	"textColor",
	"holidayColor",
	"inactiveColor",
	"borderTextColor",
	"statusIconImage",
	"statusIconImageHoli",
	"statusIconFontFamilyEnable",
	"statusIconFontFamily",
	"statusIconHolidayFontColorEnable",
	"statusIconHolidayFontColor",
	"statusIconFixedSizeEnable",
	"statusIconFixedSizeWH",
	"maxDayCacheSize",
	"eventDayViewTimeFormat",
	"pluginsTextStatusIcon",
	"showYmArrows",
	"preferencesPagePath",
	"localTzHist",  # move to a new file like local-tz.json?
)

confParamsLive = (
	"winX",
	"winY",
	"winWidth",
	"winHeight",
	"winKeepAbove",
	"winSticky",
	"winMaximized",
	"pluginsTextIsExpanded",
	"bgColor",
	"wcal_toolbar_weekNum_negative",
	"mainWinRightPanelRatio",
)

confParamsCustomize = (
	"mainWinItems",
	"mainWinFooterItems",
	"winControllerEnable",
	"statusBarEnable",
	"pluginsTextEnable",
	"eventDayViewEnable",
	"eventViewMaxHeight",
	"mainWinRightPanelEnable",
	"mainWinRightPanelSwap",
	"mainWinRightPanelWidth",
	"mainWinRightPanelWidthRatio",
	"mainWinRightPanelWidthRatioEnable",
	"mainWinRightPanelEventFontEnable",
	"mainWinRightPanelEventFont",
	"mainWinRightPanelEventTimeFontEnable",
	"mainWinRightPanelEventTimeFont",
	"mainWinRightPanelPluginsFontEnable",
	"mainWinRightPanelPluginsFont",
	"mainWinRightPanelEventJustification",
	"mainWinRightPanelPluginsJustification",
	"mainWinRightPanelEventSep",
	"eventDayViewEventSep",
	"mainWinRightPanelBorderWidth",
	"winControllerTheme",
	"winControllerButtons",
	"winControllerIconSize",
	"winControllerBorder",
	"winControllerSpacing",
	"mcalLeftMargin",
	"mcalTopMargin",
	"mcalTypeParams",
	"mcalGrid",
	"mcalGridColor",
	"mcalCursorLineWidthFactor",
	"mcalCursorRoundingFactor",
	"wcalTextSizeScale",
	"wcalItems",
	"wcalGrid",
	"wcalGridColor",
	"wcalUpperGradientEnable",
	"wcalUpperGradientColor",
	"wcal_eventsText_pastColorEnable",
	"wcal_eventsText_pastColor",
	"wcal_eventsText_ongoingColorEnable",
	"wcal_eventsText_ongoingColor",
	"wcal_toolbar_mainMenu_icon",
	"wcal_weekDays_width",
	"wcal_weekDays_expand",
	"wcalFont_weekDays",
	"wcalFont_pluginsText",
	"wcal_eventsIcon_width",
	"wcal_eventsText_showDesc",
	"wcal_eventsText_colorize",
	"wcal_pluginsText_firstLineOnly",
	"wcalFont_eventsText",
	"wcal_daysOfMonth_dir",
	"wcalTypeParams",
	"wcal_daysOfMonth_width",
	"wcal_daysOfMonth_expand",
	"wcal_eventsCount_width",
	"wcal_eventsCount_expand",
	"wcalFont_eventsBox",
	"wcal_moonStatus_width",
	"wcalCursorLineWidthFactor",
	"wcalCursorRoundingFactor",
	"dcalWidgetButtonsEnable",
	# "dcalWidgetButtons",
	"dcalDayParams",
	"dcalMonthParams",
	"dcalWeekdayParams",
	"dcalWinBackgroundColor",
	"dcalWinWidgetButtonsEnable",
	# "dcalWinWidgetButtons",

	"dcalNavButtonsEnable",
	"dcalNavButtonsGeo",
	"dcalNavButtonsOpacity",

	"dcalWeekdayLocalize",
	"dcalWeekdayAbbreviate",
	"dcalWeekdayUppercase",
	"dcalWinWeekdayLocalize",
	"dcalWinWeekdayAbbreviate",
	"dcalWinWeekdayUppercase",

	"dcalEventIconSize",
	"dcalEventTotalSizeRatio",
	"dcalWinDayParams",
	"dcalWinMonthParams",
	"dcalWinWeekdayParams",
	"dcalWinEventIconSize",
	"dcalWinEventTotalSizeRatio",
	"dcalWinSeasonPieEnable",
	"dcalWinSeasonPieGeo",
	"dcalWinSeasonPieSpringColor",
	"dcalWinSeasonPieSummerColor",
	"dcalWinSeasonPieAutumnColor",
	"dcalWinSeasonPieWinterColor",
	"dcalWinSeasonPieTextColor",
	"pluginsTextInsideExpander",
	"monthPBarCalType",
	"seasonPBar_southernHemisphere",
	"wcal_moonStatus_southernHemisphere",
	"statusBarDatesReverseOrder",
	"statusBarDatesColorEnable",
	"statusBarDatesColor",
	"labelBoxBorderWidth",
	"labelBoxMenuActiveColor",
	"labelBoxYearColorEnable",
	"labelBoxYearColor",
	"labelBoxMonthColorEnable",
	"labelBoxMonthColor",
	"labelBoxFontEnable",
	"labelBoxFont",
	"labelBoxPrimaryFontEnable",
	"labelBoxPrimaryFont",
	"boldYmLabel",
	"ud__wcalToolbarData",
	"ud__mainToolbarData",
	"customizePagePath",
)


@dataclass(slots=True)
class Font:
	family: Optional[str]
	bold: bool = False
	italic: bool = False
	size: float = 0

	def fromList(lst: "Optional[List]"):
		if lst is None:
			return
		return Font(*lst)

	def to_json(self):
		return [self.family, self.bold, self.italic, self.size]

	def copy(self):
		return Font(*self.to_json())



fontParams = [
	"fontDefault",
	"fontCustom",
	"labelBoxFont",
	"labelBoxPrimaryFont",
	"mainWinRightPanelEventFont",
	"mainWinRightPanelEventTimeFont",
	"mainWinRightPanelPluginsFont",
]

confDecoders = {
	param: Font.fromList for param in fontParams
}
confEncoders = {
# 	param: Font.to_json for param in fontParams
}

def loadConf() -> None:
	loadModuleJsonConf(__name__)
	loadJsonConf(__name__, confPathCustomize, decoders=confDecoders)
	loadJsonConf(__name__, confPathLive, decoders=confDecoders)


def saveConf() -> None:
	saveModuleJsonConf(__name__)


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
	tm = now()
	if tm - lastLiveConfChangeTime > saveLiveConfDelay:
		saveLiveConf()
		return False  # Finish loop
	return True  # Continue loop


#######################################################

def parseDroppedDate(text) -> Optional[Tuple[int, int, int]]:
	part = text.split("/")
	if len(part) != 3:
		return None
	try:
		part[0] = numDecode(part[0])
		part[1] = numDecode(part[1])
		part[2] = numDecode(part[2])
	except ValueError:
		log.exception("")
		return
	maxPart = max(part)
	if maxPart <= 999:
		valid = 0 <= part[0] <= 99 and \
			1 <= part[1] <= 12 and \
			1 <= part[2] <= 31
		if not valid:
			return
		return (
			2000 + part[0],
			part[1],
			part[2],
		)

	minMax = (
		(1000, 2100),
		(1, 12),
		(1, 31),
	)
	formats = (
		[0, 1, 2],
		[1, 2, 0],
		[2, 1, 0],
	)
	# "format" must be list because we use method "index"

	def formatIsValid(fmt: "List[int]"):
		for i in range(3):
			f = fmt[i]
			if not (minMax[f][0] <= part[i] <= minMax[f][1]):
				return False
		return True

	for fmt in formats:
		if formatIsValid(fmt):
			return (
				part[fmt.index(0)],
				part[fmt.index(1)],
				part[fmt.index(2)],
			)

	# FIXME: when drag from a persian GtkCalendar with format %y/%m/%d
	# if year < 100:
	# 	year += 2000


def checkNeedRestart() -> bool:
	for key in needRestartPref.keys():
		if needRestartPref[key] != eval(key):
			log.info(
				f"checkNeedRestart: {key!r}, "
				f"{needRestartPref[key]!r}, {eval(key)!r}"
			)
			return True
	return False


def dayOpenEvolution(arg: Any = None) -> None:
	from subprocess import Popen
	# y, m, d = jd_to(cell.jd-1, core.GREGORIAN)
	# in gnome-cal opens prev day! why??
	y, m, d = cell.dates[core.GREGORIAN]
	Popen(
		f"LANG=en_US.UTF-8 evolution calendar:///?startdate={y:04d}{m:02d}{d:02d}",
		shell=True,
	)  # FIXME
	# f"calendar:///?startdate={y:04d}{m:02d}{d:02d}T120000Z"
	# What "Time" pass to evolution?
	# like gnome-clock: T193000Z (19:30:00) / Or ignore "Time"
	# evolution calendar:///?startdate=$(date +"%Y%m%dT%H%M%SZ")


# How do this with KOrginizer? FIXME

#######################################################################


class Cell(CellType):
	"""
	status and information of a cell
	"""
	# ocTimeMax = 0
	# ocTimeCount = 0
	# ocTimeSum = 0
	def __init__(self, jd: int):
		self._eventsData = None  # type: Optional[List[Dict]]
		self._pluginsText = []  # type: List[List[str]]
		self._pluginsData = []  # List[Tuple[?,?]]
		###
		self.jd = jd
		date = core.jd_to_primary(jd)
		self.year, self.month, self.day = date
		self.weekDay = core.jwday(jd)
		self.weekNum = core.getWeekNumber(self.year, self.month, self.day)
		# self.weekNumNeg = self.weekNum+1 - core.getYearWeeksCount(self.year)
		self.weekNumNeg = self.weekNum - int(
			calTypes.primaryModule().avgYearLen / 7
		)
		self.holiday = (self.weekDay in core.holidayWeekDays)
		###################
		self.dates = [
			date if calType == calTypes.primary else jd_to(jd, calType)
			for calType in range(len(calTypes))
		]
		"""
		self.dates = dict([
			(
				calType, date if calType==calTypes.primary else jd_to(jd, calType)
			)
			for calType in calTypes.active
		])
		"""
		###################
		for k in core.plugIndex:
			plug = core.allPlugList[k]
			if plug:
				try:
					plug.updateCell(self)
				except Exception:
					log.exception("")
		###################
		self.getEventsData()

	def addPluginText(self, plug, text):
		self._pluginsText.append(text.split("\n"))
		self._pluginsData.append((plug, text))

	def getPluginsData(
		self,
		firstLineOnly=False,
	) -> "List[Tuple[BasePlugin, str]]":
		return [
			(plug, text.split("\n")[0]) if firstLineOnly
			else (plug, text)
			for (plug, text) in self._pluginsData
		]

	def getPluginsText(self, firstLineOnly=False) -> str:
		return "\n".join(
			text
			for (plug, text) in self.getPluginsData(firstLineOnly)
		)

	def clearEventsData(self):
		self._eventsData = None

	def getEventsData(self):
		if self._eventsData is not None:
			return self._eventsData
		# t0 = now()
		self._eventsData = event_lib.getDayOccurrenceData(
			self.jd,
			eventGroups,
			tfmt=eventDayViewTimeFormat,
		)
		return self._eventsData
		"""
		self._eventsData is a list, each item is a dictionary
		with these keys and type:
			time: str (time descriptive string)
			time_epoch: int (epoch time)
			is_allday: bool
			text: tuple of text lines
			icon: str (icon path)
			color: tuple (r, g, b) or (r, g, b, a)
			ids: tuple (gid, eid)
			show: tuple of 3 bools (showInDCal, showInWCal, showInMCal)
			showInStatusIcon: bool
		"""
		# dt = now() - t0
		# Cell.ocTimeSum += dt
		# Cell.ocTimeCount += 1
		# Cell.ocTimeMax = max(Cell.ocTimeMax, dt)

	def format(
		self,
		compiledFmt: CompiledTimeFormat,
		calType: Optional[int] = None,
		tm: Optional[Tuple[int, int, int]] = None,
	):
		if calType is None:
			calType = calTypes.primary
		if tm is None:
			tm = (0, 0, 0)
		pyFmt, funcs = compiledFmt
		return pyFmt % tuple(f(self, calType, tm) for f in funcs)

	def getDate(self, calType: int) -> Tuple[int, int, int]:
		return self.dates[calType]

	def inSameMonth(self, other: CellType) -> bool:
		return self.getDate(calTypes.primary)[:2] == \
			other.getDate(calTypes.primary)[:2]

	def getEventIcons(self, showIndex: int) -> List[str]:
		iconList = []
		for item in self.getEventsData():
			if not item.show[showIndex]:
				continue
			icon = item.icon
			if icon and icon not in iconList:
				iconList.append(icon)
		return iconList

	def getDayEventIcons(self) -> List[str]:
		return self.getEventIcons(0)

	def getWeekEventIcons(self) -> List[str]:
		return self.getEventIcons(1)

	def getMonthEventIcons(self) -> List[str]:
		return self.getEventIcons(2)


# I can't find the correct syntax for this `...`
# CellPluginsType = Dict[str, Tuple[
# 	Callable[[CellType], None],
# 	Callable[[CellCache, ...], List[CellType]]
# ]]


class CellCache:
	def __init__(self) -> None:
		# a mapping from julan_day to Cell instance
		self.resetCache()
		self.plugins = {}  # disabled type: CellPluginsType

	def resetCache(self):
		log.debug(f"resetCache: {maxDayCacheSize=}, {maxWeekCacheSize=}")

		# key: jd(int), value: CellType
		self.jdCells = LRUCache(maxsize=maxDayCacheSize)

		# key: absWeekNumber(int), value: List[Dict]
		self.weekEvents = LRUCache(maxsize=maxWeekCacheSize)

	def clear(self) -> None:
		global cell, todayCell
		self.resetCache()
		cell = self.getCell(cell.jd)
		todayCell = self.getCell(todayCell.jd)

	def clearEventsData(self):
		for tmpCell in self.jdCells.values():
			tmpCell.clearEventsData()
		cell.clearEventsData()
		todayCell.clearEventsData()
		self.weekEvents = LRUCache(maxsize=maxWeekCacheSize)

	def registerPlugin(
		self,
		name: str,
		setParamsCallable: Callable[[CellType], None],
		getCellGroupCallable: "Callable[[CellCache, ...], List[CellType]]",
		# ^ FIXME: ...
		# `...` is `absWeekNumber` for weekCal, and `year, month` for monthCal
	):
		"""
			setParamsCallable(cell): cell.attr1 = value1 ....
			getCellGroupCallable(cellCache, *args): return cell_group
				call cellCache.getCell(jd) inside getCellGroupFunc
		"""
		self.plugins[name] = (
			setParamsCallable,
			getCellGroupCallable,
		)
		for localCell in self.jdCells.values():
			setParamsCallable(localCell)

	def getCell(self, jd: int) -> CellType:
		c = self.jdCells.get(jd)
		if c is not None:
			return c
		return self.buildCell(jd)

	def getTmpCell(self, jd: int) -> CellType:
		# don't keep, no eventsData, no plugin params
		c = self.jdCells.get(jd)
		if c is not None:
			return c
		return Cell(jd)

	def getCellByDate(self, y: int, m: int, d: int) -> CellType:
		return self.getCell(core.primary_to_jd(y, m, d))

	def getTodayCell(self) -> CellType:
		return self.getCell(core.getCurrentJd())

	def buildCell(self, jd: int) -> CellType:
		localCell = Cell(jd)
		for pluginData in self.plugins.values():
			pluginData[0](localCell)
		self.jdCells[jd] = localCell
		return localCell

	def getCellGroup(self, pluginName: int, *args) -> List[CellType]:
		return self.plugins[pluginName][1](self, *args)

	def getWeekData(
		self,
		absWeekNumber: int,
	) -> Tuple[List[CellType], List[Dict]]:
		cells = self.getCellGroup("WeekCal", absWeekNumber)
		wEventData = self.weekEvents.get(absWeekNumber)
		if wEventData is None:
			wEventData = event_lib.getWeekOccurrenceData(
				absWeekNumber,
				eventGroups,
				tfmt=eventWeekViewTimeFormat,
			)
			self.weekEvents[absWeekNumber] = wEventData
			# log.info(f"weekEvents cache: {len(self.weekEvents)}")
		return cells, wEventData

	# def getMonthData(self, year, month):  # needed? FIXME


def changeDate(
	year: int,
	month: int,
	day: int,
	calType: Optional[int] = None,
) -> None:
	global cell
	if calType is None:
		calType = calTypes.primary
	cell = cellCache.getCell(core.to_jd(year, month, day, calType))


def gotoJd(jd: int) -> None:
	global cell
	cell = cellCache.getCell(jd)


def jdPlus(plus: int = 1) -> None:
	global cell
	cell = cellCache.getCell(cell.jd + plus)


def getMonthPlus(tmpCell: CellType, plus: int) -> CellType:
	year, month = core.monthPlus(tmpCell.year, tmpCell.month, plus)
	day = min(tmpCell.day, cal_types.getMonthLen(year, month, calTypes.primary))
	return cellCache.getCellByDate(year, month, day)


def monthPlus(plus: int = 1) -> None:
	global cell
	cell = getMonthPlus(cell, plus)


def yearPlus(plus: int = 1) -> None:
	global cell
	year = cell.year + plus
	month = cell.month
	day = min(cell.day, cal_types.getMonthLen(year, month, calTypes.primary))
	cell = cellCache.getCellByDate(year, month, day)


def getFont(
	scale=1.0,
	family=True,
	bold=False,
) -> Tuple[Optional[str], bool, bool, float]:
	f = fontCustom if fontCustomEnable else fontDefaultInit
	return Font(
		family=f.family if family else None,
		bold=f.bold or bold,
		italic=f.italic,
		size=f.size * scale,
	)


def getParamsFont(params: Dict) -> Optional[Font]:
	font = params.get("font")
	if not font:
		return None
	if not isinstance(font, Font):
		font = Font(*font)
	if font.family is None:
		font.family = getFont().family
	return font


def initFonts(fontDefaultNew: "Font") -> None:
	global fontDefault, fontCustom, mcalTypeParams
	fontDefault = fontDefaultNew
	if not fontCustom:
		fontCustom = fontDefault
	########
	###
	if mcalTypeParams[0]["font"] is None:
		mcalTypeParams[0]["font"] = getFont(1.0, family=False)  # noqa: FURB120
	###
	for item in mcalTypeParams[1:]:
		if item["font"] is None:
			item["font"] = getFont(0.6, family=False)
	######
	if dcalDayParams[0]["font"] is None:
		dcalDayParams[0]["font"] = getFont(10.0, family=False)
	###
	for item in dcalDayParams[1:]:
		if item["font"] is None:
			item["font"] = getFont(3.0, family=False)
	######
	if dcalMonthParams[0]["font"] is None:
		dcalMonthParams[0]["font"] = getFont(5.0, family=False)
	###
	for item in dcalMonthParams[1:]:
		if item["font"] is None:
			item["font"] = getFont(2.0, family=False)
	######
	if dcalWinDayParams[0]["font"] is None:
		dcalWinDayParams[0]["font"] = getFont(5.0, family=False)
	###
	for item in dcalWinDayParams[1:]:
		if item["font"] is None:
			item["font"] = getFont(2.0, family=False)
	######
	if dcalWinMonthParams[0]["font"] is None:
		dcalWinMonthParams[0]["font"] = getFont(2.5, family=False)
	###
	for item in dcalWinMonthParams[1:]:
		if item["font"] is None:
			item["font"] = getFont(1.5, family=False)
	######
	if dcalWeekdayParams["font"] is None:
		dcalWeekdayParams["font"] = getFont(1.0, family=False)  # noqa: FURB120
	if dcalWinWeekdayParams["font"] is None:
		dcalWinWeekdayParams["font"] = getFont(1.0, family=False)  # noqa: FURB120


def getHolidaysJdList(startJd: int, endJd: int) -> List[int]:
	jdList = []
	for jd in range(startJd, endJd):
		tmpCell = cellCache.getTmpCell(jd)
		if tmpCell.holiday:
			jdList.append(jd)
	return jdList


######################################################################

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


def checkEnabledNamesItems(
	items: List[Tuple[bool, str]],
	itemsDefault: List[Tuple[bool, str]],
) -> List[Tuple[bool, str]]:
	# cleaning and updating items
	names = {
		name
		for (name, i) in items
	}
	defaultNames = {
		name
		for (name, i) in itemsDefault
	}
	#####
	# removing items that are no longer supported
	items, itemsTmp = [], items
	for name, enable in itemsTmp:
		if name in defaultNames:
			items.append((name, enable))
	#####
	# adding items newly added in this version, this is for user"s convenience
	newNames = defaultNames.difference(names)
	log.debug(f"items: {newNames = }")
	##
	for name in newNames:
		items.append((name, False))  # FIXME
	return items


def moveEventToTrash(
	group: event_lib.EventGroup,
	event: event_lib.Event,
	sender: "BaseCalObj",
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
	usedTitles = set(g.title for g in eventGroups)
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


def init() -> None:
	global todayCell, cell, fs, eventAccounts, eventGroups, eventTrash
	core.init()

	fs = core.fs
	event_lib.init(fs)
	# Load accounts, groups and trash? FIXME
	eventAccounts = event_lib.EventAccountsHolder.load(fs)
	eventGroups = event_lib.EventGroupsHolder.load(fs)
	eventTrash = event_lib.EventTrash.load(fs)
	####
	todayCell = cell = cellCache.getTodayCell()  # FIXME


def withFS(obj: "SObj") -> "SObj":
	obj.fs = fs
	return obj


######################################################################

localTzHist = []

shownCals = []  # FIXME

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

##############################

menuMainItemDefs = OrderedDict([
	("resize", dict(
		cls="ImageMenuItem",
		label=_("Resize"),
		imageName="resize.svg",
		func="onResizeFromMenu",
		signalName="button-press-event"
	)),
	("onTop", dict(
		cls="CheckMenuItem",
		label=_("_On Top"),
		func="onKeepAboveClick",
		active="winKeepAbove",
	)),
	("onAllDesktops", dict(
		cls="CheckMenuItem",
		label=_("On All De_sktops"),
		func="onStickyClick",
		active="winSticky",
	)),
	("today", dict(
		cls="ImageMenuItem",
		label=_("Select _Today"),
		imageName="go-home.svg",
		func="goToday",
	)),
	("selectDate", dict(
		cls="ImageMenuItem",
		label=_("Select _Date..."),
		imageName="select-date.svg",
		func="selectDateShow",
	)),
	("dayInfo", dict(
		cls="ImageMenuItem",
		label=_("Day Info"),
		imageName="info.svg",
		func="dayInfoShow",
	)),
	("customize", dict(
		cls="ImageMenuItem",
		label=_("_Customize"),
		imageName="document-edit.svg",
		func="customizeShow",
	)),
	("preferences", dict(
		cls="ImageMenuItem",
		label=_("_Preferences"),
		imageName="preferences-system.svg",
		func="prefShow",
	)),
	# ("addCustomEvent", dict(
	# 	cls="ImageMenuItem",
	# 	label=_("_Add Event"),
	# 	imageName="list-add.svg",
	# 	func="addCustomEvent",  # to call ui.addCustomEvent
	# )),
	("dayCalWin", dict(
		cls="ImageMenuItem",
		label=_("Day Calendar (Desktop Widget)"),
		imageName="starcal.svg",
		func="dayCalWinShow",
	)),
	("eventManager", dict(
		cls="ImageMenuItem",
		label=_("_Event Manager"),
		imageName="list-add.svg",
		func="eventManShow",
	)),
	("timeLine", dict(
		cls="ImageMenuItem",
		label=_("Time Line"),
		imageName="timeline.svg",
		func="timeLineShow",
	)),
	("yearWheel", dict(
		cls="ImageMenuItem",
		label=_("Year Wheel"),
		imageName="year-wheel.svg",
		func="yearWheelShow",
	)),  # icon? FIXME
	# ("weekCal", dict(
	# 	cls="ImageMenuItem",
	# 	label=_("Week Calendar"),
	# 	imageName="week-calendar.svg",
	# 	func="weekCalShow",
	# )),
	("exportToHtml", dict(
		cls="ImageMenuItem",
		label=_("Export to {format}").format(format="HTML"),
		imageName="export-to-html.svg",
		func="onExportClick",
	)),
	("adjustTime", dict(
		cls="ImageMenuItem",
		label=_("Ad_just System Time"),
		imageName="preferences-system.svg",
		func="adjustTime",
	)),
	("about", dict(
		cls="ImageMenuItem",
		label=_("_About"),
		imageName="dialog-information.svg",
		func="aboutShow",
	)),
	("quit", dict(
		cls="ImageMenuItem",
		label=_("_Quit"),
		imageName="application-exit.svg",
		func="quit",
	)),
])

##############################


def getActiveMonthCalParams():
	return list(zip(
		calTypes.active,
		mcalTypeParams,
	))


################################

eventIconDir = join(svgDir, "event")


class TagIconItem:
	def __init__(self, name, desc="", icon="", eventTypes=()):
		self.name = name
		if not desc:
			desc = name.capitalize()
		self.desc = _(desc)
		if icon:
			if not isabs(icon):
				icon = join(eventIconDir, icon)
		else:
			iconTmp = join(eventIconDir, name) + ".svg"
			if isfile(iconTmp):
				icon = iconTmp
			else:
				log.debug(f"TagIconItem: file not found: {iconTmp}")
		self.icon = icon
		self.eventTypes = eventTypes
		self.usage = 0

	def getIconRel(self):
		icon = self.icon
		if icon.startswith(svgDir + os.sep):
			return icon[len(svgDir) + 1:]
		return icon

	def __repr__(self):
		return (
			f"TagIconItem({self.name!r}, desc={self.desc!r}, " +
			f"icon={self.icon!r}, eventTypes={self.eventTypes!r})"
		)


eventTags = (
	TagIconItem("alarm"),
	TagIconItem("birthday", eventTypes=("yearly",), desc="Birthday (Balloons)"),
	TagIconItem("birthday2", eventTypes=("yearly",), desc="Birthday (Cake)"),
	TagIconItem("business"),
	TagIconItem("education"),
	TagIconItem("favorite"),
	TagIconItem("green_clover", desc="Green Clover"),
	TagIconItem("holiday"),
	TagIconItem("important"),
	TagIconItem("marriage", eventTypes=("yearly",)),
	TagIconItem("note", eventTypes=("dailyNote",)),
	TagIconItem("phone_call", desc="Phone Call", eventTypes=("task",)),
	TagIconItem("task", eventTypes=("task",)),
	TagIconItem("university", eventTypes=("task",)),  # FIXME: eventTypes
	TagIconItem("shopping_cart", desc="Shopping Cart"),

	TagIconItem("personal"),  # TODO: icon
	TagIconItem("appointment", eventTypes=("task",)),  # TODO: icon
	TagIconItem("meeting", eventTypes=("task",)),  # TODO: icon
	TagIconItem("travel"),  # TODO: icon
)


def getEventTagsDict():
	return {
		tagObj.name: tagObj for tagObj in eventTags
	}


eventTagsDesc = {
	t.name: t.desc for t in eventTags
}

###################
fs = None  # type: event_lib.FileSystem
eventAccounts = []  # type: List[event_lib.EventAccount]
eventGroups = []  # type: List[event_lib.EventGroup]
eventTrash = None  # type: event_lib.EventTrash


def iterAllEvents():  # dosen"t include orphan events
	for group in eventGroups:
		for event in group:
			yield event
	for event in eventTrash:
		yield event


eventUpdateQueue = EventUpdateQueue()


# def updateEventTagsUsage():  # FIXME where to use?
# 	tagsDict = getEventTagsDict()
# 	for tagObj in eventTags:
# 		tagObj.usage = 0
# 	for event in events:  # FIXME
# 		for tag in event.tags:
# 			td = tagsDict.get(tag)
# 			if td is not None:
# 				tagsDict[tag].usage += 1


###################
# BUILD CACHE AFTER SETTING calTypes.primary
maxDayCacheSize = 100  # maximum size of cellCache (days number)
maxWeekCacheSize = 12

cellCache = CellCache()
todayCell = cell = None
###########################
# appLogo = join(pixDir, "starcal.png")
appLogo = join(svgDir, "starcal.svg")
appIcon = join(pixDir, "starcal-48.png")
###########################
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
####
bgColor = (26, 0, 1, 255)  # or None
borderColor = (123, 40, 0, 255)
borderTextColor = (255, 255, 255, 255)  # text of weekDays and weekNumbers
# mcalMenuCellBgColor = borderColor
textColor = (255, 255, 255, 255)
menuTextColor = None  # borderTextColor # FIXME
holidayColor = (255, 160, 0, 255)
inactiveColor = (255, 255, 255, 115)
todayCellColor = (0, 255, 0, 50)
##########
cursorOutColor = (213, 207, 0, 255)
cursorBgColor = (41, 41, 41, 255)
##########
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

##########
# cellMenuXOffset: when we were using ImageMenuItem and CheckMenuItem,
# something between 48 and 56 for cellMenuXOffset was good
# but after migrating away from those 2, it's not needed anymore (so zero)
cellMenuXOffset = 0
##########
wcalCursorLineWidthFactor = 0.12
wcalCursorRoundingFactor = 0.50
###
mcalCursorLineWidthFactor = 0.12
mcalCursorRoundingFactor = 0.50
###
mcalGrid = False
mcalGridColor = (255, 252, 0, 82)
##########
mcalLeftMargin = 30
mcalTopMargin = 30
####################
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

####################
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

####################

dcalWeekdayLocalize = True
dcalWeekdayAbbreviate = False
dcalWeekdayUppercase = False

dcalWinWeekdayLocalize = True
dcalWinWeekdayAbbreviate = False
dcalWinWeekdayUppercase = False

####################

dcalEventIconSize = 20
dcalEventTotalSizeRatio = 0.3
# 0.3 means %30 of window size (minimum of window height and width)

dcalWinEventIconSize = 20
dcalWinEventTotalSizeRatio = 0.3
# 0.3 means %30 of window size (minimum of window height and width)

####################

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


####################

boldYmLabel = True
showYmArrows = True  # apply in Pref FIXME

# delay for shift up/down items of menu for right click on YearLabel
labelMenuDelay = 0.1

####################

preferencesPagePath = ""
customizePagePath = ""

####################

statusIconImage = join(sourceDir, "status-icons", "dark-green.svg")
statusIconImageHoli = join(sourceDir, "status-icons", "dark-red.svg")
(
	statusIconImageDefault,
	statusIconImageHoliDefault,
) = statusIconImage, statusIconImageHoli
statusIconFontFamilyEnable = False
statusIconFontFamily = None
statusIconHolidayFontColorEnable = False
statusIconHolidayFontColor = None
statusIconFixedSizeEnable = False
statusIconFixedSizeWH = (24, 24)
####################
pluginsTextStatusIcon = False
pluginsTextInsideExpander = True
pluginsTextIsExpanded = True  # effects only if pluginsTextInsideExpander
eventViewMaxHeight = 200
####################
dragGetCalType = core.GREGORIAN   # apply in Pref FIXME
# dragGetDateFormat = "%Y/%m/%d"
dragRecMode = core.GREGORIAN   # apply in Pref FIXME
####################
monthRMenuNum = True
# monthRMenu

_wmDir = join(svgDir, "wm")
winControllerThemeList = [
	name for name in os.listdir(_wmDir)
	if isdir(join(_wmDir, name))
]

winControllerTheme = "default"
winControllerButtons = (
	("sep", True),
	("rightPanel", True),
	("min", True),
	("max", True),
	("close", True),
	("sep", False),
	("sep", False),
	("sep", False),
)
winControllerButtonsDefault = winControllerButtons[:]
winControllerIconSize = 24
winControllerBorder = 0
winControllerSpacing = 0
####################
winKeepAbove = True
winSticky = True
winMaximized = False
winX = 0
winY = 0
###
fontDefault = Font(family="Sans", size=12)
fontDefaultInit = fontDefault
fontCustom = None
fontCustomEnable = False
#####################
showMain = True  # Open main window on start (or only goto statusIcon)
showDesktopWidget = False  # Open desktop widget on start
#####################
mainWinItems = (
	("toolbar", True),
	("labelBox", True),
	("monthCal", False),
	("weekCal", True),
	("dayCal", False),
	("monthPBar", False),
	("seasonPBar", True),
	("yearPBar", False),
)

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


wcalItems = (
	("toolbar", True),
	("weekDays", True),
	("pluginsText", True),
	("eventsIcon", True),
	("eventsText", True),
	("daysOfMonth", True),
)

wcalItemsDefault = wcalItems[:]

####################

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


####################

monthPBarCalType = -1

####################

seasonPBar_southernHemisphere = False
wcal_moonStatus_southernHemisphere = False

####################

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


#####################

disableRedraw = False
# when set disableRedraw=True, widgets will not re-draw their contents

focusTime = 0
lastLiveConfChangeTime = 0


saveLiveConfDelay = 0.5  # seconds
timeout_initial = 200
timeout_repeat = 50


def updateFocusTime(*args):
	global focusTime
	focusTime = now()


########################################################

loadConf()

########################################################

if not isfile(statusIconImage):
	statusIconImage = statusIconImageDefault
if not isfile(statusIconImageHoli):
	statusIconImageHoli = statusIconImageHoliDefault


_localTzName = str(core.localTz)
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


needRestartPref = {}  # Right place? FIXME
for key in (
	"locale_man.lang",
	"locale_man.enableNumLocale",
	"winTaskbar",
	"showYmArrows",
	"useAppIndicator",
	"buttonIconEnable",
	"useSystemIcons",
):
	needRestartPref[key] = eval(key)

if menuTextColor is None:
	menuTextColor = borderTextColor

##################################

# move to gtk_ud ? FIXME
mainWin = None
prefWindow = None
eventManDialog = None
eventSearchWin = None
timeLineWin = None
dayCalWin = None
yearWheelWin = None
weekCalWin = None
