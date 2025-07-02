from __future__ import annotations

from time import localtime

from scal3.mywidgets.multi_spin import (
	ContainerField,
	DayField,
	IntField,
	MonthField,
	YearField,
)
from scal3.ui_gtk.mywidgets.multi_spin.option_box import MultiSpinOptionBox

__all__ = ["DateButtonOption"]


class DateButtonOption(MultiSpinOptionBox[ContainerField[int], tuple[int, int, int]]):
	def __init__(self, date: tuple[int, int, int] | None = None, **kwargs) -> None:
		MultiSpinOptionBox.__init__(
			self,
			field=ContainerField[int](
				"/",
				YearField(),
				MonthField(),
				DayField(),
			),
			**kwargs,
		)
		if date is None:
			date = localtime()[:3]
		self.set_value(date)

	def setMaxDay(self, maxDay: int) -> None:
		field = self.spin.field.children[2]
		assert isinstance(field, IntField)
		field.setMax(maxDay)
		self.spin.update()
