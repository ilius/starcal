from __future__ import annotations

from collections.abc import Sequence
from time import localtime

from scal3.mywidgets.multi_spin import ContainerField, HourField, Z60Field
from scal3.ui_gtk.mywidgets.multi_spin import MultiSpinButton

__all__ = ["HourMinuteButton"]


class HourMinuteButton(MultiSpinButton[ContainerField[int], Sequence[int]]):
	def __init__(self, hm: tuple[int, int] | None = None, **kwargs) -> None:
		MultiSpinButton.__init__(
			self,
			field=ContainerField(
				":",
				HourField(),
				Z60Field(),
			),
			**kwargs,
		)
		if hm is None:
			hm = localtime()[3:5]
		self.set_value(hm)

	# def get_value(self) -> tuple[int, int]:
	# 	value = MultiSpinButton.get_value(self)
	# 	return (value[0], 0)

	# def set_value(self, value: tuple[int, int]) -> None:
	# 	# assert not isinstance(value, int)
	# 	# value = value[:2]
	# 	MultiSpinButton.set_value(self, value)
