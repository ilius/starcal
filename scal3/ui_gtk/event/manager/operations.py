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

from copy import copy
from typing import TYPE_CHECKING

from scal3 import logger, ui
from scal3.event_lib import ev
from scal3.event_lib.trash import EventTrash
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk
from scal3.ui_gtk.event import common, setActionFuncs
from scal3.ui_gtk.event.editor import addNewEvent
from scal3.ui_gtk.event.export import SingleGroupExportDialog
from scal3.ui_gtk.event.group_op import GroupConvertCalTypeDialog, GroupSortDialog
from scal3.ui_gtk.event.manager.conf import archivedGroupsRowId
from scal3.ui_gtk.event.trash import TrashEditorDialog
from scal3.ui_gtk.event.utils import (
	checkEventsReadOnly,
	confirmEventTrash,
)
from scal3.ui_gtk.utils import (
	confirm,
	showError,
	widgetActionCallback,
)

if TYPE_CHECKING:
	from gi.repository import GObject

	from scal3.event_lib.pytypes import (
		AccountType,
		EventGroupType,
		EventType,
	)
	from scal3.ui_gtk.event.bulk_edit import EventsBulkEditDialog
	from scal3.ui_gtk.event.manager.dialog import EventManagerDialog

log = logger.get()


class EventOps:
	"""Group and event operations performed from the Event Manager."""

	def __init__(self, dialog: EventManagerDialog) -> None:
		self.dialog = dialog

	def canPasteToGroup(self, group: EventGroupType) -> bool:
		if self.dialog.toPasteEvent is None:
			return False
		if group.id in ev.archivedGroups.idList:
			return False
		if not group.acceptsEventTypes:  # noqa: SIM103
			return False
		# FIXME: check event type here?
		return True

	def checkEventToAdd(
		self,
		group: EventGroupType,
		event: EventType,
	) -> None:
		if not group.checkEventToAdd(event):
			msg = _(
				'Group type "{groupType}" can not contain event type "{eventType}"',
			).format(
				groupType=group.desc,
				eventType=event.desc,
			)
			showError(msg, transient_for=self.dialog.dialog)
			raise RuntimeError("Invalid event type for this group")

	def insertNewGroup(self, groupIndex: int) -> None:
		from scal3.ui_gtk.event.group.editor import GroupEditorDialog

		group = GroupEditorDialog(transient_for=self.dialog.dialog).run2()
		if group is None:
			return
		ev.groups.insert(groupIndex, group)
		ev.groups.save()
		assert group.id is not None
		self.dialog.tree.insertGroup(groupIndex, group)
		self.onGroupModify(group)
		self.dialog.tree.markGroupLoaded(group.id)

	def addGroupBeforeSelection(self, _w: gtk.Widget | None = None) -> None:
		path = self.dialog.tree.getSelectedPath()
		if path is None:
			groupIndex = len(ev.groups)
		else:
			if not isinstance(path, list):
				raise RuntimeError(f"invalid {path = }")
			groupIndex = min(len(ev.groups), path[0])
		self.insertNewGroup(groupIndex)

	def duplicateGroup(self, path: list[int]) -> None:
		if not (isinstance(path, list) and len(path) == 1):
			raise RuntimeError(f"invalid {path = }")
		index = path[0]
		group = self.dialog.tree.getGroupByPath(path)
		newGroup = copy(group)
		ui.duplicateGroupTitle(newGroup)
		newGroup.afterModify()
		newGroup.save()
		assert newGroup.id is not None
		ev.groups.insert(index + 1, newGroup)
		ev.groups.save()
		self.dialog.tree.insertGroup(index + 1, newGroup)

	def duplicateGroupWithEvents(self, path: list[int]) -> None:
		if not (isinstance(path, list) and len(path) == 1):
			raise RuntimeError(f"invalid {path = }")
		index = path[0]
		group = self.dialog.tree.getGroupByPath(path)
		newGroup = group.deepCopy()
		ui.duplicateGroupTitle(newGroup)
		newGroup.save()
		ev.groups.insert(index + 1, newGroup)
		ev.groups.save()
		assert newGroup.id is not None
		newGroupIter = self.dialog.tree.insertGroup(index + 1, newGroup)
		for event in newGroup:
			self.dialog.tree.appendEventRow(newGroupIter, event)
		self.dialog.tree.markGroupLoaded(newGroup.id)

	@widgetActionCallback
	def syncGroupFromMenu(
		self,
		path: list[int],
		account: AccountType,
	) -> None:
		if not (isinstance(path, list) and len(path) == 1):
			raise RuntimeError(f"invalid {path = }")

		group = self.dialog.tree.getGroupByPath(path)
		if not group.remoteIds:
			return
		assert group.id is not None
		_aid, remoteGid = group.remoteIds
		# account.showError is only used in google account
		account.showError = showError  # type: ignore[attr-defined]
		while gtk.events_pending():
			gtk.main_iteration_do(False)
		error = self.dialog.dialog.waitingDo(account.sync, group, remoteGid)
		if error:
			log.error(error)
		self.dialog.tree.reloadGroupEvents(group.id)

	@widgetActionCallback
	def duplicateGroupFromMenu(self, path: list[int]) -> None:
		self.duplicateGroup(path)

	@widgetActionCallback
	def duplicateGroupWithEventsFromMenu(
		self,
		path: list[int],
	) -> None:
		self.duplicateGroupWithEvents(path)

	def duplicateSelectedObj(self, _obj: GObject.Object) -> None:
		path = self.dialog.tree.getSelectedPath()
		if not path:
			return
		if len(path) == 1:
			self.duplicateGroup(path)
		elif len(path) == 2:  # FIXME
			if self.dialog.tree.isArchivedGroupRow(path):
				return
			self.dialog.toPasteEvent = (self.dialog.tree.iterFromPath(path), False)
			self.pasteEventToPath(path)

	def editGroupByPath(self, path: list[int]) -> None:
		from scal3.ui_gtk.event.group.editor import GroupEditorDialog

		checkEventsReadOnly()  # FIXME
		group = self.dialog.tree.getGroupByPath(path)
		if isinstance(group, EventTrash):
			self.editTrash()
			return

		if group.isReadOnly():
			msg = _(
				'Event group "{groupTitle}" is synchronizing and read-only',
			).format(groupTitle=group.title)
			showError(msg, transient_for=self.dialog.dialog)
			return

		groupNew = GroupEditorDialog(group, transient_for=self.dialog.dialog).run2()
		if groupNew is None:
			return
		self.dialog.tree.setRowValues(
			self.dialog.tree.iterFromPath(path),
			self.dialog.tree.getGroupRow(groupNew),
		)
		self.onGroupModify(groupNew)
		ui.eventUpdateQueue.put("eg", groupNew, self.dialog)

	@widgetActionCallback
	def editGroupFromMenu(self, path: list[int]) -> None:
		self.editGroupByPath(path)

	def _do_deleteGroup(self, path: list[int], group: EventGroupType) -> None:
		self.dialog.tree.addGroupEventsToTrash(group)
		if group.id in ev.archivedGroups.idList:
			ev.groups.moveArchivedToTrash(group, ev.trash)
		else:
			ev.groups.moveToTrash(group, ev.trash)
		ui.eventUpdateQueue.put("-g", group, self.dialog)
		self.dialog.tree.removeRow(path)

	def deleteGroup(self, path: list[int]) -> None:
		if not (
			isinstance(path, list)
			and (len(path) == 1 or self.dialog.tree.isArchivedGroupRow(path))
		):
			raise RuntimeError(f"invalid {path = }")
		group = self.dialog.tree.getGroupByPath(path)
		eventCount = len(group)
		if eventCount > 0 and not confirm(
			_(
				'Press Confirm if you want to delete group "{groupTitle}" '
				"and move its {eventCount} events to {trashTitle}",
			).format(
				groupTitle=group.title,
				eventCount=_(eventCount),
				trashTitle=ev.trash.title,
			),
			transient_for=self.dialog.dialog,
		):
			return
		self.dialog.dialog.waitingDo(self._do_deleteGroup, path, group)

	@widgetActionCallback
	def deleteGroupFromMenu(self, path: list[int]) -> None:
		self.deleteGroup(path)

	def _do_archiveGroup(
		self,
		_path: list[int],
		group: EventGroupType,
	) -> None:
		assert group.id is not None
		groupIter = self.dialog.tree.getGroupIter(group.id)
		assert self.dialog.tree.getRowId(groupIter) == group.id
		self.dialog.tree.removeIterChildren(groupIter)
		self.dialog.tree.unmarkGroupLoaded(group.id)
		self.dialog.tree.removeIter(groupIter)
		self.dialog.tree.removeGroupIter(group.id)
		ev.groups.archiveGroup(group)
		self.dialog.tree.appendArchivedGroupTree(group)
		self.dialog.statusbar.cursorChanged()
		ui.eventUpdateQueue.put("r", group, self.dialog)

	@widgetActionCallback
	def archiveGroupFromMenu(self, path: list[int]) -> None:
		if not (isinstance(path, list) and len(path) == 1):
			raise RuntimeError(f"invalid {path = }")
		group = self.dialog.tree.getGroupByPath(path)
		self.dialog.dialog.waitingDo(self._do_archiveGroup, path, group)

	def _do_unarchiveGroup(
		self,
		_path: list[int],
		group: EventGroupType,
	) -> None:
		assert group.id is not None
		groupIter = self.dialog.tree.getGroupIter(group.id)
		assert self.dialog.tree.getRowId(groupIter) == group.id
		self.dialog.tree.removeIter(groupIter)
		self.dialog.tree.removeGroupIter(group.id)
		ev.groups.unarchiveGroup(group)
		self.dialog.tree.appendGroupTree(group)
		self.dialog.statusbar.cursorChanged()
		ui.eventUpdateQueue.put("r", group, self.dialog)

	@widgetActionCallback
	def unarchiveGroupFromMenu(self, path: list[int]) -> None:
		if not (isinstance(path, list) and len(path) == 2):
			raise RuntimeError(f"invalid {path = }")
		assert self.dialog.tree.isArchivedGroupRow(path)
		groupId = self.dialog.tree.getRowId(self.dialog.tree.iterFromPath(path))
		group = ev.archivedGroups[groupId]
		self.dialog.dialog.waitingDo(self._do_unarchiveGroup, path, group)

	@widgetActionCallback
	def addEventToGroupFromMenu(
		self,
		path: list[int],
		group: EventGroupType,
		eventType: str,
		title: str,
	) -> None:
		event = addNewEvent(
			group,
			eventType,
			title=title,
			transient_for=self.dialog.dialog,
		)
		if event is None:
			return
		ui.eventUpdateQueue.put("+", event, self.dialog)
		groupIter = self.dialog.tree.iterFromPath(path)
		self.dialog.tree.addNewEventRow(group, groupIter, event)
		self.dialog.statusbar.cursorChanged()

	@widgetActionCallback
	def addGenericEventToGroupFromMenu(
		self,
		path: list[int],
		group: EventGroupType,
	) -> None:
		event = addNewEvent(
			group,
			group.acceptsEventTypes[0],
			typeChangable=True,
			title=_("Add Event"),
			transient_for=self.dialog.dialog,
		)
		if event is None:
			return
		ui.eventUpdateQueue.put("+", event, self.dialog)
		groupIter = self.dialog.tree.iterFromPath(path)
		self.dialog.tree.addNewEventRow(group, groupIter, event)
		self.dialog.statusbar.cursorChanged()

	def editEventByPath(self, path: list[int]) -> None:
		from scal3.ui_gtk.event.editor import EventEditorDialog

		event = self.dialog.tree.getEventByPath(path)
		eventNew = EventEditorDialog(
			event,
			title=_("Edit ") + event.desc,
			transient_for=self.dialog.dialog,
		).run2()
		if eventNew is None:
			return
		ui.eventUpdateQueue.put("e", eventNew, self.dialog)
		self.dialog.tree.updateEventRow(eventNew)

	@widgetActionCallback
	def editEventFromMenu(self, path: list[int]) -> None:
		self.editEventByPath(path)

	@widgetActionCallback
	def moveEventToPathFromMenu(
		self,
		path: list[int],
		targetPath: list[int],
	) -> None:
		self.dialog.toPasteEvent = (self.dialog.tree.iterFromPath(path), True)
		self.pasteEventToPath(targetPath, False)

	def moveEventToTrashByPath(self, path: list[int]) -> None:
		group, event = self.dialog.tree.getEventAndGroupByPath(path)
		if not confirmEventTrash(event, transient_for=self.dialog.dialog):
			return
		ui.moveEventToTrash(group, event, self.dialog)
		self.dialog.tree.removeRow(path)
		self.dialog.tree.addEventRowToTrash(event)

	@widgetActionCallback
	def moveEventToTrashFromMenu(self, path: list[int]) -> None:
		self.moveEventToTrashByPath(path)

	def moveSelectionToTrash(self) -> None:
		path = self.dialog.tree.getSelectedPath()
		if not path:
			return
		if len(path) == 1:
			if self.dialog.tree.isArchivedGroupsNode(path):
				return
			self.deleteGroup(path)
		elif len(path) == 2:
			if self.dialog.tree.isArchivedGroupRow(path):
				return
			self.moveEventToTrashByPath(path)

	@widgetActionCallback
	def deleteEventFromTrash(self, path: list[int]) -> None:
		event = self.dialog.tree.getEventByPath(path)
		assert event.id is not None
		ev.trash.delete(event.id)  # trash == ev.trash
		ev.trash.save()
		self.dialog.tree.removeRow(path)

		# no need to send to ui.eventUpdateQueue right now
		# since events in trash (or their occurrences) are not displayed
		# outside Event Manager

	def emptyTrash(self, _w: gtk.Widget) -> None:
		errors = ev.trash.empty()
		self.dialog.tree.clearTrashRows()
		if errors:
			msg = (
				_("Could not delete some events:")
				+ "\n"
				+ "\n".join(f"ID {eid}: {errText}" for eid, errText in errors.items())
			)
			showError(msg, transient_for=self.dialog.dialog)
		self.dialog.statusbar.cursorChanged()

	def editTrashFromMenu(self, _w: gtk.Widget) -> None:
		self.editTrash()

	def editTrash(self) -> None:
		TrashEditorDialog(transient_for=self.dialog.dialog).run()
		self.dialog.tree.refreshTrashRow()
		# TODO: perhaps should put on eventUpdateQueue
		# ui.eventUpdateQueue.put("et", ev.trash, self)
		# as a UI improvement, in case icon of title is changed

	def moveUp(self, path: list[int]) -> None:
		srcIter = self.dialog.tree.iterFromPath(path)
		if not isinstance(path, list):
			raise TypeError(f"invalid {path = }")
		if len(path) == 1:
			if path[0] == 0:
				return
			if self.dialog.tree.getRowId(srcIter) in {-1, archivedGroupsRowId}:
				return
			tarIter = self.dialog.tree.iterFromPath([path[0] - 1])
			self.dialog.tree.moveBefore(srcIter, tarIter)
			ev.groups.moveUp(path[0])
			ev.groups.save()
			# do we need to put on ui.eventUpdateQueue?
		elif len(path) == 2:
			if self.dialog.tree.isArchivedGroupRow(path):
				return
			parentObj, event = self.dialog.tree.getEventAndParentByPath(path)
			parentIndex, eventIndex = path
			if eventIndex > 0:
				tarIter = self.dialog.tree.iterFromPath([parentIndex, eventIndex - 1])
				self.dialog.tree.moveBefore(srcIter, tarIter)
				# ^ or use self.treeModel.swap FIXME
				parentObj.moveUp(eventIndex)
				parentObj.save()
			else:
				# move event to end of previous group
				if parentIndex < 1:
					return
				newParentIter = self.dialog.tree.iterFromPath([parentIndex - 1])
				newParentId = self.dialog.tree.getRowId(newParentIter)
				if newParentId == -1:  # could not be!
					return
				newGroup = ev.groups[newParentId]
				self.checkEventToAdd(newGroup, event)
				self.dialog.tree.removeIter(srcIter)
				self.dialog.tree.appendEventRow(newParentIter, event)
				# ---
				parentObj.remove(event)
				parentObj.save()
				newGroup.append(event)
				newGroup.save()
			ui.eventUpdateQueue.put("r", parentObj, self.dialog)
		else:
			raise ValueError(f"invalid tree path {path}")
		newPath = self.dialog.tree.getPath(srcIter)
		if len(path) == 2:
			self.dialog.tree.expandToPath(newPath)
		self.dialog.tree.setCursorPath(newPath)
		self.dialog.tree.scroll_to_cell(newPath)

	def moveDown(self, path: list[int]) -> None:
		if not isinstance(path, list):
			raise TypeError(f"invalid {path = }")
		srcIter = self.dialog.tree.iterFromPath(path)
		if len(path) == 1:
			if self.dialog.tree.getRowId(srcIter) in {-1, archivedGroupsRowId}:
				return
			tarIter = self.dialog.tree.iterFromPath([path[0] + 1])
			if self.dialog.tree.getRowId(tarIter) in {-1, archivedGroupsRowId}:
				return
			self.dialog.tree.moveAfter(srcIter, tarIter)
			# or use self.treeModel.swap FIXME
			ev.groups.moveDown(path[0])
			ev.groups.save()
			# do we need to put on ui.eventUpdateQueue?
		elif len(path) == 2:
			if self.dialog.tree.isArchivedGroupRow(path):
				return
			parentObj, event = self.dialog.tree.getEventAndParentByPath(path)
			parentLen = len(parentObj)
			parentIndex, eventIndex = path
			if eventIndex < parentLen - 1:
				tarIter = self.dialog.tree.iterFromPath(
					[
						parentIndex,
						eventIndex + 1,
					],
				)
				self.dialog.tree.moveAfter(srcIter, tarIter)
				parentObj.moveDown(eventIndex)
				parentObj.save()
			else:
				# move event to top of next group
				if isinstance(parentObj, EventTrash):
					return
				newParentIter = self.dialog.tree.iterFromPath([parentIndex + 1])
				newParentId = self.dialog.tree.getRowId(newParentIter)
				if newParentId <= 0:
					return
				newGroup = ev.groups[newParentId]
				self.checkEventToAdd(newGroup, event)
				self.dialog.tree.removeIter(srcIter)
				srcIter = self.dialog.tree.insertEventRow(newParentIter, 0, event)
				# ---
				parentObj.remove(event)
				parentObj.save()
				newGroup.insert(0, event)
				newGroup.save()
			ui.eventUpdateQueue.put("r", parentObj, self.dialog)
		else:
			raise RuntimeError(f"invalid tree path {path}")
		newPath = self.dialog.tree.getPath(srcIter)
		if len(path) == 2:
			self.dialog.tree.expandToPath(newPath)
		self.dialog.tree.setCursorPath(newPath)
		self.dialog.tree.scroll_to_cell(newPath)

	def moveUpByButton(self, _obj: GObject.Object) -> None:
		path = self.dialog.tree.getSelectedPath()
		if not path:
			return
		self.moveUp(path)

	def moveDownByButton(self, _obj: GObject.Object) -> None:
		path = self.dialog.tree.getSelectedPath()
		if not path:
			return
		self.moveDown(path)

	def groupExportFromMenu(
		self,
		_w: gtk.Widget,
		group: EventGroupType,
	) -> None:
		SingleGroupExportDialog(group, transient_for=self.dialog.dialog).run()

	@widgetActionCallback
	def groupSortFromMenu(self, path: list[int]) -> None:
		if not (isinstance(path, list) and len(path) == 1):
			raise RuntimeError(f"invalid {path = }")
		group = self.dialog.tree.getGroupByPath(path)
		if not GroupSortDialog(group, transient_for=self.dialog.dialog).run2():
			return
		if not self.dialog.tree.isGroupLoaded(group.id) and group.name != "trash":
			return
		groupIter = self.dialog.tree.iterFromPath(path)
		pathObj = gtk.TreePath.new_from_indices(path)
		expanded = self.dialog.tree.rowExpanded(pathObj)
		self.dialog.tree.removeIterChildren(groupIter)
		for event in group:
			self.dialog.tree.appendEventRow(groupIter, event)
		if expanded:
			self.dialog.tree.expandRow(pathObj)

	@widgetActionCallback
	def groupConvertCalTypeFromMenu(
		self,
		group: EventGroupType,
	) -> None:
		if GroupConvertCalTypeDialog(group, transient_for=self.dialog.dialog).perform():
			ui.eventUpdateQueue.put("r", group, self.dialog)

	def _do_groupConvertTo(
		self,
		group: EventGroupType,
		newGroupType: str,
	) -> None:
		idsCount = len(group.idList)
		newGroup = ev.groups.convertGroupTo(group, newGroupType)
		assert newGroup.id is not None
		# FIXME: reload its events in tree?
		# summary and description have been not changed!
		idsCount2 = len(newGroup.idList)
		if idsCount2 != idsCount:
			self.dialog.tree.reloadGroupEvents(newGroup.id)
		self.dialog.statusbar.cursorChanged()
		ui.eventUpdateQueue.put("eg", newGroup, self.dialog)

	@widgetActionCallback
	def groupConvertToFromMenu(
		self,
		group: EventGroupType,
		newGroupType: str,
	) -> None:
		self.dialog.dialog.waitingDo(self._do_groupConvertTo, group, newGroupType)

	def _do_groupBulkEdit(
		self,
		dialog: EventsBulkEditDialog,
		group: EventGroupType,
		path: list[int],
	) -> None:
		pathObj = gtk.TreePath.new_from_indices(path)
		expanded = self.dialog.tree.rowExpanded(pathObj)
		dialog.doAction()
		dialog.destroy()
		self.dialog.tree.removePath(pathObj)
		self.dialog.tree.insertGroupTree(path[0], group)
		if expanded:
			self.dialog.tree.expandRow(pathObj)
		self.dialog.tree.setCursorPath(pathObj)
		ui.eventUpdateQueue.put("r", group, self.dialog)

	@widgetActionCallback
	def groupBulkEditFromMenu(
		self,
		group: EventGroupType,
		path: list[int],
	) -> None:
		from scal3.ui_gtk.event.bulk_edit import EventsBulkEditDialog

		dialog = EventsBulkEditDialog(group, transient_for=self.dialog.dialog)
		if dialog.run() == gtk.ResponseType.OK:
			self.dialog.dialog.waitingDo(self._do_groupBulkEdit, dialog, group, path)

	@widgetActionCallback
	def onGroupActionClick(
		self,
		group: EventGroupType,
		actionFuncName: str,
	) -> None:
		actionFunc = getattr(group, actionFuncName, None)
		if actionFunc is None:
			setActionFuncs(group)
			actionFunc = getattr(group, actionFuncName)

		def newActionFunc() -> None:
			actionFunc(parentWin=self.dialog.dialog)

		self.dialog.dialog.waitingDo(newActionFunc)

	def _do_onGroupModify(self, group: EventGroupType) -> None:
		group.afterModify()
		group.save()  # FIXME
		assert group.id is not None
		try:
			if group.name == "universityTerm":  # FIXME
				groupIter = self.dialog.tree.getGroupIter(group.id)
				n = self.dialog.tree.iterChildrenCount(groupIter)
				for i in range(n):
					eventIter = self.dialog.tree.iterNthChild(groupIter, i)
					assert eventIter is not None
					eid = self.dialog.tree.getRowId(eventIter)
					self.dialog.tree.setValue(
						eventIter,
						self.dialog.tree.summaryColIndex,
						group[eid].autoSummary,
					)
		except Exception:
			log.exception("")

	def onGroupModify(self, group: EventGroupType) -> None:
		self.dialog.dialog.waitingDo(self._do_onGroupModify, group)

	def setGroupEnable(
		self,
		enable: bool,
		group: EventGroupType,
		path: list[int] | None,
	) -> None:
		assert group.id is not None
		if path is None:
			groupIter = self.dialog.tree.getGroupIter(group.id)
		else:
			groupIter = self.dialog.tree.iterFromPath(path)
		group.enable = enable
		self.dialog.tree.setValue(groupIter, 2, common.getTreeGroupPixbuf(group))
		ev.groups.save()
		if (
			group.enable
			and self.dialog.tree.iterChildrenCount(groupIter) == 0
			and len(group) > 0
		):
			for event in group:
				self.dialog.tree.appendEventRow(groupIter, event)
			self.dialog.tree.markGroupLoaded(group.id)
		self.onGroupModify(group)

	def onEnableAllClick(self, _menuItem: gtk.MenuItem) -> None:
		for group in ev.groups:
			self.setGroupEnable(True, group, None)

	def onDisableAllClick(self, _menuItem: gtk.MenuItem) -> None:
		for group in ev.groups:
			self.setGroupEnable(False, group, None)

	def toggleEnableGroup(self, group: EventGroupType, path: list[int]) -> bool:
		col = self.dialog.tree.pixbufCol
		cell = col.get_cells()[0]
		try:
			cell.get_property("pixbuf")
		except Exception:
			return False
		enable = not group.enable
		self.setGroupEnable(enable, group, path)
		ui.eventUpdateQueue.put("eg", group, self.dialog)
		return True

	@widgetActionCallback
	def cutEventFromMenu(self, path: list[int]) -> None:
		self.dialog.toPasteEvent = (self.dialog.tree.iterFromPath(path), True)

	@widgetActionCallback
	def copyEventFromMenu(self, path: list[int]) -> None:
		self.dialog.toPasteEvent = (self.dialog.tree.iterFromPath(path), False)

	@widgetActionCallback
	def pasteEventFromMenu(self, targetPath: list[int]) -> None:
		self.pasteEventToPath(targetPath)

	def pasteEventToPathInner(
		self,
		srcIter: gtk.TreeIter,
		move: bool,
		targetPath: list[int],
	) -> gtk.TreeIter:
		srcPathObj = self.dialog.tree.getPath(srcIter)
		srcPath = srcPathObj.get_indices()
		srcGroup, srcEvent = self.dialog.tree.getEventAndGroupByPath(srcPath)
		tarGroup = self.dialog.tree.getGroupByPath(targetPath)
		if tarGroup.id in ev.archivedGroups.idList:
			raise RuntimeError(f"can not paste event into archived group {tarGroup.id}")
		self.checkEventToAdd(tarGroup, srcEvent)
		if len(targetPath) == 1:
			tarGroupIter = self.dialog.tree.iterFromPath(targetPath)
			tarEventIter = None
			tarEventIndex = len(tarGroup)
		elif len(targetPath) == 2:
			tarGroupIter = self.dialog.tree.iterFromPath(targetPath[:1])
			tarEventIter = self.dialog.tree.iterFromPath(targetPath)
			tarEventIndex = targetPath[1]
		# ----
		if move:
			srcGroup.remove(srcEvent)
			srcGroup.save()
			tarGroup.insert(tarEventIndex, srcEvent)
			tarGroup.save()
			self.dialog.tree.removePath(srcPathObj)
			newEvent = srcEvent
			ui.eventUpdateQueue.put("r", srcGroup, self.dialog)
		else:
			newEvent = copy(srcEvent)
			newEvent.save()
			tarGroup.insert(tarEventIndex, newEvent)
			tarGroup.save()
		ui.eventUpdateQueue.put("+", newEvent, self.dialog)
		# although we insert the new event (not append) to group
		# it should not make any difference, since only occurrences (and not
		# events) are displayed outside Event Manager
		# ----
		if tarEventIter:
			newEventIter = self.dialog.tree.insertEventRowAfter(
				tarGroupIter,
				tarEventIter,
				newEvent,
			)
		else:
			newEventIter = self.dialog.tree.appendEventRow(tarGroupIter, newEvent)
		return newEventIter

	def pasteEventToPath(
		self,
		targetPath: list[int],
		doScroll: bool = True,
	) -> None:
		if not self.dialog.toPasteEvent:
			return
		srcIter, move = self.dialog.toPasteEvent
		newEventIter = self.pasteEventToPathInner(srcIter, move, targetPath)
		if doScroll:
			self.dialog.tree.setCursorPath(self.dialog.tree.getPath(newEventIter))
		self.dialog.toPasteEvent = None
