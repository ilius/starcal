from scal3.locale_man import tr as _
from scal3.ui_gtk import HBox, gtk, pack
from scal3.ui_gtk.event import common
from scal3.ui_gtk.event.group.group import WidgetClass as NormalWidgetClass

__all__ = ["WidgetClass"]


class WidgetClass(NormalWidgetClass):
	def __init__(self, group) -> None:
		NormalWidgetClass.__init__(self, group)
		# ---
		hbox = HBox()
		label = gtk.Label(label=_("Default Task Duration"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.defaultDurationBox = common.DurationInputBox()
		pack(hbox, self.defaultDurationBox)
		pack(self, hbox)
		hbox.show_all()

	def updateWidget(self) -> None:  # FIXME
		NormalWidgetClass.updateWidget(self)
		self.defaultDurationBox.setDuration(*self.group.defaultDuration)

	def updateVars(self) -> None:
		NormalWidgetClass.updateVars(self)
		self.group.defaultDuration = self.defaultDurationBox.getDuration()
