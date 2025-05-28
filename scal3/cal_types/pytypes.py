from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

__all__ = ["CalTypeModule", "OptionTuple", "TranslateFunc"]

# type TranslateFunc = Callable[[str, str]]


class TranslateFunc(Protocol):
	def __call__(self, s: str, ctx: str | None = None) -> str: ...


type OptionTuple = (
	tuple[str, type[bool], str]
	| tuple[str, type[list], str, Sequence[str]]
	| tuple[str, str, str, str]
)


class CalTypeModule(Protocol):
	name: str
	desc: str
	origLang: str
	minMonthLen: int
	maxMonthLen: int
	options: list[tuple[str, ...]]
	avgYearLen: float

	def getMonthName(self, m: int, y: int | None = None) -> str: ...

	def getMonthNameAb(
		self,
		tr: TranslateFunc,
		m: int,
		y: int | None = None,
	) -> str: ...

	def getMonthLen(self, y: int, m: int) -> int: ...

	def to_jd(self, year: int, month: int, day: int) -> int: ...

	def jd_to(self, jd: float) -> tuple[int, int, int]: ...

	def save(self) -> None: ...
