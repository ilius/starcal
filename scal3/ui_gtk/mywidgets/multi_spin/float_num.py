from __future__ import annotations

from scal3.mywidgets.multi_spin import FloatField
from scal3.ui_gtk.mywidgets.multi_spin import SingleSpinButton

__all__ = ["FloatSpinButton"]


class FloatSpinButton(SingleSpinButton):
	def __init__(
		self,
		minim: float,
		maxim: float,
		digits: int,
		step: float = 0.0,
		**kwargs,
	) -> None:
		if digits < 1:
			raise ValueError(f"FloatSpinButton: invalid {digits=}")
		if step == 0.0:
			step = 10 ** (1 - digits)
		SingleSpinButton.__init__(
			self,
			field=FloatField(minim, maxim, digits),
			step_inc=step,
			page_inc=step * 10,
			**kwargs,
		)

	def set_range(self, minim: float, maxim: float) -> None:
		self.field.children[0].setRange(minim, maxim)
		self.set_text(self.field.getText())
