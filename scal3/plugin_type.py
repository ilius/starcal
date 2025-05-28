from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
	from scal3.cell_type import CellType

__all__ = ["PluginType"]


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
