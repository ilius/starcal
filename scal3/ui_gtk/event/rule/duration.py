from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.ui_gtk.event import common

if TYPE_CHECKING:
	from scal3.event_lib.rules import DurationEventRule

__all__ = ["WidgetClass"]


class WidgetClass(common.DurationInputBox):
	def __init__(self, rule: DurationEventRule) -> None:
		self.rule = rule
		common.DurationInputBox.__init__(self)
		self.w = self

	def updateWidget(self) -> None:
		self.setDuration(self.rule.value, self.rule.unit)

	def updateVars(self) -> None:
		self.rule.value, self.rule.unit = self.getDuration()
