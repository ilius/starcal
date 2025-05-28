from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton

if TYPE_CHECKING:
	from scal3.event_lib.rules import DateEventRule

__all__ = ["WidgetClass"]


class WidgetClass(DateButton):
	def __init__(self, rule: DateEventRule) -> None:
		self.rule = rule
		DateButton.__init__(self)

	def updateWidget(self) -> None:
		self.set_value(self.rule.date)

	def updateVars(self) -> None:
		year, month, day = self.get_value()
		self.rule.date = (year, month, day)

	def changeRuleCalType(self, calType: int) -> None:
		if calType == self.rule.getCalType():
			return
		self.updateVars()
		self.rule.changeCalType(calType)
		self.updateWidget()
