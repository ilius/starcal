from dataclasses import dataclass

__all__ = ["Font"]


@dataclass(slots=True)
class Font:
	family: str | None
	bold: bool = False
	italic: bool = False
	size: float = 0

	def fromList(lst: list | None):
		if lst is None:
			return
		return Font(*lst)

	def to_json(self):
		return [self.family, self.bold, self.italic, self.size]

	def copy(self):
		return Font(*self.to_json())
