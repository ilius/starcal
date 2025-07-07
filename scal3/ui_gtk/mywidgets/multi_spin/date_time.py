from __future__ import annotations

from collections.abc import Sequence
from time import localtime

from scal3.cal_types import convert, to_jd
from scal3.mywidgets.multi_spin import (
	ContainerField,
	DateTimeFieldType,
	DayField,
	HourField,
	MonthField,
	YearField,
	Z60Field,
)
from scal3.ui_gtk.mywidgets.multi_spin import MultiSpinButton

__all__ = ["DateTimeButton"]


class DateTimeButton(MultiSpinButton[DateTimeFieldType, Sequence[Sequence[int]]]):
	def __init__(
		self,
		date_time: tuple[int, int, int, int, int, int] | None = None,
	) -> None:
		MultiSpinButton.__init__(
			self,
			field=ContainerField(
				" ",
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
		)
		if date_time is None:
			date_time = localtime()[:6]
		self.set_value([date_time])

	def get_epoch(self, calType: int) -> int:
		from scal3.time_utils import getEpochFromJhms

		date, hms = self.get_value()
		h, m, s = hms
		return getEpochFromJhms(
			to_jd(date[0], date[1], date[2], calType),
			h,
			m,
			s,
		)

	def changeCalType(self, fromType: int, toType: int) -> None:
		date, hms = self.get_value()
		newDate = convert(date[0], date[1], date[2], fromType, toType)
		self.set_value((newDate, hms))
