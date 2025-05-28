from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
	from scal3.cell import MonthStatus, WeekStatus
	from scal3.event_lib.occur_data import DayOccurData
	from scal3.plugin_type import PluginType

__all__ = ["CellCacheType", "CellType", "CompiledTimeFormat", "DummyCellCache"]

type CompiledTimeFormat = tuple[
	str,
	list[
		Callable[
			[CellType, int, tuple[int, int, int]],
			str,
		],
	],
]


class CellType(Protocol):
	jd: int
	year: int
	month: int
	day: int
	weekDay: int
	weekNum: int
	weekNumNeg: int
	holiday: bool
	dates: list[tuple[int, int, int]]
	absWeekNumber: int
	weekDayIndex: int
	monthPos: tuple[int, int]

	def __init__(self, jd: int) -> None: ...

	@property
	def date(self) -> tuple[int, int, int]: ...

	def format(
		self,
		compiledFmt: CompiledTimeFormat,
		calType: int | None = None,
		tm: tuple[int, int, int] | None = None,
	) -> str: ...

	def getDate(self, calType: int) -> tuple[int, int, int]: ...

	def getEventIcons(self, showIndex: int) -> list[str]: ...

	def getDayEventIcons(self) -> list[str]: ...

	def getWeekEventIcons(self) -> list[str]: ...

	def getMonthEventIcons(self) -> list[str]: ...

	def addPluginText(self, plug: PluginType, text: str) -> None: ...

	def clearEventsData(self) -> None: ...

	def getPluginsData(
		self,
		firstLineOnly: bool = False,
	) -> list[tuple[PluginType, str]]: ...

	def getPluginsText(self, firstLineOnly: bool = False) -> str: ...

	def dayOpenEvolution(self, arg: object = None) -> None: ...

	def getEventsData(self) -> list[DayOccurData]: ...


class CellCacheType(Protocol):
	current: CellType
	today: CellType

	def getCell(self, jd: int) -> CellType: ...
	def getTmpCell(self, jd: int) -> CellType: ...
	def getTodayCell(self) -> CellType: ...
	def clearEventsData(self) -> None: ...
	def clear(self) -> None: ...
	def getMonthStatus(self, year: int, month: int) -> MonthStatus: ...
	def getCurrentMonthStatus(self) -> MonthStatus: ...
	def getCurrentWeekStatus(self) -> WeekStatus: ...
	def gotoJd(self, jd: int) -> None: ...
	def jdPlus(self, plus: int = 1) -> None: ...
	def changeDate(
		self,
		year: int,
		month: int,
		day: int,
		calType: int | None = None,
	) -> None: ...
	def monthPlus(self, plus: int = 1) -> None: ...
	def yearPlus(self, plus: int = 1) -> None: ...


class DummyCellCache:
	current: CellType
	today: CellType

	def getCell(self, jd: int) -> CellType:
		raise NotImplementedError

	def getTmpCell(self, jd: int) -> CellType:
		raise NotImplementedError

	def getTodayCell(self) -> CellType:
		raise NotImplementedError

	def clearEventsData(self) -> None:
		raise NotImplementedError

	def clear(self) -> None:
		raise NotImplementedError

	def getMonthStatus(self, year: int, month: int) -> MonthStatus:
		raise NotImplementedError

	def getCurrentMonthStatus(self) -> MonthStatus:
		raise NotImplementedError

	def getCurrentWeekStatus(self) -> WeekStatus:
		raise NotImplementedError

	def gotoJd(self, jd: int) -> None:
		raise NotImplementedError

	def jdPlus(self, plus: int = 1) -> None:
		raise NotImplementedError

	def changeDate(
		self,
		year: int,
		month: int,
		day: int,
		calType: int | None = None,
	) -> None:
		raise NotImplementedError

	def monthPlus(self, plus: int = 1) -> None:
		raise NotImplementedError

	def yearPlus(self, plus: int = 1) -> None:
		raise NotImplementedError
