from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.mywidgets.multi_spin.time_b import TimeButton

if TYPE_CHECKING:
	from scal3.event_lib.rules import DayTimeRangeEventRule

__all__ = ["WidgetClass"]


class WidgetClass(gtk.Box):
	def __init__(self, rule: DayTimeRangeEventRule) -> None:
		self.rule = rule
		# ---
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		# ---
		self.startTbox = TimeButton()
		self.endTbox = TimeButton()
		pack(self, self.startTbox)
		pack(self, gtk.Label(label=" " + _("To", ctx="time range") + " "))
		pack(self, self.endTbox)

	def updateWidget(self) -> None:
		self.startTbox.set_value(self.rule.dayTimeStart)
		self.endTbox.set_value(self.rule.dayTimeEnd)

	def updateVars(self) -> None:
		s1, s2, s3 = self.startTbox.get_value()
		e1, e2, e3 = self.endTbox.get_value()
		self.rule.dayTimeStart = (s1, s2, s3)
		self.rule.dayTimeEnd = (e1, e2, e3)
