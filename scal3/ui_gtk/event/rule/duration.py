from scal3.ui_gtk.event import common

__all__ = ["WidgetClass"]


class WidgetClass(common.DurationInputBox):
	def __init__(self, rule) -> None:
		self.rule = rule
		common.DurationInputBox.__init__(self)

	def updateWidget(self) -> None:
		self.setDuration(self.rule.value, self.rule.unit)

	def updateVars(self) -> None:
		self.rule.value, self.rule.unit = self.getDuration()
