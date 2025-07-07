from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.event.group.vcsEpochBase import (
	VcsEpochBaseWidgetClass as BaseWidgetClass,
)

if TYPE_CHECKING:
	from scal3.event_lib.vcs import VcsTagEventGroup

__all__ = ["WidgetClass"]


class WidgetClass(BaseWidgetClass):
	group: VcsTagEventGroup

	def __init__(self, group: VcsTagEventGroup) -> None:
		BaseWidgetClass.__init__(self, group)
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Tag Description"))
		label.set_xalign(0)
		self.sizeGroup.add_widget(label)
		pack(hbox, label)
		# --
		self.statCheck = gtk.CheckButton(label=_("Stat"))
		pack(hbox, self.statCheck)
		# --
		hbox.show_all()
		pack(self, hbox)

	def updateWidget(self) -> None:
		BaseWidgetClass.updateWidget(self)
		self.statCheck.set_active(self.group.showStat)

	def updateVars(self) -> None:
		BaseWidgetClass.updateVars(self)
		self.group.showStat = self.statCheck.get_active()
