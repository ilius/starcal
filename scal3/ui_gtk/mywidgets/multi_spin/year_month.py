from __future__ import annotations

from collections.abc import Sequence
from time import localtime

from scal3.mywidgets.multi_spin import ContainerField, MonthField, YearField
from scal3.ui_gtk.mywidgets.multi_spin import MultiSpinButton

__all__ = ["YearMonthButton"]


class YearMonthButton(MultiSpinButton[ContainerField[int], Sequence[int]]):
	def __init__(self, date: tuple[int, int] | None = None, **kwargs) -> None:
		MultiSpinButton.__init__(
			self,
			field=ContainerField[int](
				"/",
				YearField(),
				MonthField(),
			),
			**kwargs,
		)
		if date is None:
			date = localtime()[:2]
		self.set_value(date)
