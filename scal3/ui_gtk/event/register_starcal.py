#!/usr/bin/env python3
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scal3 import logger

log = logger.get()
from scal3 import core, locale_man, ui
from scal3.event_lib import ev
from scal3.locale_man import tr as _
from scal3.ui_gtk import Dialog, HBox, gdk, gtk, pack
from scal3.ui_gtk.mywidgets.buttonbox import MyHButtonBox
from scal3.ui_gtk.mywidgets.dialog import MyDialog

if TYPE_CHECKING:
	from scal3.account.starcal import StarCalendarAccount
	from scal3.event_lib.pytypes import AccountType

__all__ = ["StarCalendarRegisterDialog"]


class StarCalendarRegisterDialog(MyDialog):
	def __init__(self, **kwargs) -> None:
		Dialog.__init__(self, **kwargs)
		# ---
		self.set_title(_("Register at StarCalendar.net"))
		self.resize(600, 300)
		self.connect("delete-event", self.onDeleteEvent)
		self.set_transient_for(None)
		self.set_type_hint(gdk.WindowTypeHint.NORMAL)
		# ---
		self.buttonBox = MyHButtonBox()
		self.okButton = self.buttonBox.add_ok(self.onOkClick)
		self.cancelButton = self.buttonBox.add_cancel(self.onCancelClick)
		self.vbox.pack_end(self.buttonBox, expand=False, fill=False, padding=0)
		# ---
		sgroupLabel = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# ---
		hbox = HBox(spacing=5)
		label = gtk.Label(label=_("Email"))
		label.set_xalign(0)
		pack(hbox, label, 0, 0)
		sgroupLabel.add_widget(label)
		self.emailEntry = gtk.Entry()
		self.emailEntry.set_direction(gtk.TextDirection.LTR)
		pack(hbox, self.emailEntry, 1, 1, 10)
		pack(self.vbox, hbox, 0, 0, 10)
		# ---
		hbox = HBox(spacing=5)
		label = gtk.Label(label=_("Password"))
		label.set_xalign(0)
		pack(hbox, label, 0, 0)
		sgroupLabel.add_widget(label)
		self.passwordEntry = gtk.Entry()
		self.passwordEntry.set_visibility(False)
		self.passwordEntry.set_direction(gtk.TextDirection.LTR)
		pack(hbox, self.passwordEntry, 1, 1, 10)
		pack(self.vbox, hbox, 0, 0, 10)
		# ---
		hbox = HBox(spacing=5)
		label = gtk.Label(label=_("Repeat Password"))
		label.set_xalign(0)
		pack(hbox, label, 0, 0)
		sgroupLabel.add_widget(label)
		self.passwordEntry2 = gtk.Entry()
		self.passwordEntry2.set_visibility(False)
		self.passwordEntry2.set_direction(gtk.TextDirection.LTR)
		pack(hbox, self.passwordEntry2, 1, 1, 10)
		pack(self.vbox, hbox, 0, 0, 10)
		# ---
		hbox = HBox(spacing=5)
		label = gtk.Label(label=_("Name (Optional)"))
		label.set_xalign(0)
		pack(hbox, label, 0, 0)
		sgroupLabel.add_widget(label)
		self.nameEntry = gtk.Entry()
		# self.nameEntry.set_direction(gtk.TextDirection.LTR)
		pack(hbox, self.nameEntry, 1, 1, 10)
		pack(self.vbox, hbox, 0, 0, 10)
		# ---
		hbox = HBox(spacing=5)
		label = gtk.Label()
		label.set_xalign(0)
		# make text color red
		labelColor = gdk.Color(65535, 0, 0)  # type: ignore[call-arg]
		label.modify_fg(gtk.StateType.NORMAL, labelColor)
		pack(hbox, label, 0, 0)
		pack(self.vbox, hbox, 0, 0, 10)
		self.errorLabel = label
		# ---
		self.emailEntry.connect("changed", self.updateOkSensitive)
		self.passwordEntry.connect("changed", self.updateOkSensitive)
		self.passwordEntry2.connect("changed", self.updateOkSensitive)
		self.updateOkSensitive()
		# ---
		self.vbox.show_all()
		# ---

	def canSubmit(self) -> bool:
		if not self.emailEntry.get_text():
			return False

		if not self.passwordEntry.get_text():
			return False

		if not self.passwordEntry2.get_text():
			return False

		if self.passwordEntry2.get_text() != self.passwordEntry.get_text():
			self.errorLabel.set_text(_("Two passwords do not match"))
			return False

		return True

	def updateOkSensitive(self, *_args) -> None:
		ok = self.canSubmit()
		self.okButton.set_sensitive(ok)
		if ok:
			self.errorLabel.set_text("")

	def doRegister(self) -> str | None:
		"""Return None if successful, or error string if failed."""
		import requests

		email = self.emailEntry.get_text()
		password = self.passwordEntry.get_text()
		fullName = self.nameEntry.get_text()

		accountCls: type[StarCalendarAccount] = ev.accounts.loadClass("starcal")  # type: ignore[assignment]
		assert accountCls is not None

		res = requests.post(
			accountCls.serverUrl + "auth/register/",
			json={
				"email": email,
				"password": password,
				"fullName": fullName,
			},
		)
		error = ""
		token = ""
		try:
			data = res.json()
		except Exception:
			error = f"non-json data: {res.text}"
		else:
			error = data.get("error", "")
			token = data.get("token", "")

		if error:
			self.errorLabel.set_text(_(error))
			return error

		account: AccountType = accountCls()  # type: ignore[assignment] # FIXME
		account.setDict(
			{
				"title": "StarCalendar: " + email,
				"email": email,
				"password": password,
				"lastToken": token,
			},
		)
		account.save()
		ev.accounts.append(account)
		ev.accounts.save()
		if ui.prefWindow:
			ui.prefWindow.refreshAccounts()  # messy, I know, FIXME
		# ---
		while gtk.events_pending():
			gtk.main_iteration_do(False)

		try:
			account.fetchGroups()
		except Exception as e:
			log.error("error in fetchGroups: {e}")
			return str(e)
		account.save()
		return None

	def onOkClick(self, _w: gtk.Widget) -> None:
		error = self.waitingDo(self.doRegister)
		if not error:
			self.destroy()

	def onCancelClick(self, _w: gtk.Widget) -> None:
		self.destroy()

	def onDeleteEvent(self, _w: gtk.Widget, _ge: Any) -> bool:
		self.destroy()
		return True


if __name__ == "__main__":
	if locale_man.rtl:
		gtk.Widget.set_default_direction(gtk.TextDirection.RTL)
	d = StarCalendarRegisterDialog()
	d.present()
	gtk.main()
	core.stopRunningThreads()
	gtk.main_quit()
