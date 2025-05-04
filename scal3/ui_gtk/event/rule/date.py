from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton

__all__ = ["WidgetClass"]


class WidgetClass(DateButton):
	def __init__(self, rule) -> None:
		self.rule = rule
		DateButton.__init__(self)

	def updateWidget(self) -> None:
		self.set_value(self.rule.date)

	def updateVars(self) -> None:
		self.rule.date = self.get_value()

	def changeCalType(self, calType) -> None:
		if calType == self.rule.getCalType():
			return
		self.updateVars()
		self.rule.changeCalType(calType)
		self.updateWidget()
