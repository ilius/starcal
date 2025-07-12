from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
	from scal3.event_lib.occur_data import DayOccurData

__all__ = [
	"CellCacheType",
	"CellType",
	"CompiledTimeFormat",
	"DummyCellCache",
	"MonthStatusType",
	"PluginType",
	"WeekStatusType",
]

type CompiledTimeFormat = tuple[
	str,
	list[
		Callable[
			[CellType, int, tuple[int, int, int]],
			str,
		],
	],
]


class PluginType(Protocol):
	name: str
	show_date: bool
	title: str
	file: str
	enable: bool
	external: bool
	loaded: bool
	hasConfig: bool
	about: str
	params: list[str]
	essentialParams: list[str]
	authors: list[str]

	def getArgs(self) -> dict[str, Any]: ...

	def __bool__(self) -> bool: ...

	def __init__(
		self,
		_file: str,
	) -> None: ...

	def getDict(self) -> dict[str, Any]: ...

	def setDict(self, data: dict[str, Any]) -> None: ...

	def clear(self) -> None: ...

	def loadData(self) -> None: ...

	def getText(self, year: int, month: int, day: int) -> str: ...

	def updateCell(self, c: CellType) -> None: ...

	def onCurrentDateChange(self, gdate: tuple[int, int, int]) -> None: ...

	def exportToIcs(self, fileName: str, startJd: int, endJd: int) -> None: ...

	def open_configure(self) -> None: ...


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


class MonthStatusType(Protocol):
	weekNum: list[int]
	month: int
	year: int

	def __getitem__(self, index: int) -> list[CellType]: ...


class WeekStatusType(Protocol):
	def __getitem__(self, index: int) -> CellType: ...


class CellCacheType(Protocol):
	current: CellType
	today: CellType

	def getCell(self, jd: int) -> CellType: ...
	def getTmpCell(self, jd: int) -> CellType: ...
	def getTodayCell(self) -> CellType: ...
	def clearEventsData(self) -> None: ...
	def clear(self) -> None: ...
	def getMonthStatus(self, year: int, month: int) -> MonthStatusType: ...
	def getCurrentMonthStatus(self) -> MonthStatusType: ...
	def getCurrentWeekStatus(self) -> WeekStatusType: ...
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

	def getMonthStatus(self, year: int, month: int) -> MonthStatusType:
		raise NotImplementedError

	def getCurrentMonthStatus(self) -> MonthStatusType:
		raise NotImplementedError

	def getCurrentWeekStatus(self) -> WeekStatusType:
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
