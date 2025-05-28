from __future__ import annotations

from scal3.mywidgets.multi_spin import DayField
from scal3.ui_gtk.mywidgets.multi_spin import SingleSpinButton

__all__ = ["DaySpinButton"]


class DaySpinButton(SingleSpinButton):
	def __init__(self, **kwargs) -> None:
		SingleSpinButton.__init__(
			self,
			field=DayField(pad=0),
			**kwargs,
		)

	def set_range(self, minim: int, maxim: int) -> None:
		self.field.setRange(minim, maxim)
		self.set_text(self.field.getText())
