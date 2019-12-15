#!/usr/bin/env python3
from scal3.mywidgets.multi_spin import FloatField
from scal3.ui_gtk.mywidgets.multi_spin import SingleSpinButton


class FloatSpinButton(SingleSpinButton):
	def __init__(self, _min, _max, digits, step=0.0, **kwargs):
		if digits < 1:
			raise ValueError(f"FloatSpinButton: invalid digits={digits!r}")
		if step == 0.0:
			step = 10 ** (1 - digits)
		SingleSpinButton.__init__(
			self,
			field=FloatField(_min, _max, digits),
			step_inc=step,
			page_inc=step * 10,
			**kwargs
		)

	def set_range(self, _min: float, _max: float):
		self.field.children[0].setRange(_min, _max)
		self.set_text(self.field.getText())
