# -*- coding: utf-8 -*-

from typing import Callable


class CellType:
	def __init__(self, jd: int):
		raise NotImplementedError

	def format(
		self,
		compiledFmt: "CompiledTimeFormat",
		calType: "int | None" = None,
		tm: "tuple[int, int, int] | None" = None,
	):
		raise NotImplementedError

	def getDate(self, calType: int) -> tuple[int, int, int]:
		raise NotImplementedError

	def inSameMonth(self, other: "CellType") -> bool:
		raise NotImplementedError

	def getEventIcons(self, showIndex: int) -> list[str]:
		raise NotImplementedError

	def getDayEventIcons(self) -> list[str]:
		raise NotImplementedError

	def getWeekEventIcons(self) -> list[str]:
		raise NotImplementedError

	def getMonthEventIcons(self) -> list[str]:
		raise NotImplementedError


CompiledTimeFormat = tuple[
	str,
	list[
		Callable[
			[CellType, int, tuple[int, int, int]],
			str,
		],
	],
]
