from __future__ import annotations

from time import localtime

from scal3.mywidgets.multi_spin import DayField, MonthField, YearField
from scal3.ui_gtk.mywidgets.multi_spin.option_box import MultiSpinOptionBox

__all__ = ["DateButtonOption"]


class DateButtonOption(MultiSpinOptionBox):
	def __init__(self, date: tuple[int, int, int] | None = None, **kwargs) -> None:
		MultiSpinOptionBox.__init__(
			self,
			"/",
			(
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
		self.spin.field.children[2].setMax(maxDay)
		self.spin.update()
