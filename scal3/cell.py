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

import typing
from typing import TypedDict

from cachetools import LRUCache

from scal3 import cal_types, core, event_lib, ui
from scal3.cal_types import calTypes, jd_to
from scal3.cell_type import CellType
from scal3.date_utils import getJdRangeForMonth
from scal3.date_utils import monthPlus as lowMonthPlus
from scal3.event_lib import ev
from scal3.ui import conf

if typing.TYPE_CHECKING:
	from collections.abc import Sequence

	from scal3.cell_type import CellCacheType, CompiledTimeFormat
	from scal3.color_utils import ColorType
	from scal3.event_lib.occur_data import DayOccurData
	from scal3.plugin_type import PluginType

__all__ = ["Cell", "MonthStatus", "WeekStatus", "init"]


class EventDataDict(TypedDict):
	time: str  # time descriptive string
	time_epoch: int  # epoch time
	is_allday: bool
	text: Sequence[str]  # of text lines
	icon: str  # icon path
	color: ColorType
	ids: tuple[int, int]  # (gid, eid)
	show: tuple[bool, bool, bool]  # (showInDCal, showInWCal, showInMCal)
	showInStatusIcon: bool


class Cell:
	"""status and information of a cell."""

	# ocTimeMax = 0
	# ocTimeCount = 0
	# ocTimeSum = 0
	def __init__(self, jd: int) -> None:
		self._eventsData: list[DayOccurData] | None = None
		self._pluginsText: list[list[str]] = []
		self._pluginsData: list[tuple[PluginType, str]] = []
		# ---
		self.jd = jd
		date = core.jd_to_primary(jd)
		self.year, self.month, self.day = date
		self.monthPos: tuple[int, int] = (0, 0)
		self.weekDay = core.jwday(jd)
		self.weekNum = core.getWeekNumber(self.year, self.month, self.day)
		# self.weekNumNeg = self.weekNum+1 - core.getYearWeeksCount(self.year)
		self.weekNumNeg = self.weekNum - int(
			calTypes.primaryModule().avgYearLen / 7,
		)
		self.holiday = self.weekDay in core.holidayWeekDays.v
		# -------------------
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
		# -------------------

		self.absWeekNumber = 0
		self.weekDayIndex = 0

		# -------------------
		for k in core.plugIndex.v:
			plug = core.allPlugList.v[k]
			if plug:
				try:
					plug.updateCell(self)
				except Exception:
					log.exception("")
		# -------------------
		self.getEventsData()

	@property
	def date(self) -> tuple[int, int, int]:
		return (self.year, self.month, self.day)

	def addPluginText(self, plug: PluginType, text: str) -> None:
		self._pluginsText.append(text.split("\n"))
		self._pluginsData.append((plug, text))

	def getPluginsData(
		self,
		firstLineOnly: bool = False,
	) -> list[tuple[PluginType, str]]:
		return [
			(plug, text.split("\n")[0]) if firstLineOnly else (plug, text)
			for (plug, text) in self._pluginsData
		]

	def getPluginsText(self, firstLineOnly: bool = False) -> str:
		return "\n".join(text for (plug, text) in self.getPluginsData(firstLineOnly))

	def clearEventsData(self) -> None:
		self._eventsData = None

	def getEventsData(self) -> list[DayOccurData]:
		if self._eventsData is not None:
			return self._eventsData
		# t0 = perf_counter()
		self._eventsData = event_lib.getDayOccurrenceData(
			self.jd,
			ev.groups,
			tfmt=conf.eventDayViewTimeFormat.v,
		)
		return self._eventsData
		# dt = perf_counter() - t0
		# Cell.ocTimeSum += dt
		# Cell.ocTimeCount += 1
		# Cell.ocTimeMax = max(Cell.ocTimeMax, dt)

	def format(
		self,
		compiledFmt: CompiledTimeFormat,
		calType: int | None = None,
		tm: tuple[int, int, int] | None = None,
	) -> str:
		if calType is None:
			calType = calTypes.primary
		if tm is None:
			tm = (0, 0, 0)
		pyFmt, funcs = compiledFmt
		return pyFmt % tuple(f(self, calType, tm) for f in funcs)

	def getDate(self, calType: int) -> tuple[int, int, int]:
		return self.dates[calType]

	def getEventIcons(self, showIndex: int) -> list[str]:
		iconList = []
		for item in self.getEventsData():
			if not item.show[showIndex]:
				continue
			icon = item.icon
			if icon and icon not in iconList:
				iconList.append(icon)
		return iconList

	def getDayEventIcons(self) -> list[str]:
		return self.getEventIcons(0)

	def getWeekEventIcons(self) -> list[str]:
		return self.getEventIcons(1)

	def getMonthEventIcons(self) -> list[str]:
		return self.getEventIcons(2)

	def setMonthPos(self) -> None:
		offset = core.getWeekDay(self.year, self.month, 1)  # month start offset
		yPos, xPos = divmod(offset + self.day - 1, 7)
		self.monthPos = (xPos, yPos)

	# How do this with KOrginizer? FIXME
	def dayOpenEvolution(
		self,
		arg: object = None,  # noqa: ARG002
	) -> None:
		from subprocess import Popen

		# y, m, d = jd_to(self.jd-1, core.GREGORIAN)
		# in gnome-cal opens prev day! why??
		y, m, d = self.dates[core.GREGORIAN]
		Popen(
			f"LANG=en_US.UTF-8 evolution calendar:///?startdate={y:04d}{m:02d}{d:02d}",
			shell=True,
		)  # FIXME
		# f"calendar:///?startdate={y:04d}{m:02d}{d:02d}T120000Z"
		# What "Time" pass to evolution?
		# like gnome-clock: T193000Z (19:30:00) / Or ignore "Time"
		# evolution calendar:///?startdate=$(date +"%Y%m%dT%H%M%SZ")


# I can't find the correct syntax for this `...`
# CellPluginsType = dict[str, tuple[
# 	Callable[[CellType], None],
# 	Callable[[CellCache, ...], list[CellType]]
# ]]


class CellCache:
	__slots__ = [
		"current",
		"jdCells",
		"today",
		"weekEvents",
	]

	def __init__(self) -> None:
		# a mapping from julan_day to Cell instance
		self.resetCache()
		self.today = self.getTodayCell()
		self.current = self.today

	def resetCache(self) -> None:
		# key: jd(int), value: CellType
		self.jdCells: LRUCache[int, CellType] = LRUCache(maxsize=conf.maxDayCacheSize.v)

		# key: absWeekNumber(int), value: list[dict]
		# self.weekEvents = LRUCache(maxsize=conf.maxWeekCacheSize.v)

	def clear(self) -> None:
		self.resetCache()
		self.current = self.getCell(self.current.jd)
		self.today = self.getCell(self.today.jd)

	def clearEventsData(self) -> None:
		for tmpCell in self.jdCells.values():
			tmpCell.clearEventsData()
		self.current.clearEventsData()
		self.today.clearEventsData()
		# self.weekEvents = LRUCache(maxsize=conf.maxWeekCacheSize.v)

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
		cell = Cell(jd)

		cell.absWeekNumber, cell.weekDayIndex = core.getWeekDateFromJd(jd)

		cell.setMonthPos()

		self.jdCells[jd] = cell
		return cell

	# def getMonthData(self, year, month):  # needed? FIXME

	def getMonthPlus(self, tmpCell: CellType, plus: int) -> CellType:
		year, month = lowMonthPlus(tmpCell.year, tmpCell.month, plus)
		day = min(tmpCell.day, cal_types.getMonthLen(year, month, calTypes.primary))
		return self.getCellByDate(year, month, day)

	def changeDate(
		self,
		year: int,
		month: int,
		day: int,
		calType: int | None = None,
	) -> None:
		if calType is None:
			calType = calTypes.primary
		self.current = self.getCell(core.to_jd(year, month, day, calType))

	def gotoJd(self, jd: int) -> None:
		self.current = self.getCell(jd)

	def jdPlus(self, plus: int = 1) -> None:
		self.current = self.getCell(self.current.jd + plus)

	def monthPlus(self, plus: int = 1) -> None:
		self.current = self.getMonthPlus(self.current, plus)

	def yearPlus(self, plus: int = 1) -> None:
		cell = self.current
		year = cell.year + plus
		month = cell.month
		day = min(cell.day, cal_types.getMonthLen(year, month, calTypes.primary))
		self.current = self.getCellByDate(year, month, day)

	def getCurrentWeekStatus(self) -> WeekStatus:
		return WeekStatus(self, self.current.absWeekNumber)

	def getMonthStatus(self, year: int, month: int) -> MonthStatus:
		return MonthStatus(self, year, month)

	def getCurrentMonthStatus(self) -> MonthStatus:
		return MonthStatus(self, self.current.year, self.current.month)


class WeekStatus(list[CellType]):
	__slots__ = [
		"absWeekNumber",
	]

	# list (of 7 cells)
	def __init__(self, cells: CellCacheType, absWeekNumber: int) -> None:
		self.absWeekNumber = absWeekNumber
		startJd = core.getStartJdOfAbsWeekNumber(absWeekNumber)
		endJd = startJd + 7
		# self.startJd = startJd
		# self.startDate = core.jd_to_primary(self.startJd)
		# self.weekNumberOfYear = core.getWeekNumber(*self.startDate)
		# ---------
		# list.__init__(self, [
		# 	cells.getCell(jd) for jd in range(startJd, endJd)
		# ])
		list.__init__(self, [])
		for jd in range(startJd, endJd):
			# log.debug("WeekStatus", jd)
			self.append(cells.getCell(jd))


class MonthStatus(list[list[CellType]]):  # FIXME
	__slots__ = [
		"month",
		"offset",
		"weekNum",
		"year",
	]

	# self[sy<6][sx<7] of cells
	# list (of 6 lists, each list containing 7 cells)
	def __init__(
		self,
		cells: CellCacheType,
		year: int,
		month: int,
	) -> None:
		self.year = year
		self.month = month
		self.offset = core.getWeekDay(year, month, 1)  # month start offset
		initJd = core.primary_to_jd(year, month, 1)
		self.weekNum = [core.getWeekNumberByJd(initJd + i * 7) for i in range(6)]
		# ---------
		startJd, _endJd = getJdRangeForMonth(year, month, calTypes.primary)
		tableStartJd = startJd - self.offset
		# -----
		list.__init__(
			self,
			[
				[
					cells.getCell(
						tableStartJd + yPos * 7 + xPos,
					)
					for xPos in range(7)
				]
				for yPos in range(6)
			],
		)

	# needed? FIXME
	# def getDayCell(self, day):
	# 	yPos, xPos = divmod(day + self.offset - 1, 7)
	# 	return self[yPos][xPos]


def init() -> None:
	ui.cells = CellCache()
