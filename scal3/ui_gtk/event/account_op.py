from scal3 import event_lib, ui
from scal3.event_lib import state as event_state
from scal3.event_lib.accounts import Account
from scal3.locale_man import tr as _
from scal3.ui_gtk import HBox, gtk, pack
from scal3.ui_gtk.event import makeWidget
from scal3.ui_gtk.utils import dialog_add_button

__all__ = ["AccountEditorDialog"]


class AccountEditorDialog(gtk.Dialog):
	def __init__(self, account: Account | None = None, **kwargs) -> None:
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_("Edit Account") if account else _("Add New Account"))
		# ---
		dialog_add_button(
			self,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
			res=gtk.ResponseType.CANCEL,
		)
		dialog_add_button(
			self,
			imageName="dialog-ok.svg",
			label=_("_Save"),
			res=gtk.ResponseType.OK,
		)
		# --
		self.connect("response", lambda _w, _e: self.hide())
		# -------
		self.account = account
		self.activeWidget = None
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
			defaultAccountTypeIndex = 0
			combo.set_active(defaultAccountTypeIndex)
			self.account = ui.withFS(
				event_lib.classes.account[defaultAccountTypeIndex](),
			)
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
		account = ui.withFS(cls())
		if self.account:
			account.copyFrom(self.account)
			account.setId(self.account.id)
			del self.account
		if self.isNew:
			account.title = cls.desc  # FIXME
		self.account = account
		self.activeWidget = makeWidget(account)
		pack(self.vbox, self.activeWidget)

	def run(self) -> Account | None:
		if self.activeWidget is None or self.account is None:
			return None
		if gtk.Dialog.run(self) != gtk.ResponseType.OK:
			return None
		self.activeWidget.updateVars()
		self.account.save()
		if self.isNew:
			event_state.lastIds.save()
		else:
			ui.eventAccounts[self.account.id] = self.account
		self.destroy()
		return self.account


class FetchRemoteGroupsDialog(gtk.Dialog):
	def __init__(self, account: Account, **kwargs) -> None:
		gtk.Dialog.__init__(self, **kwargs)
		self.account = account
