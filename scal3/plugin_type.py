from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.s_object import SObj

if TYPE_CHECKING:
	from collections.abc import Sequence

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
		_file,
	) -> None: ...

	def getData(self) -> None: ...

	def setData(self, data) -> None: ...

	def clear(self) -> None: ...

	def load(self) -> None: ...

	def getText(self, year, month, day) -> None: ...

	def updateCell(self, c) -> None: ...

	def onCurrentDateChange(self, gdate) -> None: ...

	def exportToIcs(self, fileName, startJd, endJd) -> None: ...


class PluginType(BasePlugin):
	pass
