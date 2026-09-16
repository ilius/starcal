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

from contextlib import suppress
from typing import TYPE_CHECKING, Any

from scal3 import cal_types, core, logger, ui
from scal3.event_lib import ev
from scal3.event_lib.event_base import Event
from scal3.event_lib.group import EventGroup
from scal3.event_lib.trash import EventTrash
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk
from scal3.ui_gtk.event.utils import confirmEventsTrash

if TYPE_CHECKING:
	from collections.abc import Iterable

	from scal3.event_lib.event_container import EventContainer
	from scal3.event_lib.pytypes import EventContainerType
	from scal3.ui_gtk.event.bulk_edit import EventsBulkEditDialog
	from scal3.ui_gtk.event.manager.dialog import EventManagerDialog

log = logger.get()


class MultiSelect:
	"""Multi-select bar and its selection state."""

	def __init__(self, dialog: EventManagerDialog) -> None:
		self.dialog = dialog
		self.enabled = False
		self.pathDict: dict[int, dict[int, object]] = {}
		self.toPaste: tuple[bool, list[gtk.TreeIter]] | None = None

	def treeviewToggleStatus(
		self,
		_column: Any,
		cell: gtk.CellRendererToggle,
		model: gtk.TreeModel,
		gIter: gtk.TreeIter,
		_userData: Any,
	) -> None:
		if not self.enabled:
			return

		path = model.get_path(gIter).get_indices()
		value = model.get_value(gIter, 0)
		if len(path) == 2:
			cell.set_property("inconsistent", False)
			cell.set_active(value)
			return

		groupIndex = path[0]
		groupId = self.dialog.tree.getRowId(gIter)
		if groupId <= 0:  # trash row or Archived Groups node
			cell.set_property("inconsistent", False)
			cell.set_active(value)
			return
		group = self.dialog.tree.getGroupByPath(path)
		assert isinstance(group, EventGroup), f"{group=}"
		if groupIndex not in self.pathDict:
			cell.set_property("inconsistent", False)
			cell.set_active(value)
			return

		# we know len(self.pathDict[groupIndex]) > 0

		if len(self.pathDict[groupIndex]) == len(group):
			cell.set_property("inconsistent", False)
			cell.set_active(True)
			return

		cell.set_property("inconsistent", True)
		cell.set_active(value)

	def setEnable(self, enable: bool) -> None:
		self.dialog.multiSelectHBox.set_visible(enable)
		self.dialog.tree.multiSelectColumn.set_visible(enable)
		self.dialog.editItem.set_sensitive(not enable)
		self.dialog.fileItem.set_sensitive(not enable)
		self.dialog.toolbar.w.set_sensitive(not enable)
		for item in self.dialog.multiSelectItemsOther:
			item.set_sensitive(enable)
		self.enabled = enable

	def toggle(self, menuItem: gtk.CheckMenuItem) -> None:
		enable = menuItem.get_active()
		self.setEnable(enable)

	def shiftUpDownPress(self, isDown: bool) -> None:
		path = self.dialog.tree.getSelectedPath()
		if path is None:
			return
		if len(path) == 1:
			return  # TODO

		if len(path) != 2:
			raise RuntimeError(f"unexpected {path=}")

		groupIndex, eventIndex = path

		self.cbSetEvent(groupIndex, eventIndex, True)

		if eventIndex == 0 and not isDown:
			return

		plus = 1 if isDown else -1
		nextPath = gtk.TreePath.new_from_indices([groupIndex, eventIndex + plus])

		try:
			self.dialog.tree.getIter(nextPath)
		except ValueError:
			# ValueError: invalid tree path '0:4'
			return

		self.cbSetEvent(groupIndex, eventIndex + plus, True)
		self.dialog.tree.setCursorPath(nextPath)
		self.dialog.tree.scroll_to_cell(nextPath)

	def shiftButtonPress(
		self,
		path: list[int],
	) -> None:
		groupIndex, eventIndex = path
		if groupIndex not in self.pathDict:
			return
		lastEventIndex = next(reversed(self.pathDict[groupIndex]))
		if eventIndex == lastEventIndex:
			return
		if eventIndex > lastEventIndex:
			evIndexRange = range(lastEventIndex + 1, eventIndex + 1)
		else:
			evIndexRange = range(eventIndex, lastEventIndex)
		for evIndex in evIndexRange:
			self.cbSetEvent(groupIndex, evIndex, True)

	def labelUpdate(self) -> None:
		self.dialog.multiSelectLabel.set_label(
			_("{count} events selected").format(
				count=_(
					sum(len(eventIndexes) for eventIndexes in self.pathDict.values()),
				),
			),
		)

	def treeviewToggleSelected(self) -> None:
		path = self.dialog.tree.getSelectedPath()
		if path is None:
			return
		self.treeviewTogglePath(path)

	def treeviewToggle(
		self,
		_cell: gtk.CellRendererToggle,
		pathStr: str,
	) -> None:
		path = gtk.TreePath.new_from_string(pathStr).get_indices()
		self.treeviewTogglePath(path)

	def cbActivate(self, groupIndex: int, eventIndex: int) -> None:
		if groupIndex not in self.pathDict:
			self.pathDict[groupIndex] = {}
		self.pathDict[groupIndex][eventIndex] = None

	def cbSetEvent(
		self,
		groupIndex: int,
		eventIndex: int,
		active: bool,
	) -> None:
		itr = self.dialog.tree.getIter(
			gtk.TreePath.new_from_indices([groupIndex, eventIndex])
		)
		self.dialog.tree.setValue(itr, 0, active)
		if active:
			self.cbActivate(groupIndex, eventIndex)
		elif groupIndex in self.pathDict:
			if eventIndex in self.pathDict[groupIndex]:
				del self.pathDict[groupIndex][eventIndex]
			if not self.pathDict[groupIndex]:
				del self.pathDict[groupIndex]

		parentIter = self.dialog.tree.getIter(str(groupIndex))
		try:
			count = len(self.pathDict[groupIndex])
		except KeyError:
			self.dialog.tree.setValue(parentIter, 0, False)
		else:
			self.dialog.tree.setValue(
				parentIter,
				0,
				count == len(ev.groups[self.dialog.tree.getRowId(parentIter)]),
			)

		self.labelUpdate()

	def cbSetGroup(
		self,
		groupIndex: int,
		eventIndex: int,
		active: bool,
	) -> None:
		if active:
			self.cbActivate(groupIndex, eventIndex)
			return

		if groupIndex in self.pathDict:
			del self.pathDict[groupIndex]

	def treeviewTogglePath(self, path: list[int]) -> None:
		if len(path) not in {1, 2}:
			raise RuntimeError(f"invalid path depth={len(path)}, {path=}")
		if self.dialog.tree.isArchivedGroupsNode(
			path
		) or self.dialog.tree.isArchivedGroupRow(
			path,
		):
			return
		itr = self.dialog.tree.getIter(gtk.TreePath.new_from_indices(path))

		active = not self.dialog.tree.getValue(itr, 0)

		if len(path) == 1:
			self.dialog.tree.setValue(itr, 0, active)
			childIter = self.dialog.tree.iterChildren(itr)
			while childIter is not None:
				isActive = self.dialog.tree.getValue(childIter, 0)
				if isActive == active:
					childIter = self.dialog.tree.iterNext(childIter)
					continue
				self.dialog.tree.setValue(childIter, 0, active)
				groupIndex, eventIndex = tuple(
					self.dialog.tree.getPath(childIter).get_indices()
				)
				self.cbSetGroup(groupIndex, eventIndex, active)
				childIter = self.dialog.tree.iterNext(childIter)
			self.labelUpdate()
			return

		self.cbSetEvent(path[0], path[1], active)

	def copy(self, _w: gtk.Widget | None = None) -> None:
		iterList = list(self.iters())
		self.toPaste = (False, iterList)
		self.dialog.multiSelectPasteButton.set_sensitive(True)

	def cut(self, _w: gtk.Widget | None = None) -> None:
		iterList = list(self.iters())
		self.toPaste = (True, iterList)
		self.dialog.multiSelectPasteButton.set_sensitive(True)

	def paste(self, _w: gtk.Widget | None = None) -> None:
		toPaste = self.toPaste
		if toPaste is None:
			log.error("nothing to paste")
			return

		move, iterList = toPaste
		if not iterList:
			return

		targetPath = self.dialog.tree.getSelectedPath()
		if targetPath is None:
			return
		newEventIter = None

		if len(targetPath) == 2:
			iterList = list(reversed(iterList))
			# so that events are inserted in the same order as they are selected

		for srcIter in iterList:
			iter_ = self.dialog.ops.pasteEventToPathInner(srcIter, move, targetPath)
			if newEventIter is None:
				newEventIter = iter_

		if not move:
			for iter_ in iterList:
				self.dialog.tree.setValue(iter_, 0, False)

		if move:
			msg = _("{count} events successfully moved")
		else:
			msg = _("{count} events successfully copied")
		self.dialog.sbar.push(
			0,
			msg.format(
				count=_(len(iterList)),
			),
		)

		self.operationFinished()
		self.toPaste = None

		if newEventIter:
			self.dialog.tree.setCursorPath(self.dialog.tree.getPath(newEventIter))

	def _doDelete(self, iterList: list[gtk.TreeIter]) -> None:
		saveGroupSet: set[EventContainer] = set()
		ui.eventUpdateQueue.pauseLoop()

		for gIter in iterList:
			path = self.dialog.tree.getPath(gIter).get_indices()
			group, event = self.dialog.tree.getEventAndGroupByPath(path)
			assert event.id is not None
			assert isinstance(event, Event), f"{event=}"

			if isinstance(group, EventTrash):
				group.delete(event.id)  # group == ev.trash
				saveGroupSet.add(group)
				self.dialog.tree.removeIter(gIter)
				continue

			assert isinstance(group, EventGroup), f"{group=}"
			ui.moveEventToTrash(group, event, self.dialog, save=False)
			saveGroupSet.add(group)
			saveGroupSet.add(ev.trash)
			self.dialog.tree.removeIter(gIter)
			self.dialog.tree.addEventRowToTrash(event)

		for groupTmp in saveGroupSet:
			groupTmp.save()

		ui.eventUpdateQueue.resumeLoop()

	def operationFinished(self) -> None:
		for groupIndex in self.pathDict:
			with suppress(ValueError):
				self.dialog.tree.setValue(
					self.dialog.tree.getIter(str(groupIndex)),
					0,
					False,
				)

		self.pathDict = {}
		self.labelUpdate()
		self.dialog.multiSelectPasteButton.set_sensitive(False)

	def delete(self, _w: gtk.Widget | None = None) -> None:
		if not self.pathDict:
			return
		iterList = list(self.iters())

		trashIndex = self.dialog.tree.getTrashIndex()
		if trashIndex in self.pathDict:
			deleteCount = len(self.pathDict[trashIndex])
		else:
			deleteCount = 0

		toTrashCount = len(iterList) - deleteCount

		if not confirmEventsTrash(toTrashCount, deleteCount):
			return

		self.dialog.dialog.waitingDo(self._doDelete, iterList)

		msgs = []
		if toTrashCount:
			msgs.append(
				_("Moved {count} events to {title}").format(
					count=_(toTrashCount),
					title=ev.trash.title,
				),
			)
		if deleteCount:
			msgs.append(
				_("Deleted {count} events from {title}").format(
					count=_(deleteCount),
					title=ev.trash.title,
				),
			)
		self.dialog.sbar.push(0, _(", ").join(msgs))

		self.operationFinished()

	def iters(self) -> Iterable[gtk.TreeIter]:
		for groupIndex, eventIndexes in self.pathDict.items():
			for eventIndex in eventIndexes:
				yield self.dialog.tree.getIter(
					gtk.TreePath.new_from_indices([groupIndex, eventIndex])
				)

	def cancel(self, _w: gtk.Widget | None = None) -> None:
		self.setEnable(False)
		self.dialog.multiSelectItem.set_active(False)
		for gIter in self.iters():
			self.dialog.tree.setValue(gIter, 0, False)
		self.operationFinished()

	def eventIdsDict(self) -> dict[int, list[int]]:
		idsDict = {}
		for groupIndex, eventIndexes in self.pathDict.items():
			groupId = self.dialog.tree.getRowId(
				self.dialog.tree.getIter(str(groupIndex))
			)
			idsDict[groupId] = [
				self.dialog.tree.getRowId(
					self.dialog.tree.getIter(
						gtk.TreePath.new_from_indices([groupIndex, eventIndex])
					)
				)
				for eventIndex in eventIndexes
			]
		return idsDict

	def eventIdsList(self) -> list[tuple[int, int]]:
		idsList = []
		for groupIndex, eventIndexes in self.pathDict.items():
			groupId = self.dialog.tree.getRowId(
				self.dialog.tree.getIter(str(groupIndex))
			)
			idsList += [
				(
					groupId,
					self.dialog.tree.getRowId(
						self.dialog.tree.getIter(
							gtk.TreePath.new_from_indices([groupIndex, eventIndex])
						)
					),
				)
				for eventIndex in eventIndexes
			]
		return idsList

	def bulkEdit(self, _w: gtk.Widget | None = None) -> None:
		from scal3.event_lib.event_container import DummyEventContainer
		from scal3.ui_gtk.event.bulk_edit import EventsBulkEditDialog

		idsDict = self.eventIdsDict()
		container: EventContainerType = DummyEventContainer(ev.groups, idsDict)  # type: ignore[assignment]
		dialog = EventsBulkEditDialog(container, transient_for=self.dialog.dialog)

		if dialog.run() == gtk.ResponseType.OK:
			self.dialog.dialog.waitingDo(self._doBulkEdit, dialog, container)

	def _doBulkEdit(
		self,
		dialog: EventsBulkEditDialog,
		container: EventContainerType,
	) -> None:
		dialog.doAction()
		dialog.destroy()
		for event in container:
			self.dialog.tree.updateEventRow(event)
			ui.eventUpdateQueue.put("e", event, self.dialog)

		self.operationFinished()

	def export(self, _w: gtk.Widget | None = None) -> None:
		from scal3.ui_gtk.event.export import EventListExportDialog

		idsList = self.eventIdsList()
		y, m, d = cal_types.getSysDate(core.GREGORIAN)
		dialog = EventListExportDialog(
			idsList,
			defaultFileName=f"selected-events-{y:04d}-{m:02d}-{d:02d}",
			# groupTitle="",
		)
		dialog.run()
		self.dialog.sbar.push(
			0,
			_("Exporting {count} events finished").format(
				count=_(len(idsList)),
			),
		)
		self.operationFinished()
