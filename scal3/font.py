from __future__ import annotations

from dataclasses import dataclass
from typing import Self

__all__ = ["Font", "FontTuple"]


type FontTuple = tuple[str, bool, bool, float]


@dataclass(slots=True)
class Font:
	family: str | None
	bold: bool = False
	italic: bool = False
	size: float = 0

	@classmethod
	def fromList(cls, lst: list | None) -> Self | None:
		if lst is None:
			return
		return Font(*lst)

	def to_json(self) -> tuple[str | None, bool, bool, float]:
		return (self.family, self.bold, self.italic, self.size)

	def copy(self) -> Self:
		return Font(*self.to_json())
