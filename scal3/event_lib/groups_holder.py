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

import json

from scal3 import logger

log = logger.get()

from collections import OrderedDict
from contextlib import suppress
from os.path import join, splitext
from typing import TYPE_CHECKING

from scal3 import ics
from scal3.app_info import APP_NAME, VERSION_TAG
from scal3.color_utils import RGB
from scal3.locale_man import tr as _
from scal3.s_object import SObjBinaryModel

from .event_base import eventsDir
from .group import EventGroup, groupsDir
from .groups_import import (
	IMPORT_MODE_SKIP_MODIFIED,
	EventGroupsImportResult,
)
from .holders import ObjectsHolderTextModel
from .objects import iterObjectFiles
from .pytypes import EventGroupType
from .register import classes

if TYPE_CHECKING:
	from typing import Any

	from .trash import EventTrash

__all__ = ["EventGroupsHolder"]


class EventGroupsHolder(ObjectsHolderTextModel[EventGroupType]):
	file = join("event", "group_list.json")

	@classmethod
	def getMainClass(cls) -> type[EventGroupType] | None:
		return classes.group.main

	def __init__(
		self,
		ident: int | None = None,
	) -> None:
		super().__init__()
		self.id = ident
		self.parent = None
		self.idByUuid = {}
		self.trash: EventTrash | None = None
		self.calType = 0  # not used? just for group.parent eligibilty

	def setTrash(self, trash: EventTrash) -> None:
		self.trash = trash

	def create(self, groupName: str) -> EventGroupType:
		group = classes.group.byName[groupName]()
		group.fs = self.fs
		return group

	def delete(self, group: EventGroupType) -> None:
		assert not group.idList  # FIXME
		group.parent = None
		super().delete(group)

	def setList(self, data: list[int]) -> None:
		self.clear()
		if data:
			super().setList(data)
			for group in self:
				assert group.id is not None
				# if TYPE_CHECKING:
				# 	_parent: ParentSObj = self
				group.parent = self
				if group.uuid is None:
					group.save()
					log.info(f"saved group {group.id} with uuid = {group.uuid}")
					assert group.uuid
				self.idByUuid[group.uuid] = group.id
				if group.enable:
					group.updateOccurrence()
		else:
			for name in (
				"noteBook",
				"taskList",
				"group",
			):
				cls = classes.group.byName[name]
				obj = cls()  # FIXME
				obj.fs = self.fs
				obj.setRandomColor()
				obj.setTitle(cls.desc)
				obj.save()
				assert obj.uuid is not None
				assert obj.id is not None
				self.idByUuid[obj.uuid] = obj.id
				self.append(obj)
			self.save()

	def getEnableIds(self) -> list[int]:
		return [group.id or -1 for group in self if group.enable]

	def moveToTrash(
		self,
		group: EventGroupType,
		trash: EventTrash,
	) -> None:
		if trash.addEventsToBeginning:
			trash.idList = group.idList + trash.idList
		else:
			trash.idList += group.idList
		group.idList = []
		self.delete(group)
		self.save()
		trash.save()

	def convertGroupTo(
		self,
		group: EventGroupType,
		newGroupType: str,
	) -> EventGroupType:
		newGroup = group.deepConvertTo(newGroupType)
		newGroup.setId(group.id)
		newGroup.afterModify()
		newGroup.save()
		assert newGroup.id is not None
		self.byId[newGroup.id] = newGroup
		return newGroup
		# and then never use old `group` object

	def exportData(self, gidList: list[int]) -> dict[str, Any]:
		return {
			"info": OrderedDict(
				[
					("appName", APP_NAME),
					("version", VERSION_TAG),
				],
			),
			"groups": [self.byId[gid].exportData() for gid in gidList],
		}

	def eventListExportData(
		self,
		idsList: list[tuple[int, int]],
		groupTitle: str = "",
	) -> dict[str, Any]:
		eventsData = []
		for groupId, eventId in idsList:
			event = self.byId[groupId].getEvent(eventId)
			if event.uuid is None:
				event.save()
			eventData = event.getDictOrdered()
			eventData["modified"] = event.modified
			# eventData["sha1"] = event.lastHash
			with suppress(KeyError):
				del eventData["remoteIds"]  # FIXME
			if not eventData["notifiers"]:
				del eventData["notifiers"]
				del eventData["notifyBefore"]
			eventsData.append(eventData)

		return {
			"info": OrderedDict(
				[
					("appName", APP_NAME),
					("version", VERSION_TAG),
				],
			),
			"groups": [
				OrderedDict(
					[
						("type", "group"),
						("title", groupTitle),
						("events", eventsData),
					],
				),
			],
		}

	def importData(self, data: dict[str, Any]) -> EventGroupsImportResult:
		res = EventGroupsImportResult()
		for gdata in data["groups"]:
			guuid = gdata.get("uuid")
			if guuid:
				gid = self.idByUuid.get(guuid)
				if gid is not None:
					group = self[gid]
					res += group.importData(
						gdata,
						importMode=IMPORT_MODE_SKIP_MODIFIED,
					)
					continue
			group = classes.group.byName[gdata["type"]]()
			group.fs = self.fs
			group.setId()
			assert group.id is not None
			group.importData(gdata, importMode=IMPORT_MODE_SKIP_MODIFIED)
			group.save()
			self.append(group)
			res.newGroupIds.add(group.id)

		self.save()
		return res

	def exportToIcs(self, fpath: str, gidList: list[int]) -> None:
		fp = self.fs.open(fpath, "w")
		fp.write(ics.icsHeader)
		for gid in gidList:
			self[gid].exportToIcsFp(fp)
		fp.write("END:VCALENDAR\n")
		fp.close()

	def checkForOrphans(self) -> EventGroup | None:
		fs = self.fs
		newGroup = EventGroup()
		newGroup.fs = fs
		newGroup.setTitle(_("Orphan Events"))
		newGroup.setColor(RGB(255, 255, 0))
		newGroup.enable = False
		for gid_fname in fs.listdir(groupsDir):
			try:
				gid = int(splitext(gid_fname)[0])
			except ValueError:
				continue
			if gid not in self.idList:
				try:
					fs.removeFile(join(groupsDir, gid_fname))
				except Exception:
					log.exception("")
		# ---------
		myEventIdList: list[int] = []
		for group in self:
			myEventIdList += group.idList
		myEventIdSet: set[int] = set(myEventIdList)
		eventHashSet: set[str] = set()

		for fname in fs.listdir(eventsDir):
			fname_nox, ext = splitext(fname)
			if ext != ".json":
				continue
			try:
				eid = int(fname_nox)
			except ValueError:
				continue
			if eid not in myEventIdSet:
				newGroup.idList.append(eid)

			with fs.open(join(eventsDir, fname)) as fp:
				data = json.loads(fp.read())
			history = data.get("history")
			if history:
				eventHashSet.update(record[1] for record in history)

		# newEventHashList = []
		eventTypeSet = set(classes.event.names)
		for hash_, _fpath in iterObjectFiles(fs):
			if hash_ in eventHashSet:
				continue
			data = SObjBinaryModel.loadBinaryDict(hash_, fs)
			if data.get("type") not in eventTypeSet:
				continue
			# newEventHashList.append(_hash)
			newEvent = newGroup.create(data["type"])
			newEvent.setDict(data)
			newEvent.save()
			newGroup.append(newEvent)

		# log.debug(newEventHashList)

		if newGroup.idList:
			newGroup.save()
			self.append(newGroup)
			self.save()
			return newGroup
		return None
