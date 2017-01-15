from time import localtime

from scal3.mywidgets.multi_spin import YearField, MonthField
from scal3.ui_gtk.mywidgets.multi_spin import MultiSpinButton


class YearMonthButton(MultiSpinButton):
	def __init__(self, date=None, **kwargs):
		MultiSpinButton.__init__(
			self,
			"/",
			(
				YearField(),
				MonthField(),
			),
			**kwargs
		)
		if date is None:
			date = localtime()[:2]
		self.set_value(date)
