from __future__ import annotations

from collections.abc import Sequence
from time import localtime

from scal3.mywidgets.multi_spin import ContainerField, HourField, Z60Field
from scal3.ui_gtk.mywidgets.multi_spin.option_box import MultiSpinOptionBox

__all__ = ["HourMinuteButtonOption"]


class HourMinuteButtonOption(MultiSpinOptionBox[ContainerField[int], Sequence[int]]):
	def __init__(self, hm: tuple[int, int] | None = None, **kwargs) -> None:
		MultiSpinOptionBox.__init__(
			self,
			ContainerField(
				":",
				HourField(),
				Z60Field(),
			),
			**kwargs,
		)
		if hm is None:
			hm = localtime()[3:5]
		self.set_value(hm)
