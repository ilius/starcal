from time import localtime

from scal3.cal_types import convert, to_jd
from scal3.mywidgets.multi_spin import (
	ContainerField,
	DayField,
	HourField,
	MonthField,
	YearField,
	Z60Field,
)
from scal3.ui_gtk.mywidgets.multi_spin import MultiSpinButton

__all__ = ["DateTimeButton"]


class DateTimeButton(MultiSpinButton):
	def __init__(
		self,
		date_time: tuple[int, int, int, int, int, int] | None = None,
		**kwargs,
	) -> None:
		MultiSpinButton.__init__(
			self,
			sep=" ",
			fields=(
				ContainerField(
					"/",
					YearField(),
					MonthField(),
					DayField(),
				),
				ContainerField(
					":",
					HourField(),
					Z60Field(),
					Z60Field(),
				),
				# StrConField("seconds"),
			),
			**kwargs,
		)
		if date_time is None:
			date_time = localtime()[:6]
		self.set_value(date_time)

	def get_epoch(self, calType: int) -> int:
		from scal3.time_utils import getEpochFromJhms

		date, hms = self.get_value()
		return getEpochFromJhms(
			to_jd(date[0], date[1], date[2], calType),
			*hms,
		)

	def changeCalType(self, fromType: int, toType: int) -> None:
		date, hms = self.get_value()
		newDate = convert(date[0], date[1], date[2], fromType, toType)
		self.set_value((newDate, hms))
