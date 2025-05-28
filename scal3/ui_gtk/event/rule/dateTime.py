from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.mywidgets.multi_spin.time_b import TimeButton

if TYPE_CHECKING:
	from scal3.event_lib.rules import DateAndTimeEventRule

__all__ = ["WidgetClass"]


class WidgetClass(gtk.Box):
	def __init__(self, rule: DateAndTimeEventRule) -> None:
		self.rule = rule
		# ---
		gtk.ComboBox.__init__(self)
		# ---
		self.dateInput = DateButton()
		pack(self, self.dateInput)
		# ---
		pack(self, gtk.Label(label="   " + _("Time")))
		self.timeInput = TimeButton()
		pack(self, self.timeInput)

	def updateWidget(self) -> None:
		self.dateInput.set_value(self.rule.date)
		self.timeInput.set_value(self.rule.time)

	def updateVars(self) -> None:
		year, month, day = self.dateInput.get_value()
		hour, minute, second = self.timeInput.get_value()
		self.rule.date = (year, month, day)
		self.rule.time = (hour, minute, second)

	def changeRuleCalType(self, calType: int) -> None:
		if calType == self.rule.getCalType():
			return
		self.updateVars()
		self.rule.changeCalType(calType)
		self.updateWidget()
