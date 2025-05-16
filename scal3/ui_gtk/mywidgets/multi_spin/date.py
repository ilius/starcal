from __future__ import annotations

from time import localtime

from scal3.cal_types import jd_to, to_jd
from scal3.mywidgets.multi_spin import DayField, MonthField, YearField
from scal3.ui_gtk.mywidgets.multi_spin import MultiSpinButton

__all__ = ["DateButton"]


class DateButton(MultiSpinButton):
	def __init__(self, date: tuple[int, int, int] | None = None, **kwargs) -> None:
		MultiSpinButton.__init__(
			self,
			sep="/",
			fields=(
				YearField(),
				MonthField(),
				DayField(),
			),
			**kwargs,
		)
		if date is None:
			date = localtime()[:3]
		self.set_value(date)

	def get_jd(self, calType: int) -> int:
		y, m, d = self.get_value()
		return to_jd(y, m, d, calType)

	def changeCalType(self, fromMode: int, toMode: int) -> None:
		self.set_value(
			jd_to(
				self.get_jd(fromMode),
				toMode,
			),
		)

	def setMaxDay(self, maxDay: int) -> None:
		self.field.children[2].setMax(maxDay)
		self.update()
