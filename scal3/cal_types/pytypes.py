from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
	from scal3.option import Option

__all__ = ["CalTypeModule", "OptionTuple", "TranslateFunc"]


class TranslateFunc(Protocol):
	def __call__(
		self,
		s: str | float,
		nums: bool = False,
		ctx: str | None = None,
		default: str | None = None,
		localeMode: str | None = None,
		calType: int | None = None,
		fillZero: int = 0,
		negEnd: bool = False,
	) -> str: ...


type OptionTuple = (
	tuple[str, type[bool], str]
	| tuple[str, type[list[Any]], str, Sequence[str]]
	| tuple[str, str, str, str]
)


class CalTypeModule(Protocol):
	name: str
	desc: str
	origLang: str
	minMonthLen: int
	maxMonthLen: int
	monthNameContext: Option[str]
	options: list[tuple[str, ...]]
	confOptions: dict[str, Option[Any]]
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
