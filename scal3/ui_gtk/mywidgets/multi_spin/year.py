from scal3.mywidgets.multi_spin import IntField, YearField
from scal3.ui_gtk.mywidgets.multi_spin import SingleSpinButton

__all__ = ["YearSpinButton"]


class YearSpinButton(SingleSpinButton[IntField, int]):
	def __init__(self, **kwargs) -> None:
		SingleSpinButton.__init__(
			self,
			YearField(),
			**kwargs,
		)
