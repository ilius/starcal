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

from typing import TYPE_CHECKING

from scal3.event_lib import ev
from scal3.locale_man import tr as _
from scal3.ui_gtk import Menu, MenuItem, gdk, gtk, pack
from scal3.ui_gtk.event.manager.conf import eventManShowDescription
from scal3.ui_gtk.event.manager.toolbar import EventManagerToolbar
from scal3.ui_gtk.event.manager.tree import EventManagerTree
from scal3.ui_gtk.mywidgets.resize_button import ResizeButton
from scal3.ui_gtk.starcal_funcs import eventSearchShow
from scal3.ui_gtk.utils import (
	dialog_add_button,
	labelImageButton,
)

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.ui_gtk.event.manager.dialog import EventManagerDialog

__all__ = ["EventManagerUi"]

type W = gtk.Widget


def onMenuBarSearchClick(_menuItem: gtk.MenuItem) -> None:
	eventSearchShow()


class EventManagerUi:
	"""Builds the Event Manager dialog widgets."""

	def __init__(self, dialog: EventManagerDialog) -> None:
		self.dialog = dialog
		self.build()

	def build(self) -> None:
		self._buildDialog()
		self._buildMenubar()
		self._buildMultiSelectBar()
		self._buildTreeview()
		self._buildStatusbar()
		self.dialog.dialog.vbox.show_all()
		self.dialog.multiSelectHBox.hide()

	def _buildDialog(self) -> None:
		dialog = self.dialog
		win = dialog.dialog
		win.set_title(_("Event Manager"))
		win.resize(800, 600)
		win.connect("delete-event", dialog.onDeleteEvent)
		win.set_transient_for(None)
		win.set_type_hint(gdk.WindowTypeHint.NORMAL)
		# --
		dialog_add_button(
			win,
			res=gtk.ResponseType.OK,
			imageName="dialog-ok.svg",
			label=_("_Apply", ctx="window action"),
		)
		# self.connect("response", lambda w, e: self.hide())
		win.connect("response", dialog.onResponse)
		win.connect("show", dialog.onShow)

	def _buildMenubar(self) -> None:
		dialog = self.dialog
		menubar = dialog.menubar = gtk.MenuBar()
		# ----
		fileItem = dialog.fileItem = MenuItem(_("_File"))
		fileMenu = Menu()
		fileItem.set_submenu(fileMenu)
		menubar.append(fileItem)
		# --
		addGroupItem = MenuItem(_("Add New Group"))
		addGroupItem.set_sensitive(not ev.allReadOnly)
		addGroupItem.connect("activate", dialog.ops.addGroupBeforeSelection)
		# FIXME: or before selected group?
		fileMenu.append(addGroupItem)
		# --
		# FIXME right place?
		searchItem = MenuItem(_("_Search Events"))
		searchItem.connect("activate", onMenuBarSearchClick)
		fileMenu.append(searchItem)
		# --
		exportItem = MenuItem(_("_Export", ctx="menu"))
		exportItem.connect("activate", dialog.onMenuBarExportClick)
		fileMenu.append(exportItem)
		# --
		importItem = MenuItem(_("_Import", ctx="menu"))
		importItem.set_sensitive(not ev.allReadOnly)
		importItem.connect("activate", dialog.onMenuBarImportClick)
		fileMenu.append(importItem)
		# --
		orphanItem = MenuItem(_("Check for Orphan Events"))
		orphanItem.set_sensitive(not ev.allReadOnly)
		orphanItem.connect("activate", dialog.onMenuBarOrphanClick)
		fileMenu.append(orphanItem)
		# ----
		editItem = dialog.editItem = MenuItem(_("_Edit"))
		if ev.allReadOnly:
			editItem.set_sensitive(False)
		else:
			editMenu = Menu()
			editItem.set_submenu(editMenu)
			menubar.append(editItem)
			# --
			editEditItem = MenuItem(_("Edit"))
			editEditItem.connect("activate", dialog.onMenuBarEditClick)
			editMenu.append(editEditItem)
			editMenu.connect("show", dialog.mbarEditMenuPopup)
			dialog.mbarEditItem = editEditItem
			# --
			editMenu.append(gtk.SeparatorMenuItem())
			# --
			cutItem = MenuItem(_("Cu_t"))
			cutItem.connect("activate", dialog.onMenuBarCutClick)
			editMenu.append(cutItem)
			dialog.mbarCutItem = cutItem
			# --
			copyItem = MenuItem(_("_Copy"))
			copyItem.connect("activate", dialog.onMenuBarCopyClick)
			editMenu.append(copyItem)
			dialog.mbarCopyItem = copyItem
			# --
			pasteItem = MenuItem(_("_Paste"))
			pasteItem.connect("activate", dialog.onMenuBarPasteClick)
			editMenu.append(pasteItem)
			dialog.mbarPasteItem = pasteItem
			# --
			editMenu.append(gtk.SeparatorMenuItem())
			# --
			dupItem = MenuItem(_("_Duplicate"))
			dupItem.connect("activate", dialog.ops.duplicateSelectedObj)
			editMenu.append(dupItem)
			dialog.mbarDupItem = dupItem
			# --
			editMenu.append(gtk.SeparatorMenuItem())
			# --
			enableAllItem = MenuItem(_("Enable All Groups"))
			enableAllItem.connect("activate", dialog.ops.onEnableAllClick)
			editMenu.append(enableAllItem)
			# --
			disableAllItem = MenuItem(_("Disable All Groups"))
			disableAllItem.connect("activate", dialog.ops.onDisableAllClick)
			editMenu.append(disableAllItem)
		# ----
		viewItem = MenuItem(_("_View"))
		viewMenu = Menu()
		viewItem.set_submenu(viewMenu)
		menubar.append(viewItem)
		# --
		collapseItem = MenuItem(_("Collapse All"))
		collapseItem.connect("activate", dialog.onCollapseAllClick)
		viewMenu.append(collapseItem)
		# --
		expandItem = MenuItem(_("Expand All"))
		expandItem.connect("activate", dialog.onExpandAllAllClick)
		viewMenu.append(expandItem)
		# --
		viewMenu.append(gtk.SeparatorMenuItem())
		# --
		dialog.showDescItem = gtk.CheckMenuItem(label=_("Show _Description"))
		dialog.showDescItem.set_use_underline(True)
		dialog.showDescItem.set_active(eventManShowDescription.v)
		dialog.showDescItem.connect("toggled", dialog.showDescItemToggled)
		viewMenu.append(dialog.showDescItem)
		# ----
		# testItem = MenuItem(_("Test"))
		# testMenu = Menu()
		# testItem.set_submenu(testMenu)
		# menubar.append(testItem)
		# ---
		# item = MenuItem("")
		# item.connect("activate", )
		# testMenu.append(item)
		# ----
		multiSelectMenu = Menu()
		multiSelectItemMain = MenuItem(label=_("Multi-select"))
		dialog.multiSelectItemMain = multiSelectItemMain
		multiSelectItemMain.set_submenu(multiSelectMenu)
		menubar.append(multiSelectItemMain)
		# --
		multiSelectItem = gtk.CheckMenuItem(label=_("Multi-select"))
		multiSelectItem.connect("activate", dialog.multiSel.toggle)
		multiSelectMenu.append(multiSelectItem)
		dialog.multiSelectItem = multiSelectItem
		dialog.multiSelectItemsOther = []
		# ----
		multiSelectMenu.append(gtk.SeparatorMenuItem())
		# ----
		cutItem = MenuItem(_("Cu_t"))
		cutItem.connect("activate", dialog.multiSel.cut)
		dialog.multiSelectItemsOther.append(cutItem)
		# --
		copyItem = MenuItem(_("_Copy"))
		copyItem.connect("activate", dialog.multiSel.copy)
		dialog.multiSelectItemsOther.append(copyItem)
		# --
		pasteItem = MenuItem(_("_Paste"))
		pasteItem.connect("activate", dialog.multiSel.paste)
		dialog.multiSelectItemsOther.append(pasteItem)
		# --
		dialog.multiSelectItemsOther.append(gtk.SeparatorMenuItem())
		# --
		deleteItem = MenuItem(_("Delete", ctx="event manager"))
		deleteItem.connect("activate", dialog.multiSel.delete)
		dialog.multiSelectItemsOther.append(deleteItem)
		# --
		dialog.multiSelectItemsOther.append(gtk.SeparatorMenuItem())
		# --
		bulkEditItem = MenuItem(_("Bulk Edit Events"))
		# imageName="document-edit.svg",
		# native CheckMenuItem and ImageMenuItem are not aligned
		bulkEditItem.connect("activate", dialog.multiSel.bulkEdit)
		dialog.multiSelectItemsOther.append(bulkEditItem)
		# --
		exportItem = MenuItem(_("_Export", ctx="menu"))
		exportItem.connect("activate", dialog.multiSel.export)
		dialog.multiSelectItemsOther.append(exportItem)
		# ---
		for item in dialog.multiSelectItemsOther:
			item.set_sensitive(False)
			multiSelectMenu.append(item)
		# ----
		menubar.show_all()
		pack(dialog.dialog.vbox, menubar)

	def _buildMultiSelectBar(self) -> None:
		dialog = self.dialog
		dialog.multiSelectHBox = hbox = gtk.Box(
			orientation=gtk.Orientation.HORIZONTAL, spacing=3
		)
		dialog.multiSelectLabel = gtk.Label(label=_("No event selected"))
		dialog.multiSelectLabel.set_xalign(0)
		dialog.multiSelectLabel.get_style_context().add_class("smaller")
		pack(hbox, dialog.multiSelectLabel, 1, 1)

		pack(
			hbox,
			self.smallerButton(
				label=_("Copy"),
				# imageName="edit-copy.svg",
				func=dialog.multiSel.copy,
				tooltip=_("Copy"),
			),
		)
		pack(
			hbox,
			self.smallerButton(
				label=_("Cut"),
				# imageName="edit-cut.svg",
				func=dialog.multiSel.cut,
				tooltip=_("Cut"),
			),
		)
		dialog.multiSelectPasteButton = self.smallerButton(
			label=_("Paste"),
			# imageName="edit-paste.svg",
			func=dialog.multiSel.paste,
			tooltip=_("Paste"),
		)
		pack(hbox, dialog.multiSelectPasteButton)
		dialog.multiSelectPasteButton.set_sensitive(False)
		pack(hbox, gtk.Label(), 1, 1)
		pack(
			hbox,
			self.smallerButton(
				label=_("Delete", ctx="event manager"),
				imageName="edit-delete.svg",
				func=dialog.multiSel.delete,
				tooltip=_("Move to {title}").format(title=ev.trash.title),
			),
		)
		pack(hbox, gtk.Label(), 1, 1)
		pack(
			hbox,
			self.smallerButton(
				label=_("Cancel"),
				imageName="dialog-cancel.svg",
				func=dialog.multiSel.cancel,
				tooltip=_("Cancel"),
			),
		)
		# ---
		pack(dialog.dialog.vbox, hbox)

	@staticmethod
	def smallerButton(
		label: str = "",
		imageName: str = "",
		func: Callable[[gtk.Button], None] | None = None,
		tooltip: str = "",
	) -> gtk.Button:
		button = labelImageButton(
			label=label,
			imageName=imageName,
			func=func,
			tooltip=tooltip,
			spacing=4,
		)
		button.get_style_context().add_class("smaller")
		return button

	def _buildTreeview(self) -> None:
		dialog = self.dialog
		treeBox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		# -----
		dialog.tree = EventManagerTree(dialog)
		dialog.tree.connectSignals(
			dialog.statusbar.cursorChanged,
			dialog.onTreeviewButtonPress,
			dialog.rowActivated,
			dialog.onTreeviewKeyPress,
		)
		dialog.w.connect("key-press-event", dialog.onKeyPress)
		# -----
		swin = gtk.ScrolledWindow()
		swin.add(dialog.tree.getWidget())
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		pack(treeBox, swin, 1, 1)
		# ---
		dialog.toolbar = EventManagerToolbar(dialog)
		# ---
		pack(treeBox, dialog.toolbar.w)
		# -----
		pack(dialog.dialog.vbox, treeBox, 1, 1)

	def _buildStatusbar(self) -> None:
		dialog = self.dialog
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		hbox.set_direction(gtk.TextDirection.LTR)
		dialog.sbar = gtk.Statusbar()
		dialog.sbar.set_direction(gtk.TextDirection.LTR)
		pack(hbox, dialog.sbar, 1, 1)
		pack(hbox, ResizeButton(dialog.dialog))
		pack(dialog.dialog.vbox, hbox)
