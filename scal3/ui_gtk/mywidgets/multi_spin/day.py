from __future__ import annotations

from scal3.mywidgets.multi_spin import DayField, IntField
from scal3.ui_gtk.mywidgets.multi_spin import SingleSpinButton

__all__ = ["DaySpinButton"]


class DaySpinButton(SingleSpinButton[IntField, int]):
	def __init__(self) -> None:
		SingleSpinButton.__init__(
			self,
			field=DayField(0),
		)

	def set_range(self, minim: int, maxim: int) -> None:
		self.field.setRange(minim, maxim)
		self.set_text(self.field.getText())

	def setValue(self, value: int | None) -> None:
		if value is None:
			return
		self.field.setValue(value)
