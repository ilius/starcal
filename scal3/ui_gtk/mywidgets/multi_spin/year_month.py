from time import localtime

from scal3.mywidgets.multi_spin import MonthField, YearField
from scal3.ui_gtk.mywidgets.multi_spin import MultiSpinButton

__all__ = ["YearMonthButton"]


class YearMonthButton(MultiSpinButton):
	def __init__(self, date: tuple[int, int, int] | None = None, **kwargs) -> None:
		MultiSpinButton.__init__(
			self,
			"/",
			(
				YearField(),
				MonthField(),
			),
			**kwargs,
		)
		if date is None:
			date = localtime()[:2]
		self.set_value(date)
