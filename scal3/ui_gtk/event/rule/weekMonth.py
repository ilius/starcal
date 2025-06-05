from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.mywidgets.month_combo import MonthComboBox
from scal3.ui_gtk.mywidgets.weekday_combo import WeekDayComboBox

if TYPE_CHECKING:
	from scal3.event_lib.rules import WeekMonthEventRule

__all__ = ["WidgetClass"]


class WidgetClass(gtk.Box):
	def show(self) -> None:
		gtk.Box.show_all(self)

	def __init__(self, rule: WeekMonthEventRule) -> None:
		self.rule = rule
		# -----
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.w = self
		# ---
		nthCombo = gtk.ComboBoxText()
		for item in rule.wmIndexNames:
			nthCombo.append_text(item)
		pack(self, nthCombo)
		self.nthCombo = nthCombo
		# ---
		weekDayCombo = WeekDayComboBox()
		pack(self, weekDayCombo)
		self.weekDayCombo = weekDayCombo
		# ---
		pack(self, gtk.Label(label=_(" of ")))
		# ---
		monthCombo = MonthComboBox(True)
		monthCombo.build(rule.getCalType())
		pack(self, monthCombo)
		self.monthCombo = monthCombo

	def updateVars(self) -> None:
		self.rule.wmIndex = self.nthCombo.get_active()
		self.rule.weekDay = self.weekDayCombo.getValue()
		self.rule.month = self.monthCombo.getValue()

	def updateWidget(self) -> None:
		self.nthCombo.set_active(self.rule.wmIndex)
		self.weekDayCombo.setValue(self.rule.weekDay)
		self.monthCombo.setValue(self.rule.month)

	def changeRuleCalType(self, calType: int) -> None:
		if calType == self.rule.getCalType():
			return
		self.monthCombo.build(calType)
