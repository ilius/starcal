from time import localtime

from scal3.mywidgets.multi_spin import HourField, Z60Field
from scal3.ui_gtk.mywidgets.multi_spin import MultiSpinButton

class HourMinuteButton(MultiSpinButton):
	def __init__(self, hm=None, **kwargs):
		MultiSpinButton.__init__(
			self,
			':',
			(
				HourField(),
				Z60Field(),
			),
			**kwargs
		)
		if hm==None:
			hm = localtime()[3:5]
		self.set_value(hm)
	get_value = lambda self: MultiSpinButton.get_value(self) + [0]
	def set_value(self, value):
		if isinstance(value, int):
			value = [value, 0]
		else:
			value = value[:2]
		MultiSpinButton.set_value(self, value)

