from __future__ import annotations

from typing import TYPE_CHECKING

from scal3 import core
from scal3.ui_gtk import gtk, pack

if TYPE_CHECKING:
	from scal3.event_lib.rules import WeekDayEventRule

__all__ = ["WidgetClass"]


class WidgetClass(gtk.Box):
	def show(self) -> None:
		gtk.Box.show_all(self)

	def __init__(self, rule: WeekDayEventRule) -> None:
		self.rule = rule
		# ---
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.w = self
		self.set_homogeneous(True)
		ls = [gtk.ToggleButton(label=item) for item in core.weekDayNameAb]
		start = core.firstWeekDay.v
		for i in range(7):
			pack(self, ls[(start + i) % 7], 1, 1)
		self.cbList = ls
		self.start = start

	def setStart(self, s: int) -> None:
		# not used, FIXME
		b = self
		ls = self.cbList
		for j in range(7):  # or range(6)
			b.reorder_child(ls[(s + j) % 7], j)
		self.start = s

	def updateVars(self) -> None:
		cbl = self.cbList
		self.rule.weekDayList = [j for j in range(7) if cbl[j].get_active()]

	def updateWidget(self) -> None:
		cbl = self.cbList
		for cb in cbl:
			cb.set_active(False)
		for j in self.rule.weekDayList:
			cbl[j].set_active(True)
