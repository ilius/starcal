from time import localtime

from scal3.cal_types import to_jd, jd_to
from scal3.mywidgets.multi_spin import YearField, MonthField, DayField
from scal3.ui_gtk.mywidgets.multi_spin import MultiSpinButton


class DateButton(MultiSpinButton):
	def __init__(self, date=None, **kwargs):
		MultiSpinButton.__init__(
			self,
			"/",
			(
				YearField(),
				MonthField(),
				DayField(),
			),
			**kwargs
		)
		if date is None:
			date = localtime()[:3]
		self.set_value(date)

	def get_jd(self, mode):
		y, m, d = self.get_value()
		return to_jd(y, m, d, mode)

	def changeMode(self, fromMode, toMode):
		self.set_value(jd_to(
			self.get_jd(fromMode),
			toMode,
		))

	def setMaxDay(self, _max):
		self.field.children[2].setMax(_max)
		self.update()
