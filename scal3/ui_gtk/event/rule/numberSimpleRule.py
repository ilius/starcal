from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton

__all__ = ["WidgetClass"]


class WidgetClass(IntSpinButton):
	def __init__(self, rule) -> None:
		self.rule = rule
		IntSpinButton.__init__(self, 0, 999999)

	def updateWidget(self) -> None:
		self.set_value(self.rule.getData())

	def updateVars(self) -> None:
		self.rule.setData(self.get_value())
