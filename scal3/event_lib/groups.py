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
from scal3.color_utils import RGB, RGBA
from scal3.s_object import copyParams

log = logger.get()

from contextlib import suppress
from copy import copy
from os.path import join
from time import perf_counter
from time import time as now
from typing import IO, TYPE_CHECKING, Self

from cachetools import LRUCache

from scal3 import ics
from scal3.cal_types import (
	getSysDate,
	to_jd,
)
from scal3.dict_utils import makeOrderedDict
from scal3.locale_man import tr as _
from scal3.time_utils import (
	durationDecode,
	durationEncode,
	getEpochFromJd,
)

from . import state
from .event_container import EventContainer
from .groups_import import (
	IMPORT_MODE_APPEND,
	IMPORT_MODE_OVERRIDE_MODIFIED,
	EventGroupsImportResult,
)
from .occur import (
	IntervalOccurSet,
	JdOccurSet,
	TimeListOccurSet,
)
from .register import classes

if TYPE_CHECKING:
	from collections.abc import Iterator, Sequence
	from typing import Any

	from scal3.color_utils import ColorType
	from scal3.event_search_tree import EventSearchTree
	from scal3.filesystem import FileSystem

	from .pytypes import (
		EventGroupType,
		EventSearchConditionDict,
		EventType,
		OccurSetType,
	)


__all__ = [
	"EventGroup",
	"LifetimeGroup",
	"NoteBook",
	"TaskList",
	"YearlyGroup",
	"groupsDir",
]

groupsDir = join("event", "groups")


@classes.group.register
@classes.group.setMain
class EventGroup(EventContainer):
	name = "group"
	nameAlias = ""
	tname = ""
	desc = _("Event Group")
	canConvertTo: list[str] = []
	actions: list[tuple[str, str]] = []  # [("Export to ICS", "exportToIcs")]
	# eventActions = []  # not implemented yet!
	eventCacheSizeMin = 0  # minimum cache size for events
	basicOptions: list[str] = EventContainer.basicOptions + [
		# "enable",  # FIXME
		# "remoteIds",  # user edits the value, FIXME
		"remoteSyncData",
		# "eventIdByRemoteIds",
		"deletedRemoteEvents",
	]
	params = EventContainer.params + [
		"calType",
		"enable",
		"showInDCal",
		"showInWCal",
		"showInMCal",
		"showInStatusIcon",
		"showInTimeLine",
		"color",
		"eventCacheSize",
		"eventTextSep",
		"startJd",
		"endJd",
		"remoteIds",
		"remoteSyncEnable",
		"remoteSyncDuration",
		"remoteSyncData",
		# "eventIdByRemoteIds",
		"deletedRemoteEvents",
		# "defaultEventType"
	]
	paramsOrder = [
		"enable",
		"uuid",
		"type",
		"title",
		"calType",
		"timeZoneEnable",
		"timeZone",
		"showInDCal",
		"showInWCal",
		"showInMCal",
		"showInStatusIcon",
		"showInTimeLine",
		"addEventsToBeginning",
		"showFullEventDesc",
		"color",
		"icon",
		"eventCacheSize",
		"eventTextSep",
		"startJd",
		"endJd",
		"remoteIds",
		"remoteSyncEnable",
		"remoteSyncDuration",
		"remoteSyncData",
		# "eventIdByRemoteIds",
		"deletedRemoteEvents",
		"idList",
	]
	importExportExclude: Sequence[str] = (
		"remoteIds",
		"remoteSyncEnable",
		"remoteSyncDuration",
		"remoteSyncData",
		# "eventIdByRemoteIds",
		"deletedRemoteEvents",
	)
	WidgetClass: Any

	@classmethod
	def load(
		cls,
		ident: int,
		fs: FileSystem,
	) -> EventGroupType | None:
		return cls.s_load(ident, fs)

	@property
	def mustId(self) -> int:
		assert self.id is not None
		return self.id

	@staticmethod
	def _timezoneFilter(event: EventType, tz: str) -> bool:
		return event.timeZone == tz if tz else not event.timeZoneEnable

	simpleFilters = {
		"text": lambda event, text: not text or text in event.getText(),
		"text_lower": lambda event, text: not text or text in event.getText().lower(),
		"modified_from": lambda event, epoch: event.modified >= epoch,
		"type": lambda event, typeName: event.name == typeName,
		"timezone": _timezoneFilter,
	}

	@classmethod
	def getFile(cls, ident: int) -> str:
		return join(groupsDir, f"{ident}.json")

	@classmethod
	def iterFiles(cls, fs: FileSystem) -> Iterator[str]:
		assert state.lastIds is not None
		for ident in range(1, state.lastIds.group + 1):
			fpath = cls.getFile(ident)
			if not fs.isfile(fpath):
				continue
			yield fpath

	@classmethod
	def getSubclass(cls, typeName: str) -> type[EventGroupType]:
		return classes.group.byName[typeName]

	def showInCal(self) -> bool:
		return self.showInDCal or self.showInWCal or self.showInMCal

	def __getitem__(self, key: int) -> EventType:
		if isinstance(key, int):  # eventId
			return self.getEvent(key)
		raise TypeError(
			f"invalid key {key!r} given to EventGroup.__getitem__",
		)

	def __setitem__(self, key: int, value: EventType) -> None:
		# if isinstance(key, basestring):  # ruleName
		# 	return self.setRule(key, value)
		if isinstance(key, int):  # eventId
			raise TypeError("can not assign event to group")  # FIXME
		raise TypeError(
			f"invalid key {key!r} given to EventGroup.__setitem__",
		)

	def __delitem__(self, key: int) -> None:
		if isinstance(key, int):  # eventId
			self.remove(self.getEvent(key))
		else:
			raise TypeError(
				f"invalid key {key!r} given to EventGroup.__delitem__",
			)

	def checkEventToAdd(self, event: EventType) -> bool:
		return event.name in self.acceptsEventTypes

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}(ident={self.id!r})"

	def __str__(self) -> str:
		return f"{self.__class__.__name__}(ident={self.id!r}, title='{self.title}')"

	def __init__(self, ident: int | None = None) -> None:
		EventContainer.__init__(self, title=self.desc)
		if ident is None:
			self.id = None
		else:
			self.setId(ident)
		self.enable = True
		self.__readOnly = False  # set True when syncing with remote group
		self.dataIsSet = False
		self.showInDCal = True
		self.showInWCal = True
		self.showInMCal = True
		self.showInStatusIcon = True
		self.showInTimeLine = True
		self.uuid: str | None = None
		self.idByUuid: dict[str, int] = {}
		self.color: ColorType = RGB(0, 0, 0)  # FIXME
		# self.defaultNotifyBefore = (10, 60)  # FIXME
		self.defaultEventType: str
		if len(self.acceptsEventTypes) == 1:
			self.defaultEventType = self.acceptsEventTypes[0]
			cls = classes.event.byName[self.defaultEventType]
			icon = cls.getDefaultIcon()
			if icon:
				self.icon = icon
		else:
			self.defaultEventType = "custom"
		# ---
		self.eventCacheSize = 100
		self.resetCache()
		# eventCache: key is eid, value is Event object
		# ---
		year, _month, _day = getSysDate(self.calType)
		self.startJd = to_jd(
			year - 10,
			1,
			1,
			self.calType,
		)
		self.endJd = to_jd(
			year + 5,
			1,
			1,
			self.calType,
		)
		# --
		self.occur: EventSearchTree | None = None
		# self.occurLoaded = False
		self.occurCount = 0
		self.notifyOccur: EventSearchTree | None = None
		self.initOccurrence()
		# ---
		self.setDefaults()
		# -----------
		self.clearRemoteAttrs()

	def resetCache(self) -> None:
		if self.eventCacheSize < 1:
			self.eventCache = None
			return
		self.eventCache = LRUCache(maxsize=self.eventCacheSize)

	def clearCache(self) -> None:
		if self.eventCache:
			self.eventCache.clear()

	def setRandomColor(self) -> None:
		import random

		from scal3.color_utils import hslToRgb

		# TODO: improve this?
		self.color = hslToRgb(random.uniform(0, 360), 1, 0.5)  # noqa: S311

	def clearRemoteAttrs(self) -> None:
		# self.remoteIds is (accountId: int, remoteGroupId: str) or None
		self.remoteIds: tuple[int, str] | None = None
		# remote groupId can be an integer or string,
		# depending on remote account type
		self.remoteSyncEnable = False
		self.remoteSyncDuration = (1.0, 3600)
		# remoteSyncDuration (value, unit) where value and unit are both ints
		self.remoteSyncData: dict[tuple[int, str], tuple[float, float]] = {}
		# remoteSyncData is a dict {remoteIds => (syncStartEpoch, syncEndEpoch)}
		# self.eventIdByRemoteIds = {}
		self.deletedRemoteEvents: dict[int, tuple[float, int, str, str]] = {}

	def setReadOnly(self, readOnly: bool) -> None:
		self.__readOnly = readOnly

	def isReadOnly(self) -> bool:
		return state.allReadOnly or self.__readOnly

	def save(self) -> None:
		if self.__readOnly:
			raise RuntimeError("event group is read-only right now")
		if self.id is None:
			self.setId()
		EventContainer.save(self)

	def getSyncDurationSec(self) -> float:
		"""Return Sync Duration in seconds (int)."""
		value, unit = self.remoteSyncDuration
		return value * unit

	def afterSync(self, startEpoch: float | None = None) -> None:
		assert self.remoteIds is not None
		endEpoch = now()
		if startEpoch is None:
			startEpoch = endEpoch
		self.remoteSyncData[self.remoteIds] = (startEpoch, endEpoch)

	def getLastSync(self) -> tuple[float, float] | None:
		"""Return a tuple (startEpoch, endEpoch) or None."""
		assert self.remoteIds is not None
		if self.remoteIds:
			with suppress(KeyError):
				return self.remoteSyncData[self.remoteIds]
		return None

	def setDefaults(self) -> None:
		"""
		Sets default values that depends on group type
		not common parameters, like those are set in __init__.
		"""

	def __bool__(self) -> bool:
		return self.enable  # FIXME

	def setId(self, ident: int | None = None) -> None:
		assert state.lastIds is not None
		if ident is None or ident < 0:
			ident = state.lastIds.group + 1  # FIXME
			state.lastIds.group = ident
		elif ident > state.lastIds.group:
			state.lastIds.group = ident
		self.id = ident
		self.file = self.getFile(self.id)

	def setTitle(self, title: str) -> None:
		self.title = title

	def setColor(self, color: RGB) -> None:
		self.color = color

	def getDict(self) -> dict[str, Any]:
		data = EventContainer.getDict(self)
		data["type"] = self.name
		for attr in (
			"remoteSyncData",
			# "eventIdByRemoteIds",
			"deletedRemoteEvents",
		):
			if isinstance(data[attr], dict):
				data[attr] = sorted(data[attr].items())
		return data

	def setDict(self, data: dict[str, Any]) -> None:
		eventCacheSize = self.eventCacheSize
		if "showInCal" in data:  # for compatibility
			data["showInDCal"] = data["showInWCal"] = data["showInMCal"] = data[
				"showInCal"
			]
			del data["showInCal"]

		EventContainer.setDict(self, data)

		self.color = RGBA.fromList(self.color)

		if isinstance(self.remoteIds, list):
			self.remoteIds = tuple(self.remoteIds)
		for attr in (
			"remoteSyncData",
			# "eventIdByRemoteIds",
			"deletedRemoteEvents",
		):
			value = getattr(self, attr)
			if isinstance(value, list):
				valueDict = {}
				for item in value:
					if len(item) != 2:
						continue
					if not isinstance(item[0], tuple | list):
						continue
					valueDict[tuple(item[0])] = item[1]
				setattr(self, attr, valueDict)
		if "id" in data:
			self.setId(data["id"])
		self.startJd = int(self.startJd)
		self.endJd = int(self.endJd)

		if self.eventCacheSize != eventCacheSize:
			self.eventCacheSize = max(self.eventCacheSize, self.eventCacheSizeMin)
			self.resetCache()

		# ----
		# if "defaultEventType" in data:
		# 	self.defaultEventType = data["defaultEventType"]
		# 	if not self.defaultEventType in classes.event.names:
		# 		raise ValueError(f"Invalid defaultEventType: {self.defaultEventType!r}")

	# event objects should be accessed from outside
	# only via one of the following 4 methods:
	# getEvent, getEventNoCache, create

	def removeFromCache(self, eid: int) -> None:
		if not self.eventCache:
			return
		if self.eventCache.get(eid) is not None:
			self.eventCache.pop(eid)

	def setToCache(self, event: EventType) -> None:
		if not self.eventCache:
			return
		self.eventCache[event.id] = event

	def getEvent(self, ident: int) -> EventType:
		if ident not in self.idList:
			raise ValueError(f"{self} does not contain {ident!r}")
		if self.eventCache:
			event = self.eventCache.get(ident)
			if event is not None:
				return event
		event = EventContainer.getEvent(self, ident)
		event.rulesHash = event.getRulesHash()
		if self.enable:
			self.setToCache(event)
		return event

	def create(self, eventType: str) -> EventType:
		# if not eventType in self.acceptsEventTypes: # FIXME
		# 	raise ValueError(
		# 		f"Event type '{eventType}' not supported "
		# 		f"in group type "{self.name}""
		# 	)
		event = classes.event.byName[eventType](parent=self)  # FIXME
		event.fs = self.fs
		return event

	# -----------------------------------------------

	# call when moving to trash
	def remove(self, event: EventType) -> int:
		assert event.id is not None
		index = EventContainer.remove(self, event)
		self.removeFromCache(event.id)
		if event.remoteIds:
			remoteIds = event.remoteIds
			self.deletedRemoteEvents[event.id] = (
				now(),
				remoteIds[0],
				remoteIds[1],
				remoteIds[2],
			)
		# try:
		# 	del self.eventIdByRemoteIds[event.remoteIds]
		# except:
		# 	pass
		assert self.occur is not None
		self.occurCount -= self.occur.delete(event.id)
		return index

	# clearEvents or excludeAll or removeAll?
	def removeAll(self) -> None:
		if self.eventCache:
			for event in self.eventCache.values():
				event.parent = None  # needed? FIXME
		# ---
		self.idList = []
		self.clearCache()
		assert self.occur is not None
		self.occur.clear()
		self.occurCount = 0

	def postAdd(self, event: EventType) -> None:
		EventContainer.postAdd(self, event)
		self.setToCache(event)
		# if event.remoteIds:
		# 	self.eventIdByRemoteIds[event.remoteIds] = event.id
		# need to update self.occur?
		# its done in event.afterModify() right?
		# not when moving event from another group
		if self.enable:
			self.updateOccurrenceEvent(event)

	def updateCache(self, event: EventType) -> None:
		if self.eventCache and self.eventCache.get(event.id) is not None:
			self.setToCache(event)
		event.afterModify()

	def __copy__(self) -> Self:
		newGroup = self.__class__()
		newGroup.fs = self.fs
		copyParams(newGroup, self)
		newGroup.removeAll()
		return newGroup

	def copyAs(self, newGroupType: str) -> EventGroupType:
		newGroup: EventGroupType = classes.group.byName[newGroupType]()
		newGroup.fs = self.fs
		copyParams(newGroup, self)
		newGroup.removeAll()
		return newGroup

	def deepCopy(self) -> EventGroupType:
		newGroup = copy(self)
		for event in self:
			newEvent = copy(event)
			newEvent.save()
			newGroup.append(newEvent)
		return newGroup

	def deepConvertTo(self, newGroupType: str) -> EventGroupType:
		newGroup = self.copyAs(newGroupType)
		newEventType = newGroup.acceptsEventTypes[0]
		newGroup.enable = False  # to prevent per-event node update
		for event in self:
			newEvent = newGroup.create(newEventType)
			newEvent.changeCalType(event.calType)  # FIXME needed?
			newEvent.copyFromExact(event)
			newEvent.setId(event.id)
			newEvent.save()
			newGroup.append(newEvent)
		newGroup.enable = self.enable
		self.removeAll()
		# events with the same id"s, can not be contained by two groups
		return newGroup

	def calcGroupOccurrences(self) -> Iterator[tuple[EventType, OccurSetType]]:
		startJd = self.startJd
		endJd = self.endJd
		for event in self:
			occur = event.calcEventOccurrenceIn(startJd, endJd)
			if occur:
				yield event, occur

	def afterModify(self) -> None:  # FIXME
		EventContainer.afterModify(self)
		self.initOccurrence()
		# ----
		if self.enable:
			self.updateOccurrence()
		else:
			self.clearCache()

	def updateOccurrenceEvent(self, event: EventType) -> None:
		log.debug(
			f"updateOccurrenceEvent: id={self.id} title={self.title} eid={event.id}",
		)
		eid = event.id
		assert eid is not None
		assert self.occur is not None
		self.occurCount -= self.occur.delete(eid)

		occur = event.calcEventOccurrence()
		if not occur:
			return

		for t0, t1 in occur.getTimeRangeList():
			self.addOccur(t0, t1, eid)

		if event.notifiers:
			assert self.notifyOccur is not None
			self.notificationEnabled = True
			for t0, t1 in occur.getTimeRangeList():
				self.notifyOccur.add(t0 - event.getNotifyBeforeSec(), t1, eid)

	def initOccurrence(self) -> None:
		from scal3.event_search_tree import EventSearchTree

		# from scal3.time_line_tree import TimeLineTree
		# self.occur = TimeLineTree(offset=self.getEpochFromJd(self.endJd))
		self.occur = EventSearchTree()
		# self.occurLoaded = False
		self.occurCount = 0
		self.notifyOccur = EventSearchTree()

	def clear(self) -> None:
		assert self.occur is not None
		self.occur.clear()
		self.occurCount = 0
		self.notificationEnabled = False

	def addOccur(self, t0: float, t1: float, eid: int) -> None:
		assert self.occur is not None
		self.occur.add(t0, t1, eid)
		self.occurCount += 1

	def updateOccurrenceLog(self, dt: float) -> None:
		log.debug(
			f"updateOccurrence, id={self.id}, title='{self.title}', "
			f"count={self.occurCount}, time={dt:.1f}",
		)

	def updateOccurrence(self) -> None:
		stm0 = perf_counter()
		self.clear()

		notificationEnabled = False
		for event, occur in self.calcGroupOccurrences():
			assert event.id is not None
			for t0, t1 in occur.getTimeRangeList():
				self.addOccur(t0, t1, event.id)
			if event.notifiers:
				notificationEnabled = True
				assert self.notifyOccur is not None
				for t0, t1 in occur.getTimeRangeList():
					self.notifyOccur.add(t0 - event.getNotifyBeforeSec(), t1, event.id)
		self.notificationEnabled = notificationEnabled

		# self.occurLoaded = True
		log.debug(f"time = {(perf_counter() - stm0) * 1000} ms for group {self.title}")
		# log.debug(
		# 	f"updateOccurrence, id={self.id}, title={self.title}, " +
		# 	f"count={self.occurCount}, time={perf_counter()-stm0}"
		# )
		# log.debug(
		# 	f"{self.id} {1000*(perf_counter()-stm0)} "
		# 	f"{self.occur.calcAvgDepth():.1f}"
		# )

	@staticmethod
	def _exportToIcsFpEvent(
		fp: IO[str],
		event: EventType,
		currentTimeStamp: str,
	) -> None:
		# log.debug("exportToIcsFp", event.id)

		commonText = (
			"\n".join(
				[
					"BEGIN:VEVENT",
					"CREATED:" + currentTimeStamp,
					"DTSTAMP:" + currentTimeStamp,  # FIXME
					"LAST-MODIFIED:" + currentTimeStamp,
					"SUMMARY:" + event.getSummary().replace("\n", "\\n"),
					"DESCRIPTION:" + event.getDescription().replace("\n", "\\n"),
					# "CATEGORIES:" + self.title,  # FIXME
					"CATEGORIES:" + event.name,  # FIXME
					"LOCATION:",
					"SEQUENCE:0",
					"STATUS:CONFIRMED",
					"UID:" + event.icsUID(),
				],
			)
			+ "\n"
		)

		icsData = event.getIcsData()
		if icsData is not None:
			vevent = commonText
			for key, value in icsData:
				vevent += key + ":" + value + "\n"
			vevent += "END:VEVENT\n"
			fp.write(vevent)
			return

		occur = event.calcEventOccurrence()
		if not occur:
			return
		if isinstance(occur, JdOccurSet):
			# for sectionStartJd in occur.getDaysJdList():
			# 	sectionEndJd = sectionStartJd + 1
			for sectionStartJd, sectionEndJd in occur.calcJdRanges():
				vevent = commonText
				vevent += "\n".join(
					[
						"DTSTART;VALUE=DATE:" + ics.getIcsDateByJd(sectionStartJd),
						"DTEND;VALUE=DATE:" + ics.getIcsDateByJd(sectionEndJd),
						"TRANSP:TRANSPARENT",
						# http://www.kanzaki.com/docs/ical/transp.html
						"END:VEVENT\n",
					],
				)
				fp.write(vevent)
		elif isinstance(occur, IntervalOccurSet | TimeListOccurSet):
			for startEpoch, endEpoch in occur.getTimeRangeList():
				vevent = commonText
				parts = [
					"DTSTART:" + ics.getIcsTimeByEpoch(startEpoch),
				]
				if endEpoch is not None and endEpoch - startEpoch > 1:
					# FIXME why is endEpoch sometimes float?
					parts.append("DTEND:" + ics.getIcsTimeByEpoch(int(endEpoch)))
				parts += [
					"TRANSP:OPAQUE",  # FIXME
					# http://www.kanzaki.com/docs/ical/transp.html
					"END:VEVENT\n",
				]
				vevent += "\n".join(parts)
				fp.write(vevent)
		else:
			raise TypeError(f"invalid type {type(occur)} for occur")

	def exportToIcsFp(self, fp: IO[str]) -> None:
		currentTimeStamp = ics.getIcsTimeByEpoch(now())
		for event in self:
			self._exportToIcsFpEvent(fp, event, currentTimeStamp)

	def exportData(self) -> dict[str, Any]:
		data = self.getDict()
		for attr in self.importExportExclude:
			del data[attr]
		data = makeOrderedDict(data, self.paramsOrder)
		data["events"] = []
		for eventId in self.idList:
			event = EventContainer.getEvent(self, eventId)
			modified = event.modified
			if event.uuid is None:
				event.save()
			eventData = event.getDictOrdered()
			eventData["modified"] = modified
			# eventData["sha1"] = event.lastHash
			data["events"].append(eventData)
			with suppress(KeyError):
				del eventData["remoteIds"]  # FIXME
			if not eventData["notifiers"]:
				del eventData["notifiers"]
				del eventData["notifyBefore"]
		del data["idList"]
		return data

	def loadEventIdByUuid(self) -> dict[str, int]:
		existingIds = set(self.idByUuid.values())
		for eid in self.idList:
			if eid in existingIds:
				continue
			event = self.getEvent(eid)
			if event.uuid is None:
				continue
			self.idByUuid[event.uuid] = eid
		return self.idByUuid

	def appendByData(self, eventData: dict[str, Any]) -> EventType:
		event = self.create(eventData["type"])
		event.setDict(eventData)
		event.save()
		self.append(event)
		return event

	def importData(
		self,
		data: dict[str, Any],
		importMode: int,
	) -> EventGroupsImportResult:
		"""The caller must call group.save() after this."""
		if not self.dataIsSet or importMode == IMPORT_MODE_OVERRIDE_MODIFIED:
			self.setDict(data)

		res = EventGroupsImportResult()
		gid = self.id
		assert gid is not None

		if importMode == IMPORT_MODE_APPEND:
			for eventData in data["events"]:
				event = self.appendByData(eventData)
				assert event.id is not None
				res.newEventIds.add((gid, event.id))
			return res

		idByUuid = self.loadEventIdByUuid()

		for eventData in data["events"]:
			modified = eventData.get("modified")
			uuid = eventData.get("uuid")
			if modified is None or uuid is None:
				event = self.appendByData(eventData)
				assert event.id is not None
				res.newEventIds.add((gid, event.id))
				continue

			eid = idByUuid.get(uuid)
			if eid is None:
				log.debug(f"appending event uuid = {uuid}")
				event = self.appendByData(eventData)
				assert event.id is not None
				res.newEventIds.add((gid, event.id))
				continue

			if importMode != IMPORT_MODE_OVERRIDE_MODIFIED:
				# assumed IMPORT_MODE_SKIP_MODIFIED
				log.debug(f"skipping to override existing uuid={uuid!r}, eid={eid!r}")
				continue

			event = self.getEvent(eid)
			event.setDictOverride(eventData)
			event.save()
			res.modifiedEventIds.add((gid, eid))
			log.debug(f"overriden existing uuid={uuid!r}, eid={eid!r}")

		return res

	def _searchTimeFilter(self, conds: EventSearchConditionDict) -> Iterator[int]:
		if not ("time_from" in conds or "time_to" in conds):
			yield from self.idList
			return

		try:
			time_from = conds["time_from"]
		except KeyError:
			time_from = getEpochFromJd(self.startJd)
		else:
			del conds["time_from"]
		try:
			time_to = conds["time_to"]
		except KeyError:
			time_to = getEpochFromJd(self.endJd)
		else:
			del conds["time_to"]

		assert self.occur is not None
		for item in self.occur.search(time_from, time_to):
			yield item.eid

	def search(self, conds: EventSearchConditionDict) -> Iterator[EventType]:
		conds = conds.copy()  # because we may modify it

		for eid in self._searchTimeFilter(conds):
			try:
				event = self[eid]
			except Exception:
				log.exception("")
				continue
			for key, value in conds.items():
				func = self.simpleFilters[key]
				if not func(event, value):
					break
			else:
				if event.uuid is None:
					event.save()
				yield event

	def createPatchList(self, sinceEpoch: int) -> list[dict[str, Any]]:
		patchList = []

		for event in self:
			# if not event.remoteIds:  # FIXME
			eventHist = event.loadHistory()
			if not eventHist:
				log.info(f"{eventHist = }")
				continue
			# assert event.modified == eventHist[0][0]
			if eventHist[0][0] > sinceEpoch:
				creationEpoch = eventHist[-1][0]
				if creationEpoch > sinceEpoch:
					patchList.append(
						{
							"eventId": event.id,
							"eventType": event.name,
							"action": "add",
							"newEventData": event.getV4Dict(),
						},
					)
				else:
					sinceHash = None
					for tmpEpoch, tmpHash in eventHist:
						sinceHash = tmpHash
						if tmpEpoch <= sinceEpoch:
							break
					assert sinceHash is not None  # FIXME?
					patchList.append(
						event.createPatchByHash(sinceHash),
					)

		return patchList


@classes.group.register
class TaskList(EventGroup):
	name = "taskList"
	desc = _("Task List")
	params = EventGroup.params + ["defaultDuration"]
	acceptsEventTypes: Sequence[str] = (
		"task",
		"allDayTask",
	)
	# actions = EventGroup.actions + []
	sortBys = EventGroup.sortBys + [
		("start", _("Start"), True),
		("end", _("End"), True),
	]
	sortByDefault = "start"

	def getSortByValue(self, event: EventType, attr: str) -> Any:
		if event.name in self.acceptsEventTypes:
			if attr == "start":
				return event.getStartEpoch()
			if attr == "end":
				return event.getEndEpoch()
		return EventGroup.getSortByValue(self, event, attr)

	def __init__(self, ident: int | None = None) -> None:
		EventGroup.__init__(self, ident)
		self.defaultDuration = (0.0, 1)  # (value, unit)

	def getDict(self) -> dict[str, Any]:
		data = EventGroup.getDict(self)
		data["defaultDuration"] = durationEncode(*self.defaultDuration)
		return data

	def setDict(self, data: dict[str, Any]) -> None:
		EventGroup.setDict(self, data)
		if "defaultDuration" in data:
			self.defaultDuration = durationDecode(data["defaultDuration"])


@classes.group.register
class NoteBook(EventGroup):
	name = "noteBook"
	desc = _("Note Book")
	acceptsEventTypes: Sequence[str] = ("dailyNote",)
	canConvertTo: list[str] = [
		"yearly",
		"taskList",
	]
	# actions = EventGroup.actions + []
	sortBys = EventGroup.sortBys + [("date", _("Date"), True)]
	sortByDefault = "date"

	def getSortByValue(self, event: EventType, attr: str) -> Any:
		if event.name in self.acceptsEventTypes and attr == "date":
			return event.getJd()
		return EventGroup.getSortByValue(self, event, attr)


@classes.group.register
class YearlyGroup(EventGroup):
	name = "yearly"
	desc = _("Yearly Events Group")
	acceptsEventTypes: Sequence[str] = ("yearly",)
	canConvertTo: list[str] = ["noteBook"]
	params = EventGroup.params + ["showDate"]

	def __init__(self, ident: int | None = None) -> None:
		EventGroup.__init__(self, ident)
		self.showDate = True


@classes.group.register
class LifetimeGroup(EventGroup):
	name = "lifetime"
	nameAlias = "lifeTime"
	desc = _("Lifetime Events Group")
	acceptsEventTypes: Sequence[str] = ("lifetime",)
	sortBys = EventGroup.sortBys + [
		("start", _("Start"), True),
	]
	params = EventGroup.params + ["showSeparateYmdInputs"]

	def getSortByValue(self, event: EventType, attr: str) -> Any:
		if event.name in self.acceptsEventTypes:
			if attr == "start":
				return event.getStartJd()
			if attr == "end":
				return event.getEndJd()
		return EventGroup.getSortByValue(self, event, attr)

	def __init__(self, ident: int | None = None) -> None:
		self.showSeparateYmdInputs = False
		EventGroup.__init__(self, ident)

	def setDict(self, data: dict[str, Any]) -> None:
		if "showSeperatedYmdInputs" in data:
			# misspell in < 3.1.x
			data["showSeparateYmdInputs"] = data["showSeperatedYmdInputs"]
		if "showSeparatedYmdInputs" in data:
			data["showSeparateYmdInputs"] = data["showSeparatedYmdInputs"]
		EventGroup.setDict(self, data)

	def setDefaults(self) -> None:
		# only show in time line
		self.showInDCal = False
		self.showInWCal = False
		self.showInMCal = False
		self.showInStatusIcon = False
