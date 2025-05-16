from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.locale_man import tr as _
from scal3.ui_gtk import HBox, gtk, pack
from scal3.ui_gtk.event.group.vcsEpochBase import (
	VcsEpochBaseWidgetClass as BaseWidgetClass,
)

if TYPE_CHECKING:
	from scal3.event_lib.groups import EventGroup

__all__ = ["WidgetClass"]


class WidgetClass(BaseWidgetClass):
	def __init__(self, group: EventGroup) -> None:
		BaseWidgetClass.__init__(self, group)
		# ----
		hbox = HBox()
		label = gtk.Label(label=_("Commit Description"))
		label.set_xalign(0)
		self.sizeGroup.add_widget(label)
		pack(hbox, label)
		# --
		self.statCheck = gtk.CheckButton(label=_("Stat"))
		pack(hbox, self.statCheck)
		# --
		pack(hbox, gtk.Label(label="   "))
		# --
		self.authorCheck = gtk.CheckButton(label=_("Author"))
		pack(hbox, self.authorCheck)
		# --
		pack(hbox, gtk.Label(label="   "))
		# --
		self.shortHashCheck = gtk.CheckButton(label=_("Short Hash"))
		pack(hbox, self.shortHashCheck)
		# --
		hbox.show_all()
		pack(self, hbox)

	def updateWidget(self) -> None:
		BaseWidgetClass.updateWidget(self)
		self.authorCheck.set_active(self.group.showAuthor)
		self.shortHashCheck.set_active(self.group.showShortHash)
		self.statCheck.set_active(self.group.showStat)

	def updateVars(self) -> None:
		BaseWidgetClass.updateVars(self)
		self.group.showAuthor = self.authorCheck.get_active()
		self.group.showShortHash = self.shortHashCheck.get_active()
		self.group.showStat = self.statCheck.get_active()
