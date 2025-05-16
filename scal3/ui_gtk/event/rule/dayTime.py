from scal3.event_lib.rules import EventRule
from scal3.ui_gtk.mywidgets.multi_spin.time_b import TimeButton

__all__ = ["WidgetClass"]


class WidgetClass(TimeButton):
	def __init__(self, rule: EventRule) -> None:
		self.rule = rule
		TimeButton.__init__(self)

	def updateWidget(self) -> None:
		self.set_value(self.rule.dayTime)

	def updateVars(self) -> None:
		self.rule.dayTime = self.get_value()
