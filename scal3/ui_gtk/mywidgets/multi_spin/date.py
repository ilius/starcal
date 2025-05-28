from __future__ import annotations

from collections.abc import Sequence
from time import localtime

from scal3.cal_types import jd_to, to_jd
from scal3.mywidgets.multi_spin import (
	ContainerField,
	DayField,
	MonthField,
	YearField,
)
from scal3.ui_gtk.mywidgets.multi_spin import MultiSpinButton

__all__ = ["DateButton"]


class DateButton(MultiSpinButton[ContainerField[int], Sequence[int]]):
	def __init__(self, date: tuple[int, int, int] | None = None, **kwargs) -> None:
		self.dayField = DayField()
		MultiSpinButton.__init__(
			self,
			field=ContainerField(
				"/",
				YearField(),
				MonthField(),
				self.dayField,
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
		self.dayField.setMax(maxDay)
		self.update()

	def getDate(self) -> tuple[int, int, int]:
		y, m, d = self.get_value()
		return (y, m, d)

	def setDate(self, date: Sequence[int]) -> None:
		y, m, d = date
		self.set_value((y, m, d))
