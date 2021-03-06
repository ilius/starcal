#!/usr/bin/env python3
from scal3.ui_gtk import *
from scal3.mywidgets.multi_spin import IntField
from scal3.ui_gtk.mywidgets.multi_spin import SingleSpinButton


class IntSpinButton(SingleSpinButton):
	def __init__(self, _min, _max, **kwargs):
		SingleSpinButton.__init__(
			self,
			IntField(_min, _max),
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
