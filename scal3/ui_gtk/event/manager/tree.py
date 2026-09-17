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
from scal3.event_lib import ev
from scal3.locale_man import tr as _
from scal3.ui_gtk import GdkPixbuf, gdk, gtk
from scal3.ui_gtk.event import common
from scal3.ui_gtk.event.manager.conf import (
	archivedGroupsRowId,
	eventManShowDescription,
)
from scal3.ui_gtk.event.utils import eventTreeIconPixbuf

if TYPE_CHECKING:
	from collections.abc import Callable, Iterable

	from scal3.event_lib.pytypes import EventGroupType, EventType
	from scal3.event_lib.trash import EventTrash
	from scal3.ui_gtk.event.manager.dialog import EventManagerDialog

__all__ = ["EventManagerTree"]

log = logger.get()


class EventManagerTree:
	"""Owns the tree view, tree store, its row iterators and path resolution."""

	def __init__(self, dialog: EventManagerDialog) -> None:
		self.dialog = dialog
		self._widget = gtk.TreeView()
		self._widget.set_search_column(3)

		# self._widget.set_fixed_height_mode(True)
		# ^ causes multi-select checkbox to be hidden after row-expanded in
		# multi-select mode

		# self._widget.set_headers_visible(False)  # FIXME
		# self._widget.get_selection().set_mode(gtk.SelectionMode.MULTIPLE)  # FIXME
		# self._widget.set_rubber_banding(gtk.SelectionMode.MULTIPLE)  # FIXME
		# self._widget.connect("realize", self.onTreeviewRealize)

		self.treeModel = gtk.TreeStore(
			bool,  # multi-select mode checkbox
			int,  # eventId or groupId, -1 for trash
			GdkPixbuf.Pixbuf,  # eventIcon, groupPixbuf or trashIcon
			str,  # eventSummary, groupTitle or trashTitle
			str,  # eventDescription, empty for group or trash
		)
		self._widget.set_model(self.treeModel)
		self.idColIndex = 1
		self.summaryColIndex = 3
		self.groupIterById: dict[int, gtk.TreeIter] = {}
		self.trashIter: gtk.TreeIter | None = None
		self.archivedGroupsIter: gtk.TreeIter | None = None
		self.isLoaded = False
		self.loadedGroupIds: set[int] = set()
		self.eventsIter: dict[int, gtk.TreeIter] = {}
		self.buildColumns()

	def getWidget(self) -> gtk.Widget:
		"""Return the tree view widget, for packing/adding only."""
		return self._widget

	def connectSignals(
		self,
		onSelectionChanged: Callable[..., Any],
		onButtonPress: Callable[..., Any],
		onRowActivated: Callable[..., Any],
		onTreeviewKeyPress: Callable[..., Any],
	) -> None:
		self._widget.get_selection().connect("changed", onSelectionChanged)
		self._widget.connect("button-press-event", onButtonPress)
		self._widget.connect("row-activated", onRowActivated)
		self._widget.connect("key-press-event", onTreeviewKeyPress)

	def rowExpanded(self, pathObj: gtk.TreePath) -> bool:
		return self._widget.row_expanded(pathObj)

	def expandRow(self, pathObj: gtk.TreePath) -> None:
		self._widget.expand_row(pathObj, False)

	def collapseRow(self, pathObj: gtk.TreePath) -> None:
		self._widget.collapse_row(pathObj)

	def expandToPath(self, pathObj: gtk.TreePath) -> None:
		self._widget.expand_to_path(pathObj)

	def collapseAll(self) -> None:
		self._widget.collapse_all()

	def expandAll(self) -> None:
		self._widget.expand_all()

	def appendColumn(self, col: gtk.TreeViewColumn) -> None:
		self._widget.append_column(col)

	def removeColumn(self, col: gtk.TreeViewColumn) -> None:
		self._widget.remove_column(col)

	def getPathAtPos(
		self, x: int, y: int
	) -> tuple[gtk.TreePath | None, gtk.TreeViewColumn | None, int, int] | None:
		return self._widget.get_path_at_pos(x, y)

	def getCellArea(
		self,
		pathObj: gtk.TreePath,
		col: gtk.TreeViewColumn,
	) -> gdk.Rectangle:
		return self._widget.get_cell_area(pathObj, col)

	def getColumn(self, index: int) -> gtk.TreeViewColumn:
		col = self._widget.get_column(index)
		assert col is not None
		return col

	def translateCoordinates(
		self,
		w: gtk.Widget,
		x: int,
		y: int,
	) -> tuple[int, int] | None:
		return self._widget.translate_coordinates(w, x, y)

	def removeTrash(self) -> None:
		if self.trashIter is not None:
			self.treeModel.remove(self.trashIter)

	def removeIter(self, gIter: gtk.TreeIter) -> None:
		self.treeModel.remove(gIter)

	def removeRow(self, path: list[int]) -> None:
		self.removeIter(self.iterFromPath(path))

	def removePath(self, pathObj: gtk.TreePath) -> None:
		self.treeModel.remove(self.treeModel.get_iter(pathObj))

	def setValue(self, gIter: gtk.TreeIter, index: int, value: Any) -> None:
		self.treeModel.set_value(gIter, index, value)  # type: ignore[no-untyped-call]

	def setRowValues(self, gIter: gtk.TreeIter, values: Iterable[Any]) -> None:
		for i, value in enumerate(values):
			self.treeModel.set_value(gIter, i, value)  # type: ignore[no-untyped-call]

	def getPath(self, gIter: gtk.TreeIter) -> gtk.TreePath:
		return self.treeModel.get_path(gIter)

	def getIter(self, pathObj: gtk.TreePath | str) -> gtk.TreeIter:
		return self.treeModel.get_iter(pathObj)

	def getValue(self, gIter: gtk.TreeIter, index: int) -> Any:
		return self.treeModel.get_value(gIter, index)

	def iterChildren(self, gIter: gtk.TreeIter) -> gtk.TreeIter | None:
		return self.treeModel.iter_children(gIter)

	def iterNext(self, gIter: gtk.TreeIter) -> gtk.TreeIter | None:
		return self.treeModel.iter_next(gIter)

	def moveBefore(self, srcIter: gtk.TreeIter, tarIter: gtk.TreeIter) -> None:
		self.treeModel.move_before(srcIter, tarIter)

	def moveAfter(self, srcIter: gtk.TreeIter, tarIter: gtk.TreeIter) -> None:
		self.treeModel.move_after(srcIter, tarIter)

	def iterChildrenCount(self, gIter: gtk.TreeIter) -> int:
		return self.treeModel.iter_n_children(gIter)

	def iterNthChild(self, gIter: gtk.TreeIter, index: int) -> gtk.TreeIter | None:
		return self.treeModel.iter_nth_child(gIter, index)

	def topLevelCount(self) -> int:
		return len(self.treeModel)

	def isGroupLoaded(self, gid: int | None) -> bool:
		return gid in self.loadedGroupIds

	def markGroupLoaded(self, gid: int) -> None:
		self.loadedGroupIds.add(gid)

	def unmarkGroupLoaded(self, gid: int) -> None:
		self.loadedGroupIds.discard(gid)

	def getGroupIter(self, gid: int) -> gtk.TreeIter:
		return self.groupIterById[gid]

	def removeGroupIter(self, gid: int) -> None:
		del self.groupIterById[gid]

	def getEventIter(self, eid: int) -> gtk.TreeIter | None:
		return self.eventsIter.get(eid)

	def addGroupEventsToTrash(self, group: EventGroupType) -> None:
		assert self.trashIter is not None
		trashedIds = group.idList
		if ev.trash.addEventsToBeginning:
			for eid in reversed(trashedIds):
				self.insertEventRow(self.trashIter, 0, group[eid])
		else:
			for eid in trashedIds:
				self.appendEventRow(self.trashIter, group[eid])

	def clearTrashRows(self) -> None:
		assert self.trashIter is not None
		self.removeIterChildren(self.trashIter)

	def refreshTrashRow(self) -> None:
		assert self.trashIter is not None
		self.treeModel.set_value(  # type: ignore[no-untyped-call]
			self.trashIter,
			2,
			eventTreeIconPixbuf(ev.trash.getIconRel()),
		)
		self.treeModel.set_value(  # type: ignore[no-untyped-call]
			self.trashIter,
			3,
			ev.trash.title,
		)

	def getTrashIndex(self) -> int:
		assert self.trashIter is not None
		return self.treeModel.get_path(self.trashIter).get_indices()[0]

	def buildColumns(self) -> None:
		cell: gtk.CellRenderer
		# ---
		cell = gtk.CellRendererToggle()
		# cell.set_property("activatable", True)
		# cell.set_radio(True)
		cell.connect("toggled", self.dialog.multiSel.treeviewToggle)
		col = gtk.TreeViewColumn(
			title="",
			cell_renderer=cell,
		)
		col.set_cell_data_func(cell, self.dialog.multiSel.treeviewToggleStatus)
		col.set_sizing(gtk.TreeViewColumnSizing.FIXED)
		col.add_attribute(cell, "active", 0)
		col.set_resizable(False)
		col.set_property("expand", False)
		col.set_visible(False)
		self.multiSelectColumn = col
		self._widget.append_column(col)
		# ---
		cell = gtk.CellRendererPixbuf()
		col = gtk.TreeViewColumn(
			title="",
			cell_renderer=cell,
		)
		col.set_sizing(gtk.TreeViewColumnSizing.FIXED)
		col.add_attribute(cell, "pixbuf", 2)
		col.set_property("expand", False)
		self._widget.append_column(col)
		self.pixbufCol = col
		# ---
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(
			title=_("Summary"),
			cell_renderer=cell,
			text=3,
		)
		col.set_sizing(gtk.TreeViewColumnSizing.FIXED)
		col.set_resizable(True)
		col.set_property("expand", True)
		self._widget.append_column(col)
		# ---
		cell = gtk.CellRendererText()
		col = self.colDesc = gtk.TreeViewColumn(
			title=_("Description"),
			cell_renderer=cell,
			text=4,
		)
		col.set_sizing(gtk.TreeViewColumnSizing.FIXED)
		col.set_property("expand", True)
		if eventManShowDescription.v:
			self._widget.append_column(col)
		# ---
		# self._widget.set_search_column(2)-- or 3

	def getRowId(self, gIter: gtk.TreeIter) -> int:
		return self.treeModel.get_value(gIter, self.idColIndex)  # type: ignore[no-any-return]

	@staticmethod
	def getGroupRow(
		group: EventGroupType,
	) -> tuple[bool, int, GdkPixbuf.Pixbuf, str, str]:
		ident, pbuf, title = common.getGroupRow(group)
		return (False, ident, pbuf, title, "")

	@staticmethod
	def getEventRow(
		event: EventType,
	) -> list[Any]:
		# tuple[bool, int, GdkPixbuf.Pixbuf | None, str, str]
		# but Gtk stubs want list[Any]
		pixbuf = eventTreeIconPixbuf(event.getIconRel())
		if event.icon and pixbuf is None:
			log.error(
				f"getEventRow: invalid {event.icon=} "
				f"for {event.id=} in {event.parent=}",
			)
		assert event.id is not None
		return [
			False,
			event.id,
			pixbuf,
			event.autoSummary,
			event.getShownDescription(),
		]

	def appendEventRow(
		self,
		parentIter: gtk.TreeIter,
		event: EventType,
	) -> gtk.TreeIter:
		assert event.id is not None
		eventIter = self.treeModel.append(parentIter, self.getEventRow(event))
		self.eventsIter[event.id] = eventIter
		return eventIter

	def insertEventRow(
		self,
		parentIter: gtk.TreeIter,
		position: int,
		event: EventType,
	) -> gtk.TreeIter:
		assert event.id is not None
		eventIter: gtk.TreeIter = self.treeModel.insert(  # type: ignore[no-untyped-call]
			parentIter,
			position,
			self.getEventRow(event),
		)
		self.eventsIter[event.id] = eventIter
		return eventIter

	def insertEventRowAfter(
		self,
		parentIter: gtk.TreeIter,
		siblingIter: gtk.TreeIter,
		event: EventType,
	) -> gtk.TreeIter:
		assert event.id is not None
		eventIter: gtk.TreeIter = self.treeModel.insert_after(  # type: ignore[no-untyped-call]
			parentIter,
			siblingIter,
			self.getEventRow(event),
		)
		self.eventsIter[event.id] = eventIter
		return eventIter

	def insertGroup(
		self,
		position: int,
		group: EventGroupType,
	) -> gtk.TreeIter:
		assert group.id is not None
		groupIter: gtk.TreeIter = self.treeModel.insert(  # type: ignore[no-untyped-call]
			None,
			position,
			self.getGroupRow(group),
		)
		self.groupIterById[group.id] = groupIter
		return groupIter

	def appendGroupEvents(
		self,
		group: EventGroupType,
		groupIter: gtk.TreeIter,
	) -> None:
		assert group.id is not None
		for event in group:
			self.appendEventRow(groupIter, event)
		self.loadedGroupIds.add(group.id)

	def insertGroupTree(self, position: int, group: EventGroupType) -> None:
		groupIter = self.insertGroup(position, group)
		if group.enable:
			self.appendGroupEvents(group, groupIter)

	def appendGroup(self, group: EventGroupType) -> gtk.TreeIter:
		assert group.id is not None
		beforeIter = self.archivedGroupsIter or self.trashIter
		groupIter: gtk.TreeIter = self.treeModel.insert_before(  # type: ignore[no-untyped-call]
			None,
			beforeIter,
			self.getGroupRow(group),
		)
		self.groupIterById[group.id] = groupIter
		return groupIter

	def appendGroupTree(self, group: EventGroupType) -> None:
		groupIter = self.appendGroup(group)
		if group.enable:
			self.appendGroupEvents(group, groupIter)

	def appendTrash(self) -> None:
		self.trashIter = self.treeModel.append(
			None,
			[
				False,
				-1,
				eventTreeIconPixbuf(ev.trash.getIconRel()),
				ev.trash.title,
				"",
			],
		)
		for event in ev.trash:
			self.appendEventRow(self.trashIter, event)

	def appendArchivedGroupTree(self, group: EventGroupType) -> None:
		assert self.archivedGroupsIter is not None
		assert group.id is not None
		groupIter: gtk.TreeIter = self.treeModel.append(
			self.archivedGroupsIter,
			list(self.getGroupRow(group)),
		)
		self.groupIterById[group.id] = groupIter

	def appendArchivedGroups(self) -> None:
		self.archivedGroupsIter = self.treeModel.insert_before(  # type: ignore[no-untyped-call]
			None,
			self.trashIter,
			[
				False,
				archivedGroupsRowId,
				eventTreeIconPixbuf(ev.archivedGroups.getIconRel()),
				ev.archivedGroups.desc,
				"",
			],
		)
		for group in ev.archivedGroups:
			self.appendArchivedGroupTree(group)

	def reloadGroupEvents(self, gid: int) -> None:
		groupIter = self.groupIterById[gid]
		assert self.getRowId(groupIter) == gid
		# --
		self.removeIterChildren(groupIter)
		# --
		group = self.getGroupById(gid)
		if gid not in self.loadedGroupIds:
			return
		for event in group:
			self.appendEventRow(groupIter, event)

	def reloadEvents(self) -> None:
		self.treeModel.clear()
		self.appendTrash()
		for group in ev.groups:
			self.appendGroupTree(group)
		self.appendArchivedGroups()
		self.dialog.statusbar.cursorChanged()
		# ----
		self.isLoaded = True

	def iterFromPath(self, path: list[int]) -> gtk.TreeIter:
		return self.treeModel.get_iter(gtk.TreePath.new_from_indices(path))

	def setCursorPath(self, path: list[int] | gtk.TreePath) -> None:
		if isinstance(path, list):
			path = gtk.TreePath.new_from_indices(path)
		self._widget.set_cursor(path)

	def getEventAndGroupByPath(
		self, path: list[int]
	) -> tuple[EventGroupType, EventType]:
		assert len(path) == 2
		assert not self.isArchivedGroupRow(path)
		groupIndex = path[0]
		eventId = self.getRowId(self.iterFromPath(path))
		groupId = self.getRowId(self.iterFromPath([groupIndex]))
		group = ev.groups[groupId]
		return group, group[eventId]

	def getEventAndParentByPath(
		self, path: list[int]
	) -> tuple[EventGroupType | EventTrash, EventType]:
		assert len(path) == 2
		assert not self.isArchivedGroupRow(path)
		groupIndex = path[0]
		eventId = self.getRowId(self.iterFromPath(path))
		groupId = self.getRowId(self.iterFromPath([groupIndex]))
		parent: EventGroupType | EventTrash
		if groupId == -1:
			parent = ev.trash
		else:
			parent = ev.groups[groupId]
		return parent, parent[eventId]

	def getEventByPath(self, path: list[int]) -> EventType:
		assert len(path) == 2
		assert not self.isArchivedGroupRow(path)
		groupIndex = path[0]
		eventId = self.getRowId(self.iterFromPath(path))
		groupId = self.getRowId(self.iterFromPath([groupIndex]))
		group = ev.groups[groupId]
		return group[eventId]

	def getGroupById(self, gid: int) -> EventGroupType:
		try:
			return ev.groups[gid]
		except KeyError:
			return ev.archivedGroups[gid]

	def getGroupByPath(self, path: list[int]) -> EventGroupType:
		groupIndex = path[0]
		groupId = self.getRowId(self.iterFromPath([groupIndex]))
		if groupId == archivedGroupsRowId:
			groupId = self.getRowId(self.iterFromPath(path))
			return ev.archivedGroups[groupId]
		if groupId <= 0:
			raise ValueError(f"invalid group id {groupId}, {path=}")
		return ev.groups[groupId]

	def getGroupOrTrashByPath(self, path: list[int]) -> EventGroupType | EventTrash:
		groupIndex = path[0]
		groupId = self.getRowId(self.iterFromPath([groupIndex]))
		if groupId == -1:
			return ev.trash
		if groupId <= 0:
			raise ValueError(f"invalid group id {groupId}, {path=}")
		return ev.groups[groupId]

	def isArchivedGroupsNode(self, path: list[int]) -> bool:
		return (
			len(path) == 1
			and self.getRowId(self.iterFromPath(path)) == archivedGroupsRowId
		)

	def isArchivedGroupRow(self, path: list[int]) -> bool:
		return (
			len(path) == 2
			and self.getRowId(self.iterFromPath([path[0]])) == archivedGroupsRowId
		)

	def removeIterChildren(self, gIter: gtk.TreeIter) -> None:
		while (childIter := self.treeModel.iter_children(gIter)) is not None:
			self.treeModel.remove(childIter)

	def updateEventRow(self, event: EventType) -> None:
		assert event.id is not None
		self.updateEventRowByIter(
			event,
			self.eventsIter[event.id],
		)

	def updateEventRowByIter(
		self,
		event: EventType,
		eventIter: gtk.TreeIter,
	) -> None:
		for i, value in enumerate(self.getEventRow(event)):
			self.treeModel.set_value(eventIter, i, value)  # type: ignore[no-untyped-call]
		self.dialog.statusbar.cursorChanged()

	def addNewEventRow(
		self,
		group: EventGroupType,
		groupIter: gtk.TreeIter,
		event: EventType,
	) -> None:
		if group.id not in self.loadedGroupIds:
			return
		if group.addEventsToBeginning:
			self.insertEventRow(groupIter, 0, event)
			return
		self.appendEventRow(groupIter, event)

	def addEventRowToTrash(self, event: EventType) -> None:
		assert self.trashIter is not None
		if ev.trash.addEventsToBeginning:
			self.insertEventRow(self.trashIter, 0, event)
		else:
			self.appendEventRow(self.trashIter, event)

	def getSelectedPath(self) -> list[int] | None:
		iter_ = self._widget.get_selection().get_selected()[1]
		if iter_ is None:
			return None
		return self.treeModel.get_path(iter_).get_indices()

	def scroll_to_cell(self, path: list[int] | gtk.TreePath) -> None:
		if isinstance(path, list):
			path = gtk.TreePath.new_from_indices(path)
		self._widget.scroll_to_cell(
			path=path,
			column=None,
			use_align=False,
			row_align=0,
			col_align=0,
		)
