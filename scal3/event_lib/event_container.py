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

import json
from time import time as now
from typing import TYPE_CHECKING, Protocol, Self

import mytz
from scal3 import core, locale_man, logger
from scal3.cal_types import calTypes
from scal3.locale_man import tr as _
from scal3.s_object import SObj
from scal3.time_utils import getEpochFromJd

from .event_base import Event
from .icon import WithIcon, iconAbsToRelativelnData
from .objects import HistoryEventObjBinaryModel
from .register import classes

if TYPE_CHECKING:
	from collections.abc import Iterator, Sequence
	from datetime import tzinfo
	from typing import Any

	from scal3.event_search_tree import EventSearchTree

	from .pytypes import EventGroupType, EventType


__all__ = ["DummyEventContainer", "EventContainer"]


class DummyEventGroupsHolder(Protocol):
	def __getitem__(self, ident: int) -> EventGroupType: ...


class DummyEventContainer:
	def __init__(
		self,
		groups: DummyEventGroupsHolder,
		idsDict: dict[int, list[int]],
	) -> None:
		self.groups = groups
		self.idsDict = idsDict

	def __len__(self) -> int:
		return sum(len(eventIds) for eventIds in self.idsDict.values())

	def __iter__(self) -> Iterator[EventType]:
		for groupId, eventIdList in self.idsDict.items():
			group = self.groups[groupId]
			for eventId in eventIdList:
				yield group.getEvent(eventId)


class Smallest:
	def __eq__(self, other: object) -> bool:
		return isinstance(other, Smallest)

	def __lt__(self, other: Any) -> bool:
		return not isinstance(other, Smallest)

	def __gt__(self, other: Any) -> bool:
		return False

	def __hash__(self) -> int:
		return hash(Smallest)


smallest = Smallest()


class EventContainer(HistoryEventObjBinaryModel, WithIcon):
	name = ""
	desc = ""
	basicParams: list[str] = [
		"idList",  # FIXME
		"uuid",
	]
	# HistoryEventObjBinaryModel.params is empty
	params: list[str] = [
		"timeZoneEnable",
		"timeZone",
		"icon",
		"title",
		"showFullEventDesc",
		"idList",
		"modified",
		"uuid",
		"addEventsToBeginning",
	]

	acceptsEventTypes: Sequence[str] = (
		"yearly",
		"dailyNote",
		"task",
		"allDayTask",
		"weekly",
		"monthly",
		"lifetime",
		"largeScale",
		"custom",
	)

	sortBys: list[tuple[str, str, bool]] = [
		# name, description, is_type_dependent
		("calType", _("Calendar Type"), False),
		("summary", _("Summary"), False),
		("description", _("Description"), False),
		("icon", _("Icon"), False),
	]
	sortByDefault = "summary"

	def __getitem__(self, key: int) -> EventType:
		if isinstance(key, int):  # eventId
			return self.getEvent(key)
		raise TypeError(
			f"invalid key type for {key!r} given to EventContainer.__getitem__",
		)

	def getTimeZoneStr(self) -> str:
		if self.timeZoneEnable and self.timeZone:
			return self.timeZone
		return ""

	def byIndex(self, index: int) -> EventType:
		return self.getEvent(self.idList[index])

	def __str__(self) -> str:
		return f"{self.__class__.__name__}(title='{self.title}')"

	def __init__(self, title: str = "Untitled") -> None:
		self.fs = core.fs
		self.parent = None
		self.enable = True
		self.timeZoneEnable = False
		self.timeZone = ""
		self.calType = calTypes.primary
		self.idList: list[int] = []
		self.title = title
		self.icon: str | None = None
		self.showFullEventDesc = False
		self.addEventsToBeginning = False
		self.eventTextSep = core.eventTextSep
		self.startJd = 0
		self.endJd = 0
		self.occur: EventSearchTree | None = None
		# ------
		self.uuid = None
		self.modified = now()
		# self.eventsModified = self.modified
		######
		self.notificationEnabled = False

	def getTimeZoneObj(self) -> tzinfo | None:
		if self.timeZoneEnable and self.timeZone:
			tz = mytz.gettz(self.timeZone)
			if tz:
				return tz
		return locale_man.localTz

	def getEpochFromJd(self, jd: int) -> int:
		return getEpochFromJd(jd, tz=self.getTimeZoneObj())

	def getStartEpoch(self) -> int:
		return self.getEpochFromJd(self.startJd)

	def getEndEpoch(self) -> int:
		return self.getEpochFromJd(self.endJd)

	def afterModify(self) -> None:
		self.modified = now()

	def getEvent(self, ident: int) -> EventType:
		if ident not in self.idList:
			raise ValueError(f"{self} does not contain {ident!r}")
		return self._getEvent(ident)

	def _getEvent(self, eid: int) -> EventType:
		eventFile = Event.getFile(eid)
		if not self.fs.isfile(eventFile):
			# self.idList.remove(eid)
			# self.save()  # FIXME
			raise FileNotFoundError(
				f"error while loading event file {eventFile!r}: "
				f"file not found. {eid=}, container={self!r}",
			)
		with self.fs.open(eventFile) as fp:
			data = json.loads(fp.read())
		data["id"] = eid  # FIXME
		lastEpoch, lastHash = self.updateBasicData(
			data,
			eventFile,
			"event",
			self.fs,
		)
		event = classes.event.byName[data["type"]](eid)
		event.fs = self.fs
		event.parent = self
		event.setDict(data)
		event.lastHash = lastHash
		event.modified = lastEpoch
		return event

	def __iter__(self) -> Iterator[EventType]:
		for eid in self.idList:
			try:
				event = self.getEvent(eid)
			except Exception:  # noqa: PERF203
				log.exception("")
			else:
				yield event

	def __len__(self) -> int:
		return len(self.idList)

	def preAdd(self, event: EventType) -> None:
		if event.id in self.idList:
			raise ValueError(f"{self} already contains {event}")
		if event.parent not in {None, self}:
			raise ValueError(
				f"{event} already has a parent={event.parent}, trying to add to {self}",
			)

	def postAdd(self, event: EventType) -> None:
		event.parent = self  # needed? FIXME

	def insert(self, index: int, event: EventType) -> None:
		assert event.id is not None
		self.preAdd(event)
		self.idList.insert(index, event.id)
		self.postAdd(event)

	def append(self, event: EventType) -> None:
		assert event.id is not None
		self.preAdd(event)
		self.idList.append(event.id)
		self.postAdd(event)

	def add(self, event: EventType) -> None:
		if self.addEventsToBeginning:
			self.insert(0, event)
		else:
			self.append(event)

	def getPath(self) -> list[int]:
		if self.parent is None:
			raise RuntimeError("getPath: parent is None")
		path = SObj.getPath(self)
		if len(path) != 2:
			raise RuntimeError(f"getPath: unexpected {path=}")
		return path

	def index(self, ident: int) -> int:
		return self.idList.index(ident)

	def moveUp(self, index: int) -> None:
		self.idList.insert(index - 1, self.idList.pop(index))

	def moveDown(self, index: int) -> None:
		self.idList.insert(index + 1, self.idList.pop(index))

	def remove(self, event: EventType) -> int:  # call when moving to trash
		"""
		Excludes event from this container (group or trash),
		not delete event data completely
		and returns the index of (previously contained) event.
		"""
		assert event.id is not None
		index = self.idList.index(event.id)
		self.idList.remove(event.id)
		event.parent = None
		return index

	def copyFrom(self, other: Self) -> None:
		HistoryEventObjBinaryModel.copyFrom(self, other)
		self.calType = other.calType

	def getDict(self) -> dict[str, Any]:
		data = HistoryEventObjBinaryModel.getDict(self)
		data["calType"] = calTypes.names[self.calType]
		iconAbsToRelativelnData(data)
		return data

	def setDict(self, data: dict[str, Any]) -> None:
		HistoryEventObjBinaryModel.setDict(self, data)
		if "calType" in data:
			calType = data["calType"]
			try:
				self.calType = calTypes.names.index(calType)
			except ValueError:
				raise ValueError(f"Invalid calType: '{calType}'") from None
		# ---
		self.iconRelativeToAbsInObj()

	def getEventNoCache(self, eid: int) -> EventType:
		"""
		No caching. and no checking if group contains eid
		used only for sorting events.
		"""
		event = EventContainer._getEvent(self, eid)
		event.parent = self
		event.rulesHash = event.getRulesHash()
		return event

	def updateOccurrenceEvent(self, event: EventType) -> None:
		raise NotImplementedError

	def getCourseNameById(
		self,
		courseId: int,
	) -> str:
		raise NotImplementedError

	def getSortBys(self) -> tuple[str, list[tuple[str, str, bool]]]:
		if not self.enable:
			return self.sortByDefault, self.sortBys

		return "time_last", self.sortBys + [
			("time_last", _("Last Occurrence Time"), False),
			("time_first", _("First Occurrence Time"), False),
		]

	def getSortByValue(self, event: EventType, attr: str) -> Any:
		assert self.occur is not None
		assert event.id is not None
		if attr in {"time_last", "time_first"}:
			if event.isSingleOccur:
				epoch = event.getStartEpoch()
				if epoch is not None:
					return epoch
			if self.enable:
				if attr == "time_last":
					last = self.occur.getLastOfEvent(event.id)
				else:
					last = self.occur.getFirstOfEvent(event.id)
				if last:
					return last[0]
				log.info(f"no time_last returned for event {event.id}")
				return smallest
		return getattr(event, attr, smallest)

	def sort(
		self,
		attr: str = "summary",
		reverse: bool = False,
	) -> None:
		isTypeDep = True
		for name, _desc, dep in self.getSortBys()[1]:
			if name == attr:
				isTypeDep = dep
				break
		if isTypeDep:

			def event_key(event: EventType) -> Any:
				return (event.name, self.getSortByValue(event, attr))

		else:

			def event_key(event: EventType) -> Any:
				return self.getSortByValue(event, attr)

		self.idList.sort(
			key=lambda eid: event_key(self.getEventNoCache(eid)),
			reverse=reverse,
		)
