from typing import Protocol

# type TranslateFunc = Callable[[str, str]]


class TranslateFunc(Protocol):
	def __call__(self, s: str, ctx: str | None = None) -> str: ...


class CalTypeModule(Protocol):
	name: str
	desc: str
	origLang: str
	minMonthLen: int
	maxMonthLen: int
	options: list[tuple[str, ...]]

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
