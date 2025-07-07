from __future__ import annotations

from collections.abc import Sequence
from time import localtime

from scal3.mywidgets.multi_spin import ContainerField, HourField, Z60Field
from scal3.ui_gtk.mywidgets.multi_spin import MultiSpinButton

__all__ = ["TimeButton"]


class TimeButton(MultiSpinButton[ContainerField[int], Sequence[int]]):
	def __init__(self, hms: tuple[int, int, int] | None = None) -> None:
		MultiSpinButton.__init__(
			self,
			field=ContainerField(
				":",
				HourField(),
				Z60Field(),
				Z60Field(),
			),
		)
		if hms is None:
			hms = localtime()[3:6]
		self.set_value(hms)

	def get_seconds(self) -> int:
		h, m, s = self.get_value()
		return h * 3600 + m * 60 + s

	def set_seconds(self, seconds: int) -> None:
		_day, s = divmod(seconds, 86400)
		# do what with "day" ?
		h, s = divmod(s, 3600)
		m, s = divmod(s, 60)
		self.set_value((h, m, s))
		# return day

	def getTime(self) -> tuple[int, int, int]:
		h, m, s = self.get_value()
		return (h, m, s)
