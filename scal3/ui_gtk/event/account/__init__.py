from __future__ import annotations

from scal3 import logger

log = logger.get()

from typing import TYPE_CHECKING

from scal3 import ui
from scal3.event_lib import ev
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.utils import (
	IdComboBox,
	labelImageButton,
	showError,
)

if TYPE_CHECKING:
	from scal3.event_lib.accounts import Account
	from scal3.event_lib.pytypes import AccountType

__all__ = [
	"AccountCombo",
	"AccountGroupBox",
	"AccountGroupCombo",
	"BaseWidgetClass",
]


class BaseWidgetClass(gtk.Box):
	def show(self) -> None:
		gtk.Box.show_all(self)

	def __init__(self, account: Account) -> None:
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.w = self
		self.baseAccount = account
		# --------
		self.sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# -----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Title"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.titleEntry = gtk.Entry()
		pack(hbox, self.titleEntry, 1, 1)
		pack(self, hbox)

	def updateWidget(self) -> None:
		self.titleEntry.set_text(self.baseAccount.title)

	def updateVars(self) -> None:
		self.baseAccount.title = self.titleEntry.get_text()


class AccountCombo(IdComboBox):
	def __init__(self) -> None:
		ls = gtk.ListStore(int, str)
		gtk.ComboBox.__init__(self)
		self.set_model(ls)
		# ---
		cell = gtk.CellRendererText()
		self.pack_start(cell, expand=True)
		self.add_attribute(cell, "text", 1)
		# ---
		ls.append([-1, _("None")])
		for account in ev.accounts:
			if account.enable:
				ls.append([account.id, account.title])
		# ---
		gtk.ComboBox.set_active(self, 0)


class AccountGroupCombo(gtk.ComboBox):
	def __init__(self) -> None:
		self.account: AccountType | None = None
		# ---
		ls = gtk.ListStore(str, str)
		gtk.ComboBox.__init__(self)
		self.set_model(ls)
		self._listStore = ls
		# ---
		cell = gtk.CellRendererText()
		self.pack_start(cell, expand=True)
		self.add_attribute(cell, "text", 1)

	def setGroupId(self, ident: str | None) -> None:
		if ident is None:
			gtk.ComboBox.set_active(self, -1)
			return
		ls = self.get_model()
		for i in range(len(ls)):
			if ls[i][0] == ident:
				gtk.ComboBox.set_active(self, i)
				return

	def getGroupId(self) -> str | None:
		i = gtk.ComboBox.get_active(self)
		if i == -1 or i is None:
			return None
		model = self.get_model()
		if model is None:
			log.info("IdComboBox.get_active: model is None")
		try:
			return model[i][0]  # type: ignore[no-any-return]
		except IndexError:
			return None

	def getAccount(self) -> AccountType | None:
		return self.account

	def setAccount(self, account: AccountType) -> None:
		self.account = account
		self.updateList()

	def updateList(self) -> None:
		if self.account is None:
			return
		ls = self._listStore
		ls.clear()
		if self.account:
			for groupData in self.account.remoteGroups:
				ls.append(
					[
						str(groupData["id"]),
						groupData["title"],
					],
				)


class AccountGroupBox(gtk.Box):
	def __init__(
		self,
		accountCombo: gtk.ComboBox | None = None,
	) -> None:
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.combo = AccountGroupCombo()
		pack(self, self.combo)
		# --
		button = labelImageButton(
			label=_("Fetch"),
			# TODO: imageName="fetch-account.svg",
		)
		button.connect("clicked", self.onFetchClick)
		pack(self, button)
		# --
		label = gtk.Label()
		label.set_xalign(0.1)
		pack(self, label, 1, 1)
		self.msgLabel = label
		# ---
		if accountCombo:
			accountCombo.connect("changed", self.accountComboChanged)

	def accountComboChanged(self, _combo: gtk.ComboBox) -> None:
		self.combo.updateList()

	def onFetchClick(self, _w: gtk.Widget | None = None) -> None:
		combo = self.combo
		account = combo.account
		if not account:
			self.msgLabel.set_label(_("No account selected"))
			return
		self.msgLabel.set_label(_("Fatching"))
		while gtk.events_pending():
			gtk.main_iteration_do(False)
		try:
			account.fetchGroups()
		except Exception as e:
			self.msgLabel.set_label(_("Error"))
			msg = _("Error in fetching remote groups") + "\n" + str(e)
			showError(msg, transient_for=ui.eventManDialog.w)
			return
		else:
			self.msgLabel.set_label("")
			account.save()
		self.combo.updateList()
