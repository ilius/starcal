from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.event import common
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton

if TYPE_CHECKING:
	from scal3.event_lib.events import DailyNoteEvent

__all__ = ["WidgetClass"]


class WidgetClass(common.WidgetClass):
	_event: DailyNoteEvent

	def __init__(self, event: DailyNoteEvent) -> None:
		common.WidgetClass.__init__(self, event)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Date")))
		self.dateInput = DateButton()
		pack(hbox, self.dateInput)
		pack(self, hbox)
		# -------------
		# self.filesBox = common.FilesBox(self._event)
		# pack(self, self.filesBox)

	def updateWidget(self) -> None:
		common.WidgetClass.updateWidget(self)
		date = self._event.getDate()
		assert date is not None
		self.dateInput.setDate(date)

	def updateVars(self) -> None:
		common.WidgetClass.updateVars(self)
		self._event.setDate(*self.dateInput.get_value())

	def calTypeComboChanged(self, _w: gtk.Widget | None = None) -> None:
		# overwrite method from common.WidgetClass
		newCalType = self.calTypeCombo.getActive()
		assert newCalType is not None
		self.dateInput.changeCalType(self._event.calType, newCalType)
		self._event.calType = newCalType
