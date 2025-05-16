from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scal3.s_object import SObj

if TYPE_CHECKING:
	from collections.abc import Sequence

	from scal3.cell_type import CellType

__all__ = ["PluginType"]


class BasePlugin(SObj):
	name: str | None
	external: bool
	loaded: bool
	params: Sequence[str]
	essentialParams: Sequence[str]

	def getArgs(self) -> None: ...

	def __bool__(self) -> bool: ...

	def __init__(
		self,
		_file: str,
	) -> None: ...

	def getData(self) -> dict[str, Any]: ...

	def setData(self, data: dict[str, Any]) -> None: ...

	def clear(self) -> None: ...

	def load(self) -> None: ...

	def getText(self, year: int, month: int, day: int) -> None: ...

	def updateCell(self, c: CellType) -> None: ...

	def onCurrentDateChange(self, gdate: tuple[int, int, int]) -> None: ...

	def exportToIcs(self, fileName: str, startJd: int, endJd: int) -> None: ...


class PluginType(BasePlugin):
	pass
