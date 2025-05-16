from scal3.event_lib.groups import EventGroup
from scal3.locale_man import tr as _
from scal3.ui_gtk import HBox, gtk, pack
from scal3.ui_gtk.event.group.vcsBase import VcsBaseWidgetClass

__all__ = ["VcsEpochBaseWidgetClass"]


class VcsEpochBaseWidgetClass(VcsBaseWidgetClass):
	def __init__(self, group: EventGroup) -> None:
		VcsBaseWidgetClass.__init__(self, group)
		# ------
		hbox = HBox()
		label = gtk.Label(label=_("Show Seconds"))
		label.set_xalign(0)
		self.sizeGroup.add_widget(label)
		pack(hbox, label)
		pack(hbox, label)
		self.showSecondsCheck = gtk.CheckButton(label="")
		pack(hbox, self.showSecondsCheck)
		hbox.show_all()
		pack(self, hbox)

	def updateWidget(self) -> None:
		VcsBaseWidgetClass.updateWidget(self)
		self.showSecondsCheck.set_active(self.group.showSeconds)

	def updateVars(self) -> None:
		VcsBaseWidgetClass.updateVars(self)
		self.group.showSeconds = self.showSecondsCheck.get_active()
