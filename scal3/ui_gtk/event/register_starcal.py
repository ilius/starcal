#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

import time
import sys
import requests

sys.path.append("/starcal")  # REMOVE FIXME

from scal3 import core
from scal3 import locale_man
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import (
	dialog_add_button,
)
from scal3.ui_gtk.mywidgets.dialog import MyDialog
from scal3.ui_gtk.mywidgets.buttonbox import MyHButtonBox


class StarCalendarRegisterDialog(gtk.Window, MyDialog):
	def __init__(self, **kwargs):
		gtk.Window.__init__(self, **kwargs)
		###
		self.set_title(_("Register at StarCalendar.net"))
		self.resize(600, 300)
		self.connect("delete-event", self.onDeleteEvent)
		self.set_transient_for(None)
		self.set_type_hint(gdk.WindowTypeHint.NORMAL)
		self.vbox = gtk.VBox()
		self.add(self.vbox)
		###
		self.buttonBox = MyHButtonBox()
		self.okButton = self.buttonBox.add_ok(self.okClicked)
		self.cancelButton = self.buttonBox.add_cancel(self.cancelClicked)
		self.vbox.pack_end(self.buttonBox, 0, 0, 0)
		###
		sgroupLabel = gtk.SizeGroup(gtk.SizeGroupMode.HORIZONTAL)
		###
		hbox = gtk.HBox(spacing=5)
		label = gtk.Label(_("Email"))
		label.set_alignment(0, 0.5)
		pack(hbox, label, 0, 0)
		sgroupLabel.add_widget(label)
		self.emailEntry = gtk.Entry()
		self.emailEntry.set_direction(gtk.TextDirection.LTR)
		pack(hbox, self.emailEntry, 1, 1, 10)
		pack(self.vbox, hbox, 0, 0, 10)
		###
		hbox = gtk.HBox(spacing=5)
		label = gtk.Label(_("Password"))
		label.set_alignment(0, 0.5)
		pack(hbox, label, 0, 0)
		sgroupLabel.add_widget(label)
		self.passwordEntry = gtk.Entry()
		self.passwordEntry.set_visibility(False)
		self.passwordEntry.set_direction(gtk.TextDirection.LTR)
		pack(hbox, self.passwordEntry, 1, 1, 10)
		pack(self.vbox, hbox, 0, 0, 10)
		###
		hbox = gtk.HBox(spacing=5)
		label = gtk.Label(_("Repeat Password"))
		label.set_alignment(0, 0.5)
		pack(hbox, label, 0, 0)
		sgroupLabel.add_widget(label)
		self.passwordEntry2 = gtk.Entry()
		self.passwordEntry2.set_visibility(False)
		self.passwordEntry2.set_direction(gtk.TextDirection.LTR)
		pack(hbox, self.passwordEntry2, 1, 1, 10)
		pack(self.vbox, hbox, 0, 0, 10)
		###
		hbox = gtk.HBox(spacing=5)
		label = gtk.Label(_("Name (Optional)"))
		label.set_alignment(0, 0.5)
		pack(hbox, label, 0, 0)
		sgroupLabel.add_widget(label)
		self.nameEntry = gtk.Entry()
		#self.nameEntry.set_direction(gtk.TextDirection.LTR)
		pack(hbox, self.nameEntry, 1, 1, 10)
		pack(self.vbox, hbox, 0, 0, 10)
		###
		hbox = gtk.HBox(spacing=5)
		label = gtk.Label()
		label.set_alignment(0, 0.5)
		# make text color red
		label.modify_fg(gtk.StateType.NORMAL, gdk.Color(65535, 0, 0))
		pack(hbox, label, 0, 0)
		pack(self.vbox, hbox, 0, 0, 10)
		self.errorLabel = label
		###
		self.emailEntry.connect("changed", self.updateOkSensitive)
		self.passwordEntry.connect("changed", self.updateOkSensitive)
		self.passwordEntry2.connect("changed", self.updateOkSensitive)
		self.updateOkSensitive()
		###
		self.vbox.show_all()
		###

	def canSubmit(self):
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

	def updateOkSensitive(self, *args):
		ok = self.canSubmit()
		self.okButton.set_sensitive(ok)
		if ok:
			self.errorLabel.set_text("")

	def doRegister(self):
		"""
		return None if successful, or error string if failed
		"""
		email = self.emailEntry.get_text()
		password = self.passwordEntry.get_text()
		fullName = self.nameEntry.get_text()

		accountCls = ui.eventAccounts.loadClass("starcal")

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
		except:
			error = "non-json data: %s" % res.text
		else:
			error = data.get("error", "")
			token = data.get("token", "")

		if error:
			self.errorLabel.set_text(_(error))
			return error

		account = accountCls()
		account.setData({
			"title": "StarCalendar: " + email,
			"email": email,
			"password": password,
			"lastToken": token,
		})
		account.save()
		ui.eventAccounts.append(account)
		ui.eventAccounts.save()
		if ui.prefDialog:
			ui.prefDialog.refreshAccounts()  # messy, I know, FIXME
		###
		while gtk.events_pending():
			gtk.main_iteration_do(False)
		error = account.fetchGroups()
		if error:
			print(error)
			return # error? FIXME
		account.save()

	def okClicked(self, widget):
		error = self.waitingDo(self.doRegister)
		if not error:
			self.destroy()
		return True

	def cancelClicked(self, widget):
		self.destroy()
		return True

	def onDeleteEvent(self, obj, event):
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
