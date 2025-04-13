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

	def getArgs(self): ...

	def __bool__(self): ...

	def __init__(
		self,
		_file,
	): ...

	def getData(self): ...

	def setData(self, data): ...

	def clear(self): ...

	def load(self): ...

	def getText(self, year, month, day): ...

	def updateCell(self, c): ...

	def onCurrentDateChange(self, gdate): ...

	def exportToIcs(self, fileName, startJd, endJd): ...


class PluginType(BasePlugin):
	pass
