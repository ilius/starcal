#!/usr/bin/env python3
from scal3.ui_gtk import *
from scal3.mywidgets.multi_spin import IntField
from scal3.ui_gtk.mywidgets.multi_spin import SingleSpinButton


class IntSpinButton(SingleSpinButton):
	def __init__(self, _min, _max, step=0, **kwargs):
		if step == 0:
			step = 1
		SingleSpinButton.__init__(
			self,
			field=IntField(_min, _max),
			step_inc=step,
			page_inc=step * 10,
			**kwargs
		)

	def set_range(self, _min: int, _max: int):
		self.field.children[0].setRange(_min, _max)
		self.set_text(self.field.getText())

	def get_value(self):
		text = self.get_text().strip()
		if not text:
			return 0
		return int(text)
