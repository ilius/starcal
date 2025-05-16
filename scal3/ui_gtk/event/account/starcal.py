from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.locale_man import tr as _
from scal3.ui_gtk import HBox, gtk, pack
from scal3.ui_gtk.event.account import BaseWidgetClass

if TYPE_CHECKING:
	from scal3.event_lib.accounts import Account


class WidgetClass(BaseWidgetClass):
	def __init__(self, account: Account) -> None:
		BaseWidgetClass.__init__(self, account)
		# -----
		hbox = HBox()
		label = gtk.Label(label=_("Email"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.emailEntry = gtk.Entry()
		pack(hbox, self.emailEntry, 1, 1)
		pack(self, hbox)
		# ----
		hbox = HBox()
		label = gtk.Label(label=_("Password"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.passwordEntry = gtk.Entry()
		self.passwordEntry.set_visibility(False)
		pack(hbox, self.passwordEntry, 1, 1)
		pack(self, hbox)

	def updateWidget(self) -> None:
		BaseWidgetClass.updateWidget(self)
		self.emailEntry.set_text(self.account.email)
		self.passwordEntry.set_text(self.account.password)

	def updateVars(self) -> None:
		BaseWidgetClass.updateVars(self)
		self.account.email = self.emailEntry.get_text()
		self.account.password = self.passwordEntry.get_text()
