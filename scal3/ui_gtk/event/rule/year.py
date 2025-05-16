from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.ui_gtk.mywidgets.num_ranges_entry import NumRangesEntry

if TYPE_CHECKING:
	from scal3.event_lib.rules import EventRule

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
