from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.locale_man import tr as _
from scal3.ui_gtk import HBox, gtk, pack
from scal3.ui_gtk.event import common
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton

if TYPE_CHECKING:
	from scal3.event_lib.events import DailyNoteEvent

__all__ = ["WidgetClass"]


class WidgetClass(common.WidgetClass):
	event: DailyNoteEvent

	def __init__(self, event: DailyNoteEvent) -> None:
		common.WidgetClass.__init__(self, event)
		# ---
		hbox = HBox()
		pack(hbox, gtk.Label(label=_("Date")))
		self.dateInput = DateButton()
		pack(hbox, self.dateInput)
		pack(self, hbox)
		# -------------
		# self.filesBox = common.FilesBox(self.event)
		# pack(self, self.filesBox)

	def updateWidget(self) -> None:
		common.WidgetClass.updateWidget(self)
		date = self.event.getDate()
		assert date is not None
		self.dateInput.setDate(date)

	def updateVars(self) -> None:
		common.WidgetClass.updateVars(self)
		self.event.setDate(*self.dateInput.get_value())

	def calTypeComboChanged(self, _w: gtk.Widget | None = None) -> None:
		# overwrite method from common.WidgetClass
		newCalType = self.calTypeCombo.get_active()
		assert newCalType is not None
		self.dateInput.changeCalType(self.event.calType, newCalType)
		self.event.calType = newCalType
