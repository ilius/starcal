#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scal3 import core
from scal3.locale_man import tr as _

from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import (
	IdComboBox,
	showError,
	labelImageButton,
)


class BaseWidgetClass(gtk.Box):
	def __init__(self, account):
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.account = account
		########
		self.sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		#####
		hbox = HBox()
		label = gtk.Label(label=_("Title"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.titleEntry = gtk.Entry()
		pack(hbox, self.titleEntry, 1, 1)
		pack(self, hbox)

	def updateWidget(self):
		self.titleEntry.set_text(self.account.title)

	def updateVars(self):
		self.account.title = self.titleEntry.get_text()


class AccountCombo(IdComboBox):
	def __init__(self):
		ls = gtk.ListStore(int, str)
		gtk.ComboBox.__init__(self)
		self.set_model(ls)
		###
		cell = gtk.CellRendererText()
		pack(self, cell, 1)
		self.add_attribute(cell, "text", 1)
		###
		ls.append([-1, _("None")])
		for account in ui.eventAccounts:
			if account.enable:
				ls.append([account.id, account.title])
		###
		gtk.ComboBox.set_active(self, 0)

	def get_active(self):
		active = IdComboBox.get_active(self)
		if active == -1:
			active = None
		return active

	def set_active(self, active):
		if active is None:
			active = -1
		IdComboBox.set_active(self, active)


class AccountGroupCombo(IdComboBox):
	def __init__(self):
		self.account = None
		###
		ls = gtk.ListStore(str, str)
		gtk.ComboBox.__init__(self)
		self.set_model(ls)
		###
		cell = gtk.CellRendererText()
		pack(self, cell, 1)
		self.add_attribute(cell, "text", 1)

	def setAccount(self, account):
		self.account = account
		self.updateList()

	def updateList(self):
		ls = self.get_model()
		ls.clear()
		if self.account:
			for groupData in self.account.remoteGroups:
				ls.append([
					str(groupData["id"]),
					groupData["title"],
				])


class AccountGroupBox(gtk.Box):
	def __init__(self, accountCombo=None):
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.combo = AccountGroupCombo()
		pack(self, self.combo)
		##
		button = labelImageButton(
			label=_("Fetch"),
			# TODO: imageName="fetch-account.svg",
		)
		button.connect("clicked", self.onFetchClick)
		pack(self, button)
		self.fetchButton = button
		##
		label = gtk.Label()
		label.set_xalign(0.1)
		pack(self, label, 1, 1)
		self.msgLabel = label
		###
		if accountCombo:
			accountCombo.connect("changed", self.accountComboChanged)

	def accountComboChanged(self, combo):
		aid = combo.get_active()
		if aid:
			account = ui.eventAccounts[aid]
			self.combo.setAccount(account)

	def onFetchClick(self, obj=None):
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
			showError(msg, transient_for=ui.eventManDialog)
			return
		else:
			self.msgLabel.set_label("")
			account.save()
		self.combo.updateList()
