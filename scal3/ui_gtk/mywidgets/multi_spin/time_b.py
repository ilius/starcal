from time import localtime

from scal3.mywidgets.multi_spin import HourField, Z60Field
from scal3.ui_gtk.mywidgets.multi_spin import MultiSpinButton

__all__ = ["TimeButton"]


class TimeButton(MultiSpinButton):
	def __init__(self, hms=None, **kwargs) -> None:
		MultiSpinButton.__init__(
			self,
			sep=":",
			fields=(
				HourField(),
				Z60Field(),
				Z60Field(),
			),
			**kwargs,
		)
		if hms is None:
			hms = localtime()[3:6]
		self.set_value(hms)

	def get_seconds(self):
		h, m, s = self.get_value()
		return h * 3600 + m * 60 + s

	def set_seconds(self, seconds) -> None:
		_day, s = divmod(seconds, 86400)
		# do what with "day" ?
		h, s = divmod(s, 3600)
		m, s = divmod(s, 60)
		self.set_value((h, m, s))
		# return day
