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

import typing

from scal3 import event_lib as lib
from scal3 import logger, ui
from scal3.event_lib import ev
from scal3.event_lib.event_base import Event
from scal3.event_lib.group import EventGroup
from scal3.locale_man import tr as _
from scal3.ui_gtk import gdk, gtk
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.cal_obj_base import CalObjWidget
from scal3.ui_gtk.event.export import MultiGroupExportDialog
from scal3.ui_gtk.event.import_event import EventsImportWindow
from scal3.ui_gtk.event.manager.conf import (
	eventManPos,
	eventManShowDescription,
	loadConf,
	saveConf,
)
from scal3.ui_gtk.event.manager.context_menu import ContextMenu
from scal3.ui_gtk.event.manager.multi_select import MultiSelect
from scal3.ui_gtk.event.manager.operations import EventOps
from scal3.ui_gtk.event.manager.status import StatusBar
from scal3.ui_gtk.event.manager.ui import EventManagerUi
from scal3.ui_gtk.event.utils import checkEventsReadOnly
from scal3.ui_gtk.mywidgets.dialog import MyDialog
from scal3.ui_gtk.utils import rectangleContainsPoint

if typing.TYPE_CHECKING:
	from scal3.event_update_queue import EventUpdateRecord
	from scal3.ui_gtk import Dialog
	from scal3.ui_gtk.event.manager.toolbar import EventManagerToolbar
	from scal3.ui_gtk.event.manager.tree import EventManagerTree
	from scal3.ui_gtk.starcal_types import MainWinType

log = logger.get()

__all__ = ["EventManagerDialog"]

type W = gtk.Widget


class EventManagerDialog(CalObjWidget):
	objName = "eventMan"
	desc = _("Event Manager")
	# widgets and state created by EventManagerUi (manager.ui)
	menubar: gtk.MenuBar
	fileItem: gtk.MenuItem
	editItem: gtk.MenuItem
	mbarEditItem: gtk.MenuItem
	mbarCutItem: gtk.MenuItem
	mbarCopyItem: gtk.MenuItem
	mbarPasteItem: gtk.MenuItem
	mbarDupItem: gtk.MenuItem
	showDescItem: gtk.CheckMenuItem
	multiSelectItemMain: gtk.MenuItem
	multiSelectItem: gtk.CheckMenuItem
	multiSelectItemsOther: list[gtk.MenuItem]
	multiSelectHBox: gtk.Box
	multiSelectLabel: gtk.Label
	multiSelectPasteButton: gtk.Button
	toolbar: EventManagerToolbar
	tree: EventManagerTree
	sbar: gtk.Statusbar

	def __init__(
		self,
		mainWin: MainWinType,
	) -> None:
		loadConf()
		checkEventsReadOnly()  # FIXME
		self.dialog = MyDialog(transient_for=mainWin.win)
		self.w: gtk.Widget = self.dialog
		self.mainWin = mainWin
		self.initVars()
		ud.windowList.appendItem(self)
		ui.eventUpdateQueue.registerConsumer(self)
		# ----
		self.syncing = None  # or a tuple of (groupId, statusText)
		# (treeIter, move: bool)
		self.toPasteEvent: tuple[gtk.TreeIter, bool] | None = None
		# ----
		self.ops = EventOps(self)
		self.multiSel = MultiSelect(self)
		self.menu = ContextMenu(self)
		self.statusbar = StatusBar(self)
		self.ui = EventManagerUi(self)

	@property
	def multiSelect(self) -> bool:
		return self.multiSel.enabled

	def onShow(self, _w: W) -> None:
		self.dialog.move(*eventManPos.v)
		self.onConfigChange()

	@staticmethod
	def onDeleteEvent(_dialog: Dialog, _ge: gdk.Event) -> bool:
		# onResponse is called before onDeleteEvent
		# just return True, no need to do anything else
		# without this signal handler, the window will be destroyed
		# and can not be opened again
		return True

	def onResponse(self, _dialog: Dialog, _response_id: int) -> None:
		eventManPos.v = self.dialog.get_position()
		saveConf()
		# ---
		self.hide()

	def onConfigChange(self) -> None:
		super().onConfigChange()
		if not self.tree.isLoaded:
			if self.w.get_property("visible"):
				self.dialog.waitingDo(self.tree.reloadEvents)  # FIXME
			return

	def onEventUpdate(self, record: EventUpdateRecord) -> None:
		action = record.action

		if action == "r":  # reload group or trash
			if isinstance(record.obj, lib.EventTrash):
				self.tree.removeTrash()
				self.tree.appendTrash()
				return
			assert record.obj.id is not None
			self.tree.reloadGroupEvents(record.obj.id)

		elif action == "+g":  # new group with events inside it (imported)
			assert isinstance(record.obj, EventGroup), f"{record.obj=}"
			assert record.obj.id is not None
			try:
				groupIndex = ev.groups.index(record.obj.id)
			except ValueError:
				groupIndex = self.tree.topLevelCount() - 1
			self.tree.insertGroupTree(groupIndex, record.obj)

		elif action == "-g":
			log.error(f"Event Manager: onEventUpdate: unexpected {action=}")

		elif action == "eg":  # edit group
			group = record.obj
			assert isinstance(group, EventGroup), f"{group=}"
			assert group.id is not None
			groupIter = self.tree.getGroupIter(group.id)
			self.tree.setRowValues(groupIter, self.tree.getGroupRow(group))

		elif action == "-":
			assert isinstance(record.obj.parent, EventGroup), f"{record.obj.parent=}"
			assert isinstance(record.obj, Event), f"{record.obj}"
			assert record.obj.id is not None
			eventIter = self.tree.getEventIter(record.obj.id)
			if eventIter is None:
				if self.tree.isGroupLoaded(record.obj.parent.id):
					log.error(
						f"trying to delete non-existing event row, eid={record.obj.id}",
					)
				self.tree.addEventRowToTrash(record.obj)
				return
			path = self.tree.getPath(eventIter)
			parentPathObj = gtk.TreePath.new_from_indices(path.get_indices()[:1])
			expanded = self.tree.rowExpanded(parentPathObj)
			# log.debug(f"{path=}, {parentPathObj=}, {expanded=}")
			self.tree.removeIter(eventIter)
			self.tree.addEventRowToTrash(record.obj)
			if expanded:
				# FIXME: does not work!
				self.tree.expandRow(parentPathObj)

		elif action == "+":
			group2 = record.obj.parent
			assert isinstance(group2, EventGroup)
			assert isinstance(record.obj, Event), f"{record.obj=}"
			assert group2.id is not None
			if not self.tree.isGroupLoaded(group2.id):
				return
			parentIter = self.tree.getGroupIter(group2.id)
			# event is always added to the end of group (at least from
			# outside Event Manager dialog), unless we add a bool global option
			# to add all created events to the beginning of group (prepend)
			self.tree.appendEventRow(parentIter, record.obj)

		elif action == "e":
			assert isinstance(record.obj.parent, EventGroup), f"{record.obj.parent=}"
			assert isinstance(record.obj, Event), f"{record.obj=}"
			assert record.obj.id is not None
			eventIter = self.tree.getEventIter(record.obj.id)
			if eventIter is None:
				if self.tree.isGroupLoaded(record.obj.parent.id):
					log.error(
						f"trying to edit non-existing event row, eid={record.obj.id}",
					)
			else:
				self.tree.updateEventRowByIter(record.obj, eventIter)

	def rowActivated(
		self,
		_treev: gtk.TreeView,
		path: list[int],
		_col: gtk.TreeViewColumn,
	) -> None:
		if self.multiSelect:
			return
		if len(path) == 1:
			pathObj = gtk.TreePath.new_from_indices(path)
			if self.tree.rowExpanded(pathObj):
				self.tree.collapseRow(pathObj)
			else:
				self.tree.expandRow(pathObj)
		elif len(path) == 2:
			if self.tree.isArchivedGroupRow(path):
				self.ops.editGroupByPath(path)
			else:
				self.ops.editEventByPath(path)

	def onKeyPress(self, _dialog: W, gevent: gdk.EventKey) -> bool:
		kname = gdk.keyval_name(gevent.keyval)
		if not kname:
			return False
		kname = kname.lower()
		if kname == "escape":
			return self.onEscape()
		if kname == "menu":  # noqa: SIM102
			# simulate right click (key beside Right-Ctrl)
			if self.multiSelect:
				self.menubar.select_item(self.multiSelectItemMain)
				return True
		return False
		# return self.onTreeviewKeyPress(self.tree.getWidget(), gevent)

	def onTreeviewKeyPress(
		self,
		_treev: gtk.TreeView,
		gevent: gdk.EventKey,
	) -> bool:
		# log.debug(now()-gdk.CURRENT_TIME/1000.0)
		# gdk.CURRENT_TIME == 0
		# gevent.time == gtk.get_current_event_time()	# OK
		kname = gdk.keyval_name(gevent.keyval)
		if not kname:
			return False
		kname = kname.lower()
		if kname == "menu":  # simulate right click (key beside Right-Ctrl)
			if self.multiSelect:
				self.menubar.select_item(self.multiSelectItemMain)
				return True
			path = self.tree.getSelectedPath()
			if path:
				self.menu.menuKeyPressOnPath(path, gevent)
				return True

		elif kname == "delete":
			if self.multiSelect:
				self.multiSel.delete()
			else:
				self.ops.moveSelectionToTrash()
			return True

		elif kname == "space":
			if self.multiSelect:
				self.multiSel.treeviewToggleSelected()
				return True

		elif kname in {"up", "down"}:
			if self.multiSelect and gevent.state & gdk.ModifierType.SHIFT_MASK > 0:
				isDown = kname == "down"
				self.multiSel.shiftUpDownPress(isDown)
				return True

		return False

	def onEscape(self) -> bool:
		if self.multiSelect:
			self.multiSel.cancel()
			return True
		self.hide()
		return True

	def onMenuBarExportClick(self, _menuItem: gtk.MenuItem) -> None:
		MultiGroupExportDialog(transient_for=self.dialog).run()

	def onMenuBarImportClick(self, _menuItem: gtk.MenuItem) -> None:
		EventsImportWindow(self.dialog).present()

	def _do_recoverOrphans(self) -> None:
		newGroup = ev.groups.recoverOrphans()
		if newGroup is not None:
			self.tree.appendGroupTree(newGroup)

	def onMenuBarOrphanClick(self, _menuItem: gtk.MenuItem) -> None:
		self.dialog.waitingDo(self._do_recoverOrphans)

	def mbarEditMenuPopup(self, _menuItem: gtk.MenuItem) -> None:
		path = self.tree.getSelectedPath()
		if path is None:
			return
		selected = bool(path)
		eventSelected = (
			selected and len(path) == 2 and not self.tree.isArchivedGroupRow(path)
		)
		# ---
		self.mbarEditItem.set_sensitive(selected)
		self.mbarCutItem.set_sensitive(eventSelected)
		self.mbarCopyItem.set_sensitive(eventSelected)
		self.mbarDupItem.set_sensitive(selected)
		# ---
		try:
			group = self.tree.getGroupByPath(path)
		except ValueError:
			canPaste = False
		else:
			canPaste = self.ops.canPasteToGroup(group)
		self.mbarPasteItem.set_sensitive(selected and canPaste)

	def onMenuBarEditClick(self, _menuItem: gtk.MenuItem) -> None:
		path = self.tree.getSelectedPath()
		if not path:
			return
		if len(path) == 1:
			self.ops.editGroupByPath(path)
		elif len(path) == 2:
			if self.tree.isArchivedGroupRow(path):
				self.ops.editGroupByPath(path)
			else:
				self.ops.editEventByPath(path)

	def onMenuBarCutClick(self, _menuItem: gtk.MenuItem) -> None:
		path = self.tree.getSelectedPath()
		if not path:
			return
		if len(path) == 2:
			self.toPasteEvent = (self.tree.iterFromPath(path), True)

	def onMenuBarCopyClick(self, _menuItem: gtk.MenuItem) -> None:
		path = self.tree.getSelectedPath()
		if not path:
			return
		if len(path) == 2:
			self.toPasteEvent = (self.tree.iterFromPath(path), False)

	def onMenuBarPasteClick(self, _menuItem: gtk.MenuItem) -> None:
		path = self.tree.getSelectedPath()
		if not path:
			return
		self.ops.pasteEventToPath(path)

	def onCollapseAllClick(self, _menuItem: gtk.MenuItem) -> None:
		return self.tree.collapseAll()

	def onExpandAllAllClick(self, _menuItem: gtk.MenuItem) -> None:
		return self.tree.expandAll()

	def _do_showDescItemToggled(self) -> None:
		active = self.showDescItem.get_active()
		eventManShowDescription.v = active
		saveConf()
		if active:
			self.tree.appendColumn(self.tree.colDesc)
		else:
			self.tree.removeColumn(self.tree.colDesc)

	def showDescItemToggled(self, _menuItem: gtk.MenuItem) -> None:
		self.dialog.waitingDo(self._do_showDescItemToggled)

	def onTreeviewLeftButtonPress(
		self,
		_treev: gtk.TreeView,
		gevent: gdk.EventButton,
		path: list[int],
		col: gtk.TreeViewColumn,
	) -> None:
		if len(path) != 1:
			return

		groupId = self.tree.getRowId(self.tree.iterFromPath(path))
		if groupId > 0 and col == self.tree.pixbufCol:
			group = ev.groups[groupId]
			self.ops.toggleEnableGroup(group, path)
			self.tree.setCursorPath(path)
			return

		if self.multiSelect and gevent.state & gdk.ModifierType.SHIFT_MASK > 0:
			self.multiSel.shiftButtonPress(path)

	def onTreeviewButtonPress(
		self,
		_treev: gtk.TreeView,
		gevent: gdk.EventButton,
	) -> None:
		pos_t = self.tree.getPathAtPos(int(gevent.x), int(gevent.y))
		if not pos_t:
			return

		pathObj: gtk.TreePath | None
		pathObj, col, _xRel, _yRel = pos_t
		if not pathObj:
			return
		path = pathObj.get_indices()

		if gevent.button == 3:
			if self.multiSelect:
				return
			self.menu.openRightClickMenu(path, gevent.time)
			return

		if gevent.button == 1:
			if not col:
				return
			if not rectangleContainsPoint(
				self.tree.getCellArea(pathObj, col),
				gevent.x,
				gevent.y,
			):
				return
			self.onTreeviewLeftButtonPress(_treev, gevent, path, col)
