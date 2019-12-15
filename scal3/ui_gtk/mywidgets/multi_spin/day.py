#!/usr/bin/env python3
from scal3.mywidgets.multi_spin import DayField
from scal3.ui_gtk.mywidgets.multi_spin import SingleSpinButton


class DaySpinButton(SingleSpinButton):
	def __init__(self, **kwargs):
		SingleSpinButton.__init__(
			self,
			field=DayField(pad=0),
			**kwargs
		)

	def set_range(self, _min: int, _max: int):
		self.field.children[0].setRange(_min, _max)
		self.set_text(self.field.getText())
