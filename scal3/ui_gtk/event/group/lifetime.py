from scal3.event_lib.groups import EventGroup
from scal3.locale_man import tr as _
from scal3.ui_gtk import HBox, gtk, pack
from scal3.ui_gtk.event.group.group import WidgetClass as NormalWidgetClass

__all__ = ["WidgetClass"]


class WidgetClass(NormalWidgetClass):
	def __init__(self, group: EventGroup) -> None:
		NormalWidgetClass.__init__(self, group)
		# ----
		hbox = HBox()
		self.showSeparateYmdInputsCheck = gtk.CheckButton(
			label=_(
				"Show Separate Inputs for Year, Month and Day",
			),
		)
		pack(hbox, self.showSeparateYmdInputsCheck)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		hbox.show_all()

	def updateWidget(self) -> None:
		NormalWidgetClass.updateWidget(self)
		self.showSeparateYmdInputsCheck.set_active(
			self.group.showSeparateYmdInputs,
		)

	def updateVars(self) -> None:
		NormalWidgetClass.updateVars(self)
		self.group.showSeparateYmdInputs = self.showSeparateYmdInputsCheck.get_active()
