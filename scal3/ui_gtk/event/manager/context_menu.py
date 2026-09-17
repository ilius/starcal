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

from scal3 import event_lib as lib
from scal3 import logger
from scal3.event_lib import ev
from scal3.event_lib.trash import EventTrash
from scal3.locale_man import rtl
from scal3.locale_man import tr as _
from scal3.ui_gtk import Menu, gdk, gtk
from scal3.ui_gtk.event.history import EventHistoryDialog
from scal3.ui_gtk.event.manager.conf import archivedGroupsRowId
from scal3.ui_gtk.event.utils import (
	eventWriteImageMenuItem,
	eventWriteMenuItem,
	menuItemFromEventGroup,
)
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.utils import (
	get_menu_width,
	widgetActionCallback,
)

if TYPE_CHECKING:
	from scal3.event_lib.pytypes import EventGroupType, EventType
	from scal3.ui_gtk.event.manager.dialog import EventManagerDialog

__all__ = ["ContextMenu"]

log = logger.get()

type W = gtk.Widget


class ContextMenu:
	"""Builds and shows the right-click context menus."""

	def __init__(self, dialog: EventManagerDialog) -> None:
		self.dialog = dialog

	@widgetActionCallback
	def historyOfEventFromMenu(self, path: list[int]) -> None:
		event = self.dialog.tree.getEventByPath(path)
		EventHistoryDialog(event, transient_for=self.dialog.dialog).dialog.run()

	def trashAddRightClickMenuItems(
		self,
		menu: gtk.Menu,
		path: list[int],
		trash: EventTrash,
	) -> None:
		# log.debug("right click on trash", group.title)
		menu.add(
			eventWriteMenuItem(
				_("Edit"),
				imageName="document-edit.svg",
				func=self.dialog.ops.editTrashFromMenu,
			),
		)

		menu.add(
			eventWriteMenuItem(
				_("Sort Events"),
				imageName="view-sort-ascending.svg",
				func=self.dialog.ops.groupSortFromMenu(path),
				sensitive=bool(trash.idList),
			),
		)

		# FIXME: _("Empty {title}").format(title=group.title),
		menu.add(
			eventWriteMenuItem(
				_("Empty Trash"),
				imageName="sweep.svg",
				func=self.dialog.ops.emptyTrash,
				sensitive=bool(trash.idList),
			),
		)

	def groupAddRightClickMenuItems(
		self,
		menu: gtk.Menu,
		path: list[int],
		group: EventGroupType,
	) -> None:
		# log.debug("right click on group", group.title)
		menu.add(
			eventWriteMenuItem(
				_("Edit"),
				imageName="document-edit.svg",
				func=self.dialog.ops.editGroupFromMenu(path),
			),
		)
		eventTypes = group.acceptsEventTypes
		if eventTypes is None:
			eventTypes = lib.classes.event.names
		if len(eventTypes) > 3:
			menu.add(
				eventWriteMenuItem(
					_("Add Event"),
					imageName="list-add.svg",
					func=self.dialog.ops.addGenericEventToGroupFromMenu(path, group),
				),
			)
		else:
			for eventType in eventTypes:
				# if eventType == "custom":  # FIXME
				# 	eventTypeDesc = _("Event")
				# else:
				eventTypeDesc = lib.classes.event.byName[eventType].desc
				label = _("Add {eventType}").format(
					eventType=eventTypeDesc,
				)
				menu.add(
					eventWriteMenuItem(
						label,
						imageName="list-add.svg",
						func=self.dialog.ops.addEventToGroupFromMenu(
							path, group, eventType, label
						),
					),
				)
		pasteItem = eventWriteMenuItem(
			_("Paste Event"),
			imageName="edit-paste.svg",
			func=self.dialog.ops.pasteEventFromMenu(path),
		)
		menu.add(pasteItem)
		pasteItem.set_sensitive(self.dialog.ops.canPasteToGroup(group))
		# --
		if group.remoteIds:
			aid, _remoteGid = group.remoteIds
			try:
				account = ev.accounts[aid]
			except KeyError:
				log.exception("")
			else:
				if account.enable:
					menu.add(gtk.SeparatorMenuItem())
					menu.add(
						eventWriteMenuItem(
							_("Synchronize"),
							imageName="",
							# FIXME: sync-events.svg
							func=self.dialog.ops.syncGroupFromMenu(path, account),
						),
					)
				# else:  # FIXME
		# --
		menu.add(gtk.SeparatorMenuItem())
		menu.add(
			eventWriteMenuItem(
				_("Duplicate"),
				imageName="edit-copy.svg",
				func=self.dialog.ops.duplicateGroupFromMenu(path),
			),
		)
		# ---
		dupAllItem = eventWriteMenuItem(
			_("Duplicate with All Events"),
			imageName="edit-copy.svg",
			func=self.dialog.ops.duplicateGroupWithEventsFromMenu(path),
		)
		menu.add(dupAllItem)
		dupAllItem.set_sensitive(
			not group.isReadOnly() and bool(group.idList),
		)
		# ---
		menu.add(gtk.SeparatorMenuItem())
		menu.add(
			eventWriteMenuItem(
				_("Archive"),
				imageName="user-archive.svg",
				func=self.dialog.ops.archiveGroupFromMenu(path),
			),
		)
		menu.add(
			eventWriteMenuItem(
				_("Delete Group"),
				imageName="edit-delete.svg",
				func=self.dialog.ops.deleteGroupFromMenu(path),
			),
		)
		menu.add(gtk.SeparatorMenuItem())

		def export(w: W) -> None:
			self.dialog.ops.groupExportFromMenu(w, group)

		menu.add(
			ImageMenuItem(
				_("Export", ctx="menu"),
				# imageName="export-events.svg",  # FIXME
				onActivate=export,
			),
		)
		# ---
		menu.add(
			eventWriteMenuItem(
				_("Sort Events"),
				imageName="view-sort-ascending.svg",
				func=self.dialog.ops.groupSortFromMenu(path),
				sensitive=not group.isReadOnly() and bool(group.idList),
			),
		)
		# ---
		convertItem = eventWriteMenuItem(
			_("Convert Calendar Type"),
			imageName="convert-calendar.svg",
			func=self.dialog.ops.groupConvertCalTypeFromMenu(group),
		)
		menu.add(convertItem)
		convertItem.set_sensitive(
			not group.isReadOnly() and bool(group.idList),
		)
		# ---
		for newGroupType in group.canConvertTo:
			newGroupTypeDesc = lib.classes.group.byName[newGroupType].desc
			menu.add(
				eventWriteMenuItem(
					_("Convert to {groupType}").format(
						groupType=newGroupTypeDesc,
					),
					func=self.dialog.ops.groupConvertToFromMenu(group, newGroupType),
				),
			)
		# ---
		bulkItem = eventWriteMenuItem(
			_("Bulk Edit Events"),
			imageName="document-edit.svg",
			func=self.dialog.ops.groupBulkEditFromMenu(group, path),
		)
		menu.add(bulkItem)
		bulkItem.set_sensitive(
			not group.isReadOnly() and bool(group.idList),
		)
		# ---
		for actionName, actionFuncName in group.actions:
			menu.add(
				eventWriteMenuItem(
					_(actionName),
					func=self.dialog.ops.onGroupActionClick(group, actionFuncName),
				),
			)

	def archivedGroupAddRightClickMenuItems(
		self,
		menu: gtk.Menu,
		path: list[int],
	) -> None:
		# log.debug("right click on archived group", group.title)
		menu.add(
			eventWriteMenuItem(
				_("Edit"),
				imageName="document-edit.svg",
				func=self.dialog.ops.editGroupFromMenu(path),
			),
		)
		# --
		menu.add(gtk.SeparatorMenuItem())
		menu.add(
			eventWriteMenuItem(
				_("Unarchive"),
				imageName="user-archive.svg",
				func=self.dialog.ops.unarchiveGroupFromMenu(path),
			),
		)
		# --
		menu.add(gtk.SeparatorMenuItem())
		menu.add(
			eventWriteMenuItem(
				_("Delete Group"),
				imageName="edit-delete.svg",
				func=self.dialog.ops.deleteGroupFromMenu(path),
			),
		)

	def eventAddRightClickMenuItems(
		self,
		menu: gtk.Menu,
		path: list[int],
		group: EventGroupType | EventTrash,
		event: EventType,
	) -> None:
		# log.debug("right click on event", event.autoSummary)
		menu.add(
			eventWriteMenuItem(
				_("Edit"),
				imageName="document-edit.svg",
				func=self.dialog.ops.editEventFromMenu(path),
			),
		)
		# ----
		menu.add(
			eventWriteImageMenuItem(
				_("History"),
				"history.svg",
				func=self.historyOfEventFromMenu(path),
			),
		)
		# ----
		moveToItem = eventWriteMenuItem(
			_("Move to {title}").format(title="..."),
		)
		moveToMenu = Menu()
		for new_group in ev.groups:
			assert new_group.id is not None
			if new_group.id == group.id:
				continue
			# if not new_group.enable:  # FIXME
			# 	continue
			new_groupPath = self.dialog.tree.getPath(
				self.dialog.tree.getGroupIter(new_group.id)
			).get_indices()
			if event.name in new_group.acceptsEventTypes:
				moveToMenu.add(
					menuItemFromEventGroup(
						new_group,
						onActivate=self.dialog.ops.moveEventToPathFromMenu(
							path, new_groupPath
						),
					),
				)
		moveToItem.set_submenu(moveToMenu)
		menu.add(moveToItem)
		# ----
		menu.add(gtk.SeparatorMenuItem())
		# ----
		menu.add(
			eventWriteMenuItem(
				_("Cut"),
				imageName="edit-cut.svg",
				func=self.dialog.ops.cutEventFromMenu(path),
			),
		)
		menu.add(
			eventWriteMenuItem(
				_("Copy"),
				imageName="edit-copy.svg",
				func=self.dialog.ops.copyEventFromMenu(path),
			),
		)
		# --
		if isinstance(group, EventTrash):
			menu.add(gtk.SeparatorMenuItem())
			menu.add(
				eventWriteMenuItem(
					_("Delete", ctx="event manager"),
					imageName="edit-delete.svg",
					func=self.dialog.ops.deleteEventFromTrash(path),
				),
			)
		else:
			pasteItem = eventWriteMenuItem(
				_("Paste"),
				imageName="edit-paste.svg",
				func=self.dialog.ops.pasteEventFromMenu(path),
			)
			menu.add(pasteItem)
			pasteItem.set_sensitive(self.dialog.ops.canPasteToGroup(group))
			# --
			menu.add(gtk.SeparatorMenuItem())
			menu.add(
				eventWriteMenuItem(
					_("Move to {title}").format(title=ev.trash.title),
					imageName=ev.trash.getIconRel(),
					func=self.dialog.ops.moveEventToTrashFromMenu(path),
				),
			)

	def genRightClickMenu(self, path: list[int]) -> gtk.Menu | None:
		# and Select _All menu item
		# log.debug(len(obj_list))
		menu = Menu()
		if len(path) == 2:
			if self.dialog.tree.isArchivedGroupRow(path):
				self.archivedGroupAddRightClickMenuItems(menu, path)
				menu.show_all()
				return menu
			group, event = self.dialog.tree.getEventAndParentByPath(path)
			self.eventAddRightClickMenuItems(menu, path, group, event)
			menu.show_all()
			return menu

		assert len(path) == 1

		groupId = self.dialog.tree.getRowId(self.dialog.tree.iterFromPath(path))
		if groupId == -1:
			self.trashAddRightClickMenuItems(menu, path, ev.trash)
			menu.show_all()
			return menu
		if groupId == archivedGroupsRowId:
			return None

		group = ev.groups[groupId]
		self.groupAddRightClickMenuItems(menu, path, group)
		menu.show_all()
		return menu

	def openRightClickMenu(
		self,
		path: list[int],
		etime: int | None = None,
	) -> None:
		menu = self.genRightClickMenu(path)
		if not menu:
			return
		if etime is None:
			etime = gtk.get_current_event_time()
		menu.popup(None, None, None, None, 3, etime)

	def menuKeyPressOnPath(self, path: list[int], gevent: gdk.EventKey) -> None:
		menu = self.genRightClickMenu(path)
		if not menu:
			return
		win = self.dialog.w.get_window()
		assert win is not None
		rect = self.dialog.tree.getCellArea(
			gtk.TreePath.new_from_indices(path),
			self.dialog.tree.getColumn(1),
		)
		x = rect.x
		if rtl:
			x -= get_menu_width(menu) + 40
		else:
			x += 40
		dcord = self.dialog.tree.translateCoordinates(
			self.dialog.w,
			x,
			rect.y + 2 * rect.height,
		)
		assert dcord is not None
		dx, dy = dcord
		_foo, wx, wy = win.get_origin()
		menu.popup(
			None,
			None,
			lambda *_args: (
				wx + dx,
				wy + dy,
				True,
			),
			None,
			3,
			gevent.time,
		)
