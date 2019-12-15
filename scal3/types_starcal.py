#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Tuple, List, Callable


class CellType:
	def __init__(self, jd: int):
		raise NotImplementedError

	def format(
		self,
		compiledFmt: "CompiledTimeFormat",
		calType: Optional[int] = None,
		tm: Optional[Tuple[int, int, int]] = None,
	):
		raise NotImplementedError

	def getDate(self, calType: int) -> Tuple[int, int, int]:
		raise NotImplementedError

	def inSameMonth(self, other: "CellType") -> bool:
		raise NotImplementedError

	def getEventIcons(self, showIndex: int) -> List[str]:
		raise NotImplementedError

	def getDayEventIcons(self) -> List[str]:
		raise NotImplementedError

	def getWeekEventIcons(self) -> List[str]:
		raise NotImplementedError

	def getMonthEventIcons(self) -> List[str]:
		raise NotImplementedError


CompiledTimeFormat = Tuple[
	str,
	List[
		Callable[
			[CellType, int, Tuple[int, int, int]],
			str,
		],
	],
]
