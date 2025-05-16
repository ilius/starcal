from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Never, Protocol

if TYPE_CHECKING:
	from scal3.plugin_type import PluginType

__all__ = ["CellCacheType", "CellType", "CompiledTimeFormat"]

type CompiledTimeFormat = tuple[
	str,
	list[
		Callable[
			[CellType, int, tuple[int, int, int]],
			str,
		],
	],
]


class CellType:
	def __init__(self, jd: int) -> None:
		raise NotImplementedError

	def format(
		self,
		compiledFmt: CompiledTimeFormat,
		calType: int | None = None,
		tm: tuple[int, int, int] | None = None,
	) -> Never:
		raise NotImplementedError

	def getDate(self, calType: int) -> tuple[int, int, int]:
		raise NotImplementedError

	def getEventIcons(self, showIndex: int) -> list[str]:
		raise NotImplementedError

	def getDayEventIcons(self) -> list[str]:
		raise NotImplementedError

	def getWeekEventIcons(self) -> list[str]:
		raise NotImplementedError

	def getMonthEventIcons(self) -> list[str]:
		raise NotImplementedError

	def addPluginText(self, plug: PluginType, text: str) -> None:
		raise NotImplementedError

	@property
	def holiday(self) -> bool: ...

	@holiday.setter
	def holiday(self, x: bool) -> None: ...

	@property
	def dates(self) -> Sequence[tuple[int, int, int]]: ...

	@property
	def jd(self) -> int: ...

	@jd.setter
	def jd(self, jd: int) -> None: ...


class CellCacheType(Protocol):
	def getCell(self, jd: int) -> CellType: ...

	def getTmpCell(self, jd: int) -> CellType: ...
