from scal3.locale_man import tr as _
from scal3.ui_gtk import HBox, gtk, pack
from scal3.ui_gtk.event import common
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton

__all__ = ["WidgetClass"]


class WidgetClass(common.WidgetClass):
	def __init__(self, event) -> None:
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
		self.dateInput.set_value(self.event.getDate())

	def updateVars(self) -> None:
		common.WidgetClass.updateVars(self)
		self.event.setDate(*self.dateInput.get_value())

	def calTypeComboChanged(self, _obj=None) -> None:
		# overwrite method from common.WidgetClass
		newCalType = self.calTypeCombo.get_active()
		self.dateInput.changeCalType(self.event.calType, newCalType)
		self.event.calType = newCalType
