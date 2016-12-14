from scal3.mywidgets.multi_spin import DayField
from scal3.ui_gtk.mywidgets.multi_spin import SingleSpinButton

class DaySpinButton(SingleSpinButton):
	def __init__(self, **kwargs):
		SingleSpinButton.__init__(
			self,
			DayField(pad=0),
			**kwargs
		)

