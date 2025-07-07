from __future__ import annotations

from collections.abc import Sequence
from time import localtime

from scal3.mywidgets.multi_spin import ContainerField, MonthField, YearField
from scal3.ui_gtk.mywidgets.multi_spin import MultiSpinButton

__all__ = ["YearMonthButton"]


class YearMonthButton(MultiSpinButton[ContainerField[int], Sequence[int]]):
	def __init__(
		self,
		date: tuple[int, int] | None = None,
		arrow_select: bool = True,
		step_inc: float = 1,
		page_inc: float = 10,
	) -> None:
		MultiSpinButton.__init__(
			self,
			field=ContainerField[int](
				"/",
				YearField(),
				MonthField(),
			),
			arrow_select=arrow_select,
			step_inc=step_inc,
			page_inc=page_inc,
		)
		if date is None:
			date = localtime()[:2]
		self.set_value(date)
