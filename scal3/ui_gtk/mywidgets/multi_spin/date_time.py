from time import localtime

from scal3.cal_types import to_jd
from scal3.mywidgets.multi_spin import (
	ContainerField,
	YearField,
	MonthField,
	DayField,
	HourField,
	Z60Field,
)
from scal3.ui_gtk.mywidgets.multi_spin import MultiSpinButton


class DateTimeButton(MultiSpinButton):
	def __init__(self, date_time=None, **kwargs):
		MultiSpinButton.__init__(
			self,
			' ',
			(
				ContainerField(
					'/',
					YearField(),
					MonthField(),
					DayField(),
				),
				ContainerField(
					':',
					HourField(),
					Z60Field(),
					Z60Field(),
				),
			),
			#StrConField('seconds'),
			**kwargs
		)
		if date_time is None:
			date_time = localtime()[:6]
		self.set_value(date_time)

	def get_epoch(self, mode):
		from scal3.time_utils import getEpochFromJhms
		date, hms = self.get_value()
		return getEpochFromJhms(
			to_jd(date[0], date[1], date[2], mode),
			*hms
		)
