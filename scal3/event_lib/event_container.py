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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from typing import Any

from time import time as now

from scal3.cal_types import calTypes
from scal3.json_utils import jsonToData
from scal3.locale_man import tr as _

# from scal3.interval_utils import
from scal3.s_object import updateBasicDataFromBson

from .events import Event
from .icon import iconAbsToRelativelnData, iconRelativeToAbsInObj
from .objects import HistoryEventObjBinaryModel
from .register import classes

__all__ = ["EventContainer"]


class Smallest:
	def __eq__(self, other: object) -> bool:
		return isinstance(other, Smallest)

	def __lt__(self, other: Any) -> bool:
		return not isinstance(other, Smallest)

	def __gt__(self, other: Any) -> bool:
		return False

	def __hash__(self):
		return hash(Smallest)


smallest = Smallest()


class EventContainer(HistoryEventObjBinaryModel):
	name = ""
	desc = ""
	basicParams = (
		"idList",  # FIXME
		"uuid",
	)
	# HistoryEventObjBinaryModel.params is empty
	params = (
		"timeZoneEnable",
		"timeZone",
		"icon",
		"title",
		"showFullEventDesc",
		"idList",
		"modified",
		"uuid",
		"addEventsToBeginning",
	)

	acceptsEventTypes = (
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

	sortBys = (
		# name, description, is_type_dependent
		("calType", _("Calendar Type"), False),
		("summary", _("Summary"), False),
		("description", _("Description"), False),
		("icon", _("Icon"), False),
	)
	sortByDefault = "summary"

	def __getitem__(self, key):
		if isinstance(key, int):  # eventId
			return self.getEvent(key)
		raise TypeError(
			f"invalid key type for {key!r} given to EventContainer.__getitem__",
		)

	def getTimeZoneStr(self):
		if self.timeZoneEnable and self.timeZone:
			return self.timeZone
		return ""

	def byIndex(self, index):
		return self.getEvent(self.idList[index])

	def __str__(self) -> str:
		return f"{self.__class__.__name__}(title='{self.title}')"

	def __init__(self, title="Untitled"):
		self.fs = None
		self.parent = None
		self.timeZoneEnable = False
		self.timeZone = ""
		self.calType = calTypes.primary
		self.idList = []
		self.title = title
		self.icon = ""
		self.showFullEventDesc = False
		self.addEventsToBeginning = False
		# ------
		self.uuid = None
		self.modified = now()
		# self.eventsModified = self.modified
		######
		self.notificationEnabled = False

	def afterModify(self):
		self.modified = now()

	def getEvent(self, eid):
		if eid not in self.idList:
			raise ValueError(f"{self} does not contain {eid!r}")
		return self._getEvent(eid)

	def _getEvent(self, eid):
		eventFile = Event.getFile(eid)
		if not self.fs.isfile(eventFile):
			# self.idList.remove(eid)
			# self.save()  # FIXME
			raise FileNotFoundError(
				f"error while loading event file {eventFile!r}: "
				f"file not found. {eid=}, container={self!r}",
			)
		with self.fs.open(eventFile) as fp:
			data = jsonToData(fp.read())
		data["id"] = eid  # FIXME
		lastEpoch, lastHash = updateBasicDataFromBson(
			data,
			eventFile,
			"event",
			self.fs,
		)
		event = classes.event.byName[data["type"]](eid)
		event.fs = self.fs
		event.parent = self
		event.setData(data)
		event.lastHash = lastHash
		event.modified = lastEpoch
		return event

	def __iter__(self):
		for eid in self.idList:
			try:
				event = self.getEvent(eid)
			except Exception:  # noqa: PERF203
				log.exception("")
			else:
				yield event

	def __len__(self):
		return len(self.idList)

	def preAdd(self, event: Event):
		if event.id in self.idList:
			raise ValueError(f"{self} already contains {event}")
		if event.parent not in {None, self}:
			raise ValueError(
				f"{event} already has a parent={event.parent}, trying to add to {self}",
			)

	def postAdd(self, event: Event):
		event.parent = self  # needed? FIXME

	def insert(self, index, event: Event):
		self.preAdd(event)
		self.idList.insert(index, event.id)
		self.postAdd(event)

	def append(self, event: Event):
		self.preAdd(event)
		self.idList.append(event.id)
		self.postAdd(event)

	def add(self, event: Event) -> None:
		if self.addEventsToBeginning:
			self.insert(0, event)
		else:
			self.append(event)

	def index(self, eid):
		return self.idList.index(eid)

	def moveUp(self, index):
		return self.idList.insert(index - 1, self.idList.pop(index))

	def moveDown(self, index):
		return self.idList.insert(index + 1, self.idList.pop(index))

	def remove(self, event: Event):  # call when moving to trash
		"""
		Excludes event from this container (group or trash),
		not delete event data completely
		and returns the index of (previously contained) event.
		"""
		index = self.idList.index(event.id)
		self.idList.remove(event.id)
		event.parent = None
		return index

	def copyFrom(self, other):
		HistoryEventObjBinaryModel.copyFrom(self, other)
		self.calType = other.calType

	def getData(self):
		data = HistoryEventObjBinaryModel.getData(self)
		data["calType"] = calTypes.names[self.calType]
		iconAbsToRelativelnData(data)
		return data

	def setData(self, data) -> None:
		HistoryEventObjBinaryModel.setData(self, data)
		if "calType" in data:
			calType = data["calType"]
			try:
				self.calType = calTypes.names.index(calType)
			except ValueError:
				raise ValueError(f"Invalid calType: '{calType}'") from None
		# ---
		iconRelativeToAbsInObj(self)

	def getEventNoCache(self, eid: int) -> Event:
		"""
		No caching. and no checking if group contains eid
		used only for sorting events.
		"""
		event = EventContainer._getEvent(self, eid)
		event.parent = self
		event.rulesHash = event.getRulesHash()
		return event

	def getSortBys(self) -> tuple[str, list[str]]:
		if not self.enable:
			return self.sortByDefault, self.sortBys

		return "time_last", self.sortBys + [
			("time_last", _("Last Occurrence Time"), False),
			("time_first", _("First Occurrence Time"), False),
		]

	def getSortByValue(self, event: Event, attr: str) -> Any:
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

			def event_key(event: Event):
				return (event.name, self.getSortByValue(event, attr))

		else:

			def event_key(event: Event):
				return self.getSortByValue(event, attr)

		self.idList.sort(
			key=lambda eid: event_key(self.getEventNoCache(eid)),
			reverse=reverse,
		)
