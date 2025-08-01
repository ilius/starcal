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

from scal3 import logger

log = logger.get()

from scal3.event_lib import ev
from scal3.locale_man import tr as _
from scal3.ui_gtk import gdk, gtk, pack
from scal3.ui_gtk.stack import StackPage
from scal3.ui_gtk.toolbox import ToolBoxItem, VerticalStaticToolBox
from scal3.ui_gtk.utils import confirm, showError

__all__ = ["PreferencesAccounts"]


class PreferencesAccounts:
	def __init__(self, window: gtk.Window, spacing: int) -> None:
		self.win = window
		vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=int(spacing / 2))
		vbox.set_border_width(int(spacing / 2))
		page = StackPage()
		self.page = page
		page.pageWidget = vbox
		page.pageName = "accounts"
		page.pageTitle = _("Accounts")
		page.pageLabel = _("Accounts")
		page.pageIcon = "applications-development-web.png"
		# -----
		treev = gtk.TreeView()
		treev.set_headers_clickable(True)
		treeModel = gtk.ListStore(int, bool, str)  # id (hidden), enable, title
		treev.set_model(treeModel)
		treev.enable_model_drag_source(
			gdk.ModifierType.BUTTON1_MASK,
			[
				gtk.TargetEntry.new("row", gtk.TargetFlags.SAME_WIDGET, 0),
			],
			gdk.DragAction.MOVE,
		)
		treev.enable_model_drag_dest(
			[
				gtk.TargetEntry.new("row", gtk.TargetFlags.SAME_WIDGET, 0),
			],
			gdk.DragAction.MOVE,
		)
		treev.connect("row-activated", self.accountsTreevRActivate)
		treev.connect("button-press-event", self.accountsTreevButtonPress)
		# ---
		swin = gtk.ScrolledWindow()
		swin.add(treev)
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		cell: gtk.CellRenderer
		# ------
		cell = gtk.CellRendererToggle()
		# cell.set_property("activatable", True)
		cell.connect("toggled", self.accountsTreeviewCellToggled)
		col = gtk.TreeViewColumn(title=_("Enable"), cell_renderer=cell)
		col.add_attribute(cell, "active", 1)
		# cell.set_active(False)
		col.set_resizable(True)
		col.set_property("expand", False)
		treev.append_column(col)
		# ------
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("Title"), cell_renderer=cell, text=2)
		col.set_property("expand", True)
		treev.append_column(col)
		# ------
		self.accountsTreeview = treev
		self.accountsTreeModel = treeModel
		# -----------------------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		vboxPlug = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		pack(vboxPlug, swin, 1, 1)
		pack(hbox, vboxPlug, 1, 1)
		# -----
		toolbar = VerticalStaticToolBox(self)
		# -----
		toolbar.extend(
			[
				ToolBoxItem(
					name="register",
					imageName="starcal.svg",
					onClick=self.onAccountsRegisterClick,
					desc=_("Register at StarCalendar.net"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="add",
					imageName="list-add.svg",
					onClick=self.onAccountsAddClick,
					desc=_("Add"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="edit",
					imageName="document-edit.svg",
					onClick=self.onAccountsEditClick,
					desc=_("Edit"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="delete",
					imageName="edit-delete.svg",
					onClick=self.onAccountsDeleteClick,
					desc=_("Delete", ctx="button"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="moveUp",
					imageName="go-up.svg",
					onClick=self.onAccountsUpClick,
					desc=_("Move up"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="moveDown",
					imageName="go-down.svg",
					onClick=self.onAccountsDownClick,
					desc=_("Move down"),
					continuousClick=False,
				),
			],
		)
		# -----------
		pack(hbox, toolbar.w)
		pack(vbox, hbox, 1, 1)

	def refreshAccounts(self) -> None:
		self.accountsTreeModel.clear()
		for account in ev.accounts:
			self.accountsTreeModel.append(
				[
					account.id,
					account.enable,
					account.title,
				],
			)

	def editAccount(self, index: int) -> None:
		from scal3.ui_gtk.event.account_op import AccountEditorDialog

		accountId = self.accountsTreeModel[index][0]
		account = ev.accounts[accountId]
		if not account.loaded:
			showError(
				_("Account must be enabled before editing"), transient_for=self.win
			)
			return
		accountNew = AccountEditorDialog(account, transient_for=self.win).run2()
		if accountNew is None:
			return
		accountNew.save()
		ev.accounts.save()
		self.accountsTreeModel[index][2] = accountNew.title

	def onAccountsEditClick(self, _w: gtk.Widget) -> None:
		cur = self.accountsTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		self.editAccount(index)

	def onAccountsRegisterClick(self, _w: gtk.Widget) -> None:
		from scal3.ui_gtk.event.register_starcal import StarCalendarRegisterDialog

		win = StarCalendarRegisterDialog(transient_for=self.win)
		win.run()  # type: ignore[no-untyped-call]

	def onAccountsAddClick(self, _w: gtk.Widget) -> None:
		from scal3.ui_gtk.event.account_op import AccountEditorDialog

		account = AccountEditorDialog(transient_for=self.win).run2()
		if account is None:
			return
		account.save()
		ev.accounts.append(account)
		ev.accounts.save()
		self.accountsTreeModel.append(
			[
				account.id,
				account.enable,
				account.title,
			],
		)
		# ---
		while gtk.events_pending():
			gtk.main_iteration_do(False)
		try:
			account.fetchGroups()
		except Exception as e:
			log.error(f"error in fetchGroups: {e}")
			return
		account.save()

	def onAccountsDeleteClick(self, _w: gtk.Widget) -> None:
		cur = self.accountsTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		accountId = self.accountsTreeModel[index][0]
		account = ev.accounts[accountId]
		if not confirm(
			_('Do you want to delete account "{accountTitle}"').format(
				accountTitle=account.title,
			),
			transient_for=self.win,
		):
			return
		ev.accounts.delete(account)
		ev.accounts.save()
		del self.accountsTreeModel[index]

	def accountSetCursor(self, index: int) -> None:
		self.accountsTreeview.set_cursor(gtk.TreePath.new_from_indices([index]))

	def onAccountsUpClick(self, _w: gtk.Widget) -> None:
		cur = self.accountsTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		t = self.accountsTreeModel
		if index <= 0 or index >= len(t):
			gdk.beep()
			return
		ev.accounts.moveUp(index)
		ev.accounts.save()
		t.swap(
			t.get_iter(str(index - 1)),
			t.get_iter(str(index)),
		)
		self.accountSetCursor(index - 1)

	def onAccountsDownClick(self, _w: gtk.Widget) -> None:
		cur = self.accountsTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		t = self.accountsTreeModel
		if index < 0 or index >= len(t) - 1:
			gdk.beep()
			return
		ev.accounts.moveDown(index)
		ev.accounts.save()
		t.swap(t.get_iter(str(index)), t.get_iter(str(index + 1)))
		self.accountSetCursor(index + 1)

	def accountsTreevRActivate(
		self,
		_treev: gtk.TreeView,
		path: gtk.TreePath,
		_col: gtk.TreeViewColumn,
	) -> None:
		index = path.get_indices()[0]
		self.editAccount(index)

	@staticmethod
	def accountsTreevButtonPress(_widget: gtk.Widget, gevent: gdk.EventButton) -> bool:
		b = gevent.button
		if b == 3:  # noqa: SIM103
			# FIXME
			# cur = self.accountsTreeview.get_cursor()[0]
			# if cur:
			# 	index = cur[0]
			# 	accountId = self.accountsTreeModel[index][0]
			# 	account = ev.accounts[accountId]
			# 	menu = Menu()
			# 	#
			# 	menu.show_all()
			# 	menu.popup(None, None, None, None, 3, gevent.time)
			return True
		return False

	def accountsTreeviewCellToggled(
		self,
		cell: gtk.CellRendererToggle,
		path: gtk.TreePath,
	) -> None:
		index = path.get_indices()[0]
		active = not cell.get_active()
		# ---
		accountId = self.accountsTreeModel[index][0]
		account = ev.accounts[accountId]
		# not account.loaded -> it's a dummy account
		if active and not account.loaded:
			account = ev.accounts.replaceDummyObj(account)
			if account is None:
				return
		account.enable = active
		account.save()
		# ---
		self.accountsTreeModel[index][1] = active
