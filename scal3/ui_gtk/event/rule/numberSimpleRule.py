from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton

if TYPE_CHECKING:
	from scal3.event_lib.rules import EventRule

__all__ = ["WidgetClass"]


class WidgetClass(IntSpinButton):
	def __init__(self, rule: EventRule) -> None:
		self.rule = rule
		IntSpinButton.__init__(self, 0, 999999)

	def updateWidget(self) -> None:
		self.set_value(self.rule.getRuleValue())

	def updateVars(self) -> None:
		self.rule.setRuleValue(self.get_value())
