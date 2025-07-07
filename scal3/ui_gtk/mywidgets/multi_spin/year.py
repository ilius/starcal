from scal3.mywidgets.multi_spin import IntField, YearField
from scal3.ui_gtk.mywidgets.multi_spin import SingleSpinButton

__all__ = ["YearSpinButton"]


class YearSpinButton(SingleSpinButton[IntField, int]):
	def __init__(
		self,
		# arrow_select: bool = True,
		# step_inc: float = 1,
		# page_inc: float = 10,
	) -> None:
		SingleSpinButton.__init__(
			self,
			YearField(),
			# arrow_select=arrow_select,
			# step_inc=step_inc,
			# page_inc=page_inc,
		)
