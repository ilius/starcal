from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.ui_gtk.mywidgets.num_ranges_entry import NumRangesEntry

if TYPE_CHECKING:
	from scal3.event_lib.rules import YearEventRule

__all__ = ["WidgetClass"]


class WidgetClass(NumRangesEntry):
	def show(self) -> None:
		NumRangesEntry.show(self.w)

	def __init__(self, rule: YearEventRule) -> None:
		self.rule = rule
		NumRangesEntry.__init__(self, 0, 9999, 10)
		self.w = self

	def updateWidget(self) -> None:
		self.setValues(self.rule.values)

	def updateVars(self) -> None:
		self.rule.values = self.getValues()

	def changeRuleCalType(self, calType: int) -> None:
		if calType == self.rule.getCalType():
			return
		self.updateVars()
		self.rule.changeCalType(calType)
		self.updateWidget()
