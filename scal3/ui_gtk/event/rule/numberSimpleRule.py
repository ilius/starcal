
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton


class WidgetClass(IntSpinButton):
	def __init__(self, rule):
		self.rule = rule
		IntSpinButton.__init__(self, 0, 999999)

	def updateWidget(self):
		self.set_value(self.rule.getData())

	def updateVars(self):
		self.rule.setData(self.get_value())
