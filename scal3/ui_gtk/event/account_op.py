from __future__ import annotations

from typing import TYPE_CHECKING

from scal3 import event_lib
from scal3.event_lib import ev
from scal3.locale_man import tr as _
from scal3.ui_gtk import Dialog, HBox, gtk, pack
from scal3.ui_gtk.event import EventWidgetType, makeWidget
from scal3.ui_gtk.utils import dialog_add_button

if TYPE_CHECKING:
	from scal3.event_lib.accounts import Account
	from scal3.event_lib.pytypes import AccountType

__all__ = ["AccountEditorDialog"]


class AccountEditorDialog(Dialog):
	vbox: gtk.Box  # type: ignore[assignment]

	def __init__(self, account: AccountType | None = None, **kwargs) -> None:
		Dialog.__init__(self, **kwargs)
		self.set_title(_("Edit Account") if account else _("Add New Account"))
		# ---
		dialog_add_button(
			self,
			res=gtk.ResponseType.CANCEL,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
		)
		dialog_add_button(
			self,
			res=gtk.ResponseType.OK,
			imageName="dialog-ok.svg",
			label=_("_Save"),
		)
		# --
		self.connect("response", lambda _w, _e: self.hide())
		# -------
		self.account = account
		self.activeWidget: EventWidgetType | None = None
		# -------
		hbox = HBox()
		combo = gtk.ComboBoxText()
		for cls in event_lib.classes.account:
			combo.append_text(cls.desc)
		pack(hbox, gtk.Label(label=_("Account Type")))
		pack(hbox, combo)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self.vbox, hbox)
		# ----
		if self.account:
			self.isNew = False
			combo.set_active(
				event_lib.classes.account.names.index(self.account.name),
			)
		else:
			self.isNew = True
			acls = event_lib.classes.account.byName["starcal"]
			combo.set_active(event_lib.classes.account.index(acls))
			self.account = acls()
			# self.account.fs = core.fs
		self.activeWidget = None
		combo.connect("changed", self.typeChanged)
		self.comboType = combo
		self.vbox.show_all()
		self.typeChanged()

	def dateModeChanged(self, combo: gtk.ComboBox) -> None:
		pass

	def typeChanged(self, _combo: gtk.ComboBox | None = None) -> None:
		if self.activeWidget:
			self.activeWidget.updateVars()
			self.activeWidget.destroy()
		cls = event_lib.classes.account[self.comboType.get_active()]
		account = cls()
		if self.account:
			account.copyFrom(self.account)
			account.setId(self.account.id)
			del self.account
		if self.isNew:
			account.title = cls.desc  # FIXME
		self.account = account
		self.activeWidget = makeWidget(account)
		assert self.activeWidget is not None
		pack(self.vbox, self.activeWidget.w)

	def run(self) -> AccountType | None:
		if self.activeWidget is None or self.account is None:
			return None
		if Dialog.run(self) != gtk.ResponseType.OK:
			return None
		self.activeWidget.updateVars()
		self.account.save()
		if self.isNew:
			ev.lastIds.save()
		else:
			ev.accounts[self.account.id] = self.account
		self.destroy()
		return self.account


class FetchRemoteGroupsDialog(Dialog):
	def __init__(self, account: Account, **kwargs) -> None:
		Dialog.__init__(self, **kwargs)
		self.account = account
