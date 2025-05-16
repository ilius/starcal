from __future__ import annotations

from scal3.mywidgets.multi_spin import IntField
from scal3.ui_gtk.mywidgets.multi_spin import SingleSpinButton

__all__ = ["IntSpinButton"]


class IntSpinButton(SingleSpinButton):
	def __init__(self, minim: int, maxim: int, step: int = 0, **kwargs) -> None:
		if step == 0:
			step = 1
		SingleSpinButton.__init__(
			self,
			field=IntField(minim, maxim),
			step_inc=step,
			page_inc=step * 10,
			**kwargs,
		)

	def set_range(self, minim: int, maxim: int) -> None:
		self.field.children[0].setRange(minim, maxim)
		self.set_text(self.field.getText())

	def get_value(self) -> int:
		text = self.get_text().strip()
		if not text:
			return 0
		return int(text)
