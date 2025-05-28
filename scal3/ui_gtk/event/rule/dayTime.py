from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.ui_gtk.mywidgets.multi_spin.time_b import TimeButton

if TYPE_CHECKING:
	from scal3.event_lib.rules import DayTimeEventRule

__all__ = ["WidgetClass"]


class WidgetClass(TimeButton):
	def __init__(self, rule: DayTimeEventRule) -> None:
		self.rule = rule
		TimeButton.__init__(self)

	def updateWidget(self) -> None:
		self.set_value(self.rule.dayTime)

	def updateVars(self) -> None:
		h, m, d = self.get_value()
		self.rule.dayTime = (h, m, d)
