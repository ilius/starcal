from scal3.event_lib.rules import EventRule
from scal3.ui_gtk.mywidgets.num_ranges_entry import NumRangesEntry

__all__ = ["WidgetClass"]


class WidgetClass(NumRangesEntry):
	def __init__(self, rule: EventRule) -> None:
		self.rule = rule
		NumRangesEntry.__init__(self, 0, 9999, 10)

	def updateWidget(self) -> None:
		self.setValues(self.rule.values)

	def updateVars(self) -> None:
		self.rule.values = self.getValues()

	def changeCalType(self, calType: str) -> None:
		if calType == self.rule.getCalType():
			return
		self.updateVars()
		self.rule.changeCalType(calType)
		self.updateWidget()
