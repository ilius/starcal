from scal3.mywidgets.multi_spin import DayField
from scal3.ui_gtk.mywidgets.multi_spin import SingleSpinButton

__all__ = ["DaySpinButton"]


class DaySpinButton(SingleSpinButton):
	def __init__(self, **kwargs):
		SingleSpinButton.__init__(
			self,
			field=DayField(pad=0),
			**kwargs,
		)

	def set_range(self, minim: int, maxim: int):
		self.field.children[0].setRange(minim, maxim)
		self.set_text(self.field.getText())
