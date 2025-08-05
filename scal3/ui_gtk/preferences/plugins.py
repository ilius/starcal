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

from typing import Protocol

from scal3 import logger

log = logger.get()

import typing

from scal3 import core, plugin_man, ui
from scal3.locale_man import tr as _
from scal3.ui_gtk import Dialog, Menu, gdk, gtk, pack
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.stack import StackPage
from scal3.ui_gtk.toolbox import ToolBoxItem, VerticalStaticToolBox
from scal3.ui_gtk.utils import (
	dialog_add_button,
	labelImageButton,
	openWindow,
)

if typing.TYPE_CHECKING:
	from scal3.pytypes import PluginType

__all__ = ["PreferencesPlugins"]


class PreferencesWindowType(Protocol):
	def plugTreeviewTop(self, _w: gtk.Widget) -> None: ...
	def plugTreeviewUp(self, _w: gtk.Widget) -> None: ...
	def plugTreeviewDown(self, _w: gtk.Widget) -> None: ...
	def plugTreeviewBottom(self, _w: gtk.Widget) -> None: ...
	def onPlugAddClick(self, _w: gtk.Widget) -> None: ...
	def onPlugDeleteClick(self, _w: gtk.Widget) -> None: ...


class PreferencesPluginsToolbar(VerticalStaticToolBox):
	def __init__(self, parent: PreferencesWindowType) -> None:
		VerticalStaticToolBox.__init__(
			self,
			parent,
			# buttonBorder=0,
			# buttonPadding=0,
		)
		# with iconSize < 20, the button would not become smaller
		# so 20 is the best size
		self.extend(
			[
				ToolBoxItem(
					name="goto-top",
					imageName="go-top.svg",
					onClick=parent.plugTreeviewTop,
					desc=_("Move to top"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="go-up",
					imageName="go-up.svg",
					onClick=parent.plugTreeviewUp,
					desc=_("Move up"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="go-down",
					imageName="go-down.svg",
					onClick=parent.plugTreeviewDown,
					desc=_("Move down"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="goto-bottom",
					imageName="go-bottom.svg",
					onClick=parent.plugTreeviewBottom,
					desc=_("Move to bottom"),
					continuousClick=False,
				),
			],
		)
		self.buttonAdd = self.append(
			ToolBoxItem(
				name="add",
				imageName="list-add.svg",
				onClick=parent.onPlugAddClick,
				desc=_("Add"),
				continuousClick=False,
			),
		)
		self.buttonAdd.w.set_sensitive(False)
		self.append(
			ToolBoxItem(
				name="delete",
				imageName="edit-delete.svg",
				onClick=parent.onPlugDeleteClick,
				desc=_("Delete"),
				continuousClick=False,
			),
		)

	def setCanAdd(self, canAdd: bool) -> None:
		self.buttonAdd.w.set_sensitive(canAdd)


class PreferencesPlugins:
	def __init__(self, window: gtk.Window, spacing: int) -> None:
		self.window = window
		vbox = gtk.Box(
			orientation=gtk.Orientation.VERTICAL,
			spacing=int(spacing / 2),
		)
		page = StackPage()
		self.page = page
		vbox.set_border_width(int(spacing / 2))
		page.pageWidget = vbox
		page.pageName = "plugins"
		page.pageTitle = _("Plugins")
		page.pageLabel = _("_Plugins")
		page.pageIcon = "preferences-plugin.svg"
		# -----
		treev = gtk.TreeView()
		treev.set_headers_clickable(True)
		listStore = self.plugListStore = gtk.ListStore(
			int,  # index
			bool,  # enable
			bool,  # show_date
			str,  # title
		)
		treev.set_model(listStore)
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
		treev.connect("drag_data_received", self.plugTreevDragReceived)
		treev.get_selection().connect("changed", self.plugTreevCursorChanged)
		treev.connect("row-activated", self.plugTreevRActivate)
		treev.connect("button-press-event", self.plugTreevButtonPress)
		# ---
		# treev.drag_source_add_text_targets()
		# treev.drag_source_add_uri_targets()
		# treev.drag_source_unset()
		# ---
		swin = gtk.ScrolledWindow()
		swin.add(treev)
		swin.set_policy(
			gtk.PolicyType.AUTOMATIC,
			gtk.PolicyType.AUTOMATIC,
		)
		# ------
		# each named font size if 1.2 times larger than last
		# size='medium' is the same as not having this tag (equal to widget's font)
		# so size='large' is 1.2 times larger and size='small' is 1.2 times
		# smaller than default
		# font='12.5' is equal to size='12800' because 12.5*1024 = 12800
		# named sizes:
		#   xx-small	= default * 0.5787
		#   x-small		= default * 0.6944
		#   small		= default * 0.8333
		#   medium		= default * 1.0
		#   large		= default * 1.2
		#   x-large		= default * 1.44
		#   xx-large	= default * 1.7279
		# ------
		size = ui.getFont().size
		cell: gtk.CellRenderer
		# ------
		cell = gtk.CellRendererToggle()
		# cell.set_property("activatable", True)
		cell.connect("toggled", self.plugTreeviewCellToggled)
		titleLabel = gtk.Label(
			label=f"<span font='{size * 0.7}'>" + _("Enable") + "</span>",
			use_markup=True,
		)
		titleLabel.show()
		col = gtk.TreeViewColumn(cell_renderer=cell)
		col.set_widget(titleLabel)
		col.add_attribute(cell, "active", 1)
		# cell.set_active(False)
		col.set_resizable(True)
		col.set_property("expand", False)
		treev.append_column(col)
		# ------
		cell = gtk.CellRendererToggle()
		# cell.set_property("activatable", True)
		cell.connect("toggled", self.plugTreeviewCellToggled2)
		titleLabel = gtk.Label(
			label=f"<span font='{size * 0.5}'>" + _("Show\nDate") + "</span>",
			use_markup=True,
		)
		titleLabel.show()
		col = gtk.TreeViewColumn(cell_renderer=cell)
		col.set_widget(titleLabel)
		col.add_attribute(cell, "active", 2)
		# cell.set_active(False)
		col.set_resizable(True)
		col.set_property("expand", False)
		treev.append_column(col)
		# ------
		# cell = gtk.CellRendererText()
		# col = gtk.TreeViewColumn(title=_("File Name"), cell_renderer=cell, text=2)
		# col.set_resizable(True)
		# treev.append_column(col)
		# treev.set_search_column(1)
		# ------
		cell = gtk.CellRendererText()
		# cell.set_property("wrap-mode", gtk.WrapMode.WORD)
		# cell.set_property("editable", True)
		# cell.set_property("wrap-width", 200)
		col = gtk.TreeViewColumn(title=_("Title"), cell_renderer=cell, text=3)
		# treev.connect("draw", self.plugTreevExpose)
		# self.plugTitleCell = cell
		# self.plugTitleCol = col
		# col.set_resizable(True)-- No need!
		col.set_property("expand", True)
		treev.append_column(col)
		# ------
		# for i in xrange(len(core.plugIndex.v)):
		# 	x = core.plugIndex.v[i]
		# 	treeModel.append([x[0], x[1], x[2], .v[x[0]].title])
		# ------
		self.plugTreeview = treev
		# -----------------------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		vboxPlug = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		pack(vboxPlug, swin, 1, 1)
		pack(hbox, vboxPlug, 1, 1)
		# ---
		aboutHbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		# ---
		button = labelImageButton(
			label=_("_About Plugin"),
			imageName="dialog-information.svg",
		)
		button.set_sensitive(False)
		button.connect("clicked", self.onPlugAboutClick)
		self.plugButtonAbout = button
		pack(aboutHbox, button)
		pack(aboutHbox, gtk.Label(), 1, 1)
		# ---
		button = labelImageButton(
			label=_("C_onfigure Plugin"),
			imageName="preferences-system.svg",
		)
		button.set_sensitive(False)
		button.connect("clicked", self.onPlugConfClick)
		self.plugButtonConf = button
		pack(aboutHbox, button)
		pack(aboutHbox, gtk.Label(), 1, 1)
		# ---
		pack(vboxPlug, aboutHbox)
		# ---
		toolbar = PreferencesPluginsToolbar(self)
		pack(hbox, toolbar.w)
		self.pluginsToolbar = toolbar
		# -----
		"""
		vpan = gtk.VPaned()
		vpan.add1(hbox)
		vbox2 gtk.Box(orientation=gtk.Orientation.VERTICAL)
		pack(vbox2, gtk.Label(label="Test Label"))
		vpan.add2(vbox2)
		vpan.set_position(100)
		pack(vbox, vpan)
		"""
		pack(vbox, hbox, 1, 1)
		# --------------------------
		d = Dialog(transient_for=window)
		d.set_transient_for(window)
		# dialog.set_transient_for(parent) makes the window on top of parent
		# and at the center point of parent
		# but if you call dialog.show() or dialog.present(), the parent is
		# still active(clickabel widgets) before closing child "dialog"
		# you may call dialog.run() to realy make it transient for parent
		# d.set_has_separator(False)
		d.connect("delete-event", self.plugAddDialogDeleteEvent)
		d.set_title(_("Add Plugin"))
		# ---
		dialog_add_button(
			d,
			res=gtk.ResponseType.CANCEL,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
			onClick=self.plugAddDialogClose,
		)
		dialog_add_button(
			d,
			res=gtk.ResponseType.OK,
			imageName="dialog-ok.svg",
			label=_("_Choose"),
			onClick=self.plugAddDialogOK,
		)
		# ---
		treev = gtk.TreeView()
		listStore = gtk.ListStore(str)
		treev.set_model(listStore)
		# treev.enable_model_drag_source(
		# 	gdk.ModifierType.BUTTON1_MASK,
		# 	[("", 0, 0, 0)],
		# 	gdk.DragAction.MOVE,
		# )  # FIXME
		# treev.enable_model_drag_dest(
		# 	[("", 0, 0, 0)],
		# 	gdk.DragAction.MOVE,
		# )  # FIXME
		treev.connect("drag_data_received", self.plugTreevDragReceived)
		treev.connect("row-activated", self.plugAddTreevRActivate)
		# ----
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("Title"), cell_renderer=cell, text=0)
		# col.set_resizable(True)# no need when have only one column!
		treev.append_column(col)
		# ----
		swin = gtk.ScrolledWindow()
		swin.add(treev)
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		pack(d.vbox, swin, 1, 1)
		d.vbox.show_all()
		self.plugAddDialog = d
		self.plugAddTreeview = treev
		self.plugAddTreeModel = listStore
		# -------------
		# treev.set_resize_mode(gtk.RESIZE_IMMEDIATE)
		# self.plugAddItems = []

	@staticmethod
	def loadPlugin(plug: PluginType, plugI: int) -> PluginType:
		plug2 = plugin_man.loadPlugin(plug.file, enable=True)
		if plug2:
			assert plug2.loaded
		core.allPlugList.v[plugI] = plug2
		return plug

	def updatePrefGui(self) -> None:
		model = self.plugListStore
		model.clear()
		for p in core.getPluginsTable():
			model.append(
				[
					p.idx,
					p.enable,
					p.show_date,
					p.title,
				],
			)
		self.plugAddItems = []
		self.plugAddTreeModel.clear()
		for i, title in core.getDeletedPluginsTable():
			self.plugAddItems.append(i)
			self.plugAddTreeModel.append([title])
			self.pluginsToolbar.setCanAdd(True)

	def apply(self) -> None:
		index = []
		for row in self.plugListStore:
			plugI = row[0]
			enable = row[1]
			show_date = row[2]
			index.append(plugI)
			plug = core.allPlugList.v[plugI]
			if plug.loaded:
				try:
					plug.enable = enable
					plug.show_date = show_date
				except NameError:
					core.log.exception("")
					log.info(f"plugIndex = {core.plugIndex.v}")
			elif enable:
				plug = self.loadPlugin(plug, plugI)
		core.plugIndex.v = index
		core.updatePlugins()

	# def plugTreevExpose(self, widget: gtk.Widget, gevent: gdk.Event):
	# 	self.plugTitleCell.set_property(
	# 		"wrap-width",
	# 		self.plugTitleCol.get_width() + 2
	# 	)

	def plugTreevCursorChanged(
		self,
		_selection: gtk.SelectionData | None = None,
	) -> None:
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		model = self.plugListStore
		j = model[index][0]
		plug = core.allPlugList.v[j]
		self.plugButtonAbout.set_sensitive(bool(plug.about))
		self.plugButtonConf.set_sensitive(plug.hasConfig)

	def onPlugAboutClick(self, _w: gtk.Widget | None = None) -> None:
		from scal3.ui_gtk.about import AboutDialog

		cur: gtk.TreePath = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		model = self.plugListStore
		pIndex = model[index][0]
		plug = core.allPlugList.v[pIndex]
		# open_about returns True only if overriden by external plugin
		if plug.open_about():
			return
		if plug.about is None:
			return
		about = AboutDialog(
			# name="",  # FIXME
			title=_("About Plugin"),  # _("About ") + plug.title
			authors=plug.authors,
			comments=plug.about,
		)
		about.set_transient_for(self.window)
		about.connect("delete-event", lambda w, _e: w.destroy())
		about.connect("response", lambda w, _e: w.destroy())
		# about.set_resizable(True)
		# about.vbox.show_all()  # OR about.vbox.show_all() ; about.run()
		openWindow(about)  # FIXME

	def onPlugConfClick(self, _w: gtk.Widget | None = None) -> None:
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		model = self.plugListStore
		pIndex = model[index][0]
		plug = core.allPlugList.v[pIndex]
		if not plug.hasConfig:
			return
		plug.open_configure()

	@staticmethod
	def onPlugExportToIcsClick(_w: gtk.Widget, plug: PluginType) -> None:
		from scal3.ui_gtk.export import ExportToIcsDialog

		ExportToIcsDialog(plug.exportToIcs, plug.title).run()  # type: ignore[no-untyped-call]

	def plugTreevRActivate(
		self,
		_treev: gtk.TreeView,
		_path: gtk.TreePath,
		col: gtk.TreeViewColumn,
	) -> None:
		if col.get_title() == _("Title"):  # FIXME
			self.onPlugAboutClick()

	def plugTreevButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		b = gevent.button
		if b != 3:
			return False
		cur = self.plugTreeview.get_cursor()[0]
		if not cur:
			return True
		index = cur.get_indices()[0]
		pIndex = self.plugListStore[index][0]
		plug = core.allPlugList.v[pIndex]
		menu = Menu()
		# --
		item = ImageMenuItem(
			_("_About"),
			imageName="dialog-information.svg",
			onActivate=self.onPlugAboutClick,
		)
		item.set_sensitive(bool(plug.about))
		menu.add(item)
		# --
		item = ImageMenuItem(
			_("_Configure"),
			imageName="preferences-system.svg",
			onActivate=self.onPlugConfClick,
		)
		item.set_sensitive(plug.hasConfig)
		menu.add(item)

		# --
		def onPlugExportToIcsClick(w: gtk.Widget) -> None:
			self.onPlugExportToIcsClick(w, plug)

		menu.add(
			ImageMenuItem(
				_("Export to {format}").format(format="iCalendar"),
				imageName="text-calendar-ics.png",
				onActivate=onPlugExportToIcsClick,
			),
		)
		# --
		menu.show_all()
		menu.popup(None, None, None, None, 3, gevent.time)
		return True

	def onPlugAddClick(self, _w: gtk.Widget) -> None:
		# FIXME
		# Reize window to show all texts
		# self.plugAddTreeview.columns_autosize()  # FIXME
		column = self.plugAddTreeview.get_column(0)
		assert column is not None
		_x, _y, w, _h = column.cell_get_size()
		# log.debug(x, y, w, h)
		self.plugAddDialog.resize(
			w + 30,
			75 + 30 * len(self.plugAddTreeModel),
		)
		# ---------------
		self.plugAddDialog.run()
		self.pluginsToolbar.setCanAdd(len(self.plugAddItems) > 0)

	def plugAddDialogDeleteEvent(
		self,
		_widget: gtk.Widget,
		_gevent: gdk.Event,
	) -> bool:
		self.plugAddDialog.hide()
		return True

	def plugAddDialogClose(
		self,
		_widget: gtk.Widget,
	) -> None:
		self.plugAddDialog.hide()

	def plugTreeviewCellToggled(
		self,
		cell: gtk.CellRendererToggle,
		path: str,
	) -> None:
		model = self.plugListStore
		active = not cell.get_active()
		itr = model.get_iter(path)
		model.set_value(itr, 1, active)
		if active:
			plugI = model[path][0]
			plug = core.allPlugList.v[plugI]
			if not plug.loaded:
				plug = self.loadPlugin(plug, plugI)
			self.plugTreevCursorChanged()

	def plugTreeviewCellToggled2(
		self,
		cell: gtk.CellRendererToggle,
		path: str,
	) -> None:
		model = self.plugListStore
		active = not cell.get_active()
		itr = model.get_iter(path)
		model.set_value(itr, 2, active)

	def plugSetCursor(self, index: int) -> None:
		self.plugTreeview.set_cursor(gtk.TreePath.new_from_indices([index]))

	def plugTreeviewTop(self, _w: gtk.Widget) -> None:
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		listStore = self.plugListStore
		if index <= 0 or index >= len(listStore):
			gdk.beep()
			return
		listStore.prepend(list(listStore[index]))  # type: ignore[call-overload]
		listStore.remove(listStore.get_iter(str(index + 1)))
		self.plugSetCursor(0)

	def plugTreeviewBottom(self, _w: gtk.Widget) -> None:
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		listStore = self.plugListStore
		if index < 0 or index >= len(listStore) - 1:
			gdk.beep()
			return
		listStore.append(list(listStore[index]))  # type: ignore[call-overload]
		listStore.remove(listStore.get_iter(str(index)))
		self.plugSetCursor(len(listStore) - 1)

	def plugTreeviewUp(self, _w: gtk.Widget) -> None:
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		listStore = self.plugListStore
		if index <= 0 or index >= len(listStore):
			gdk.beep()
			return
		listStore.swap(
			listStore.get_iter(str(index - 1)),
			listStore.get_iter(str(index)),
		)
		self.plugSetCursor(index - 1)

	def plugTreeviewDown(self, _w: gtk.Widget) -> None:
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		listStore = self.plugListStore
		if index < 0 or index >= len(listStore) - 1:
			gdk.beep()
			return
		listStore.swap(
			listStore.get_iter(str(index)),
			listStore.get_iter(str(index + 1)),
		)
		self.plugSetCursor(index + 1)

	def plugTreevDragReceived(
		self,
		treev: gtk.TreeView,
		_context: gdk.DragContext,
		x: int,
		y: int,
		_selection: gtk.SelectionData,
		_target_id: int,
		_etime: int,
	) -> None:
		t = self.plugListStore
		cur = treev.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		dest = treev.get_dest_row_at_pos(x, y)
		if dest is None:
			t.move_after(
				t.get_iter(str(index)),
				t.get_iter(str(len(t) - 1)),
			)
		elif dest[1] in {
			gtk.TreeViewDropPosition.BEFORE,
			gtk.TreeViewDropPosition.INTO_OR_BEFORE,
		}:
			t.move_before(
				t.get_iter(str(index)),
				t.get_iter(str(dest[0].get_indices()[0])),
			)
		else:
			t.move_after(
				t.get_iter(str(index)),
				t.get_iter(str(dest[0].get_indices()[0])),
			)

	def onPlugDeleteClick(self, _w: gtk.Widget) -> None:
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		listStore = self.plugListStore
		n = len(listStore)
		if index < 0 or index >= n:
			gdk.beep()
			return
		j = listStore[index][0]
		listStore.remove(listStore.get_iter(str(index)))
		# j is index of deleted plugin
		self.plugAddItems.append(j)
		title = core.allPlugList.v[j].title
		self.plugAddTreeModel.append([title])
		log.debug(f"deleting {title}")
		self.pluginsToolbar.setCanAdd(True)
		if n > 1:
			self.plugSetCursor(min(n - 2, index))

	def plugAddDialogOK(self, _w: gtk.Widget | None) -> None:
		cur = self.plugAddTreeview.get_cursor()[0]
		if cur is None:
			gdk.beep()
			return
		index = cur.get_indices()[0]
		j = self.plugAddItems[index]
		cur2 = self.plugTreeview.get_cursor()[0]
		if cur2 is None:
			pos = len(self.plugListStore)
		else:
			pos = cur2.get_indices()[0] + 1
		plug = core.allPlugList.v[j]
		if plug is None:
			log.error("plug is None")
			return
		self.plugListStore.insert(  # type: ignore[no-untyped-call]
			pos,
			[
				j,
				True,
				False,
				plug.title,
			],
		)
		self.plugAddTreeModel.remove(self.plugAddTreeModel.get_iter(str(index)))
		self.plugAddItems.pop(index)
		self.plugAddDialog.hide()
		self.plugSetCursor(pos)  # pos == -1 # FIXME

	def plugAddTreevRActivate(
		self,
		_treev: gtk.TreeView,
		_path: gtk.TreePath,
		_col: gtk.TreeViewColumn,
	) -> None:
		self.plugAddDialogOK(None)  # FIXME
