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
	import io
	from collections.abc import Iterator
	from datetime import datetime
	from typing import Any

	from scal3.filesystem import FileSystem

	from .events import Event

from contextlib import suppress
from os.path import join
from time import perf_counter
from time import time as now
from typing import NamedTuple

from cachetools import LRUCache

import mytz
from scal3 import core, ics, locale_man
from scal3.cal_types import (
	calTypes,
	getSysDate,
	jd_to,
	to_jd,
)
from scal3.core import getAbsWeekNumberFromJd
from scal3.date_utils import dateDecode, dateEncode
from scal3.event_lib import state
from scal3.locale_man import textNumEncode
from scal3.locale_man import tr as _
from scal3.s_object import (
	SObj,
	makeOrderedData,
)
from scal3.time_utils import (
	durationDecode,
	durationEncode,
	getEpochFromJd,
	hmDecode,
	hmEncode,
	simpleTimeEncode,
	timeToFloatHour,
)
from scal3.utils import findNearestIndex

from .event_container import EventContainer
from .groups_import import (
	IMPORT_MODE_APPEND,
	IMPORT_MODE_OVERRIDE_MODIFIED,
	EventGroupsImportResult,
)
from .occur import (
	IntervalOccurSet,
	JdOccurSet,
	OccurSet,
	TimeListOccurSet,
)
from .register import classes

__all__ = [
	"EventGroup",
	"LargeScaleGroup",
	"NoteBook",
	"groupsDir",
]

groupsDir = join("event", "groups")


@classes.group.register
@classes.group.setMain
class EventGroup(EventContainer):
	name = "group"
	desc = _("Event Group")
	canConvertTo = ()
	actions = []  # [("Export to ICS", "exportToIcs")]
	# eventActions = []  # not implemented yet!
	eventCacheSizeMin = 0  # minimum cache size for events
	basicParams = EventContainer.basicParams + (
		# "enable",  # FIXME
		# "remoteIds",  # user edits the value, FIXME
		"remoteSyncData",
		# "eventIdByRemoteIds",
		"deletedRemoteEvents",
	)
	params = EventContainer.params + (
		# "enable",
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
	)
	paramsOrder = (
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
	)
	importExportExclude = (
		"remoteIds",
		"remoteSyncEnable",
		"remoteSyncDuration",
		"remoteSyncData",
		# "eventIdByRemoteIds",
		"deletedRemoteEvents",
	)

	@staticmethod
	def _timezoneFilter(event: Event, tz: str) -> bool:
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
		for ident in range(1, state.lastIds.group + 1):
			fpath = cls.getFile(ident)
			if not fs.isfile(fpath):
				continue
			yield fpath

	@classmethod
	def getSubclass(cls, typeName: str) -> type[EventGroup]:
		return classes.group.byName[typeName]

	def getTimeZoneObj(self) -> datetime.tzinfo:
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

	def showInCal(self) -> bool:
		return self.showInDCal or self.showInWCal or self.showInMCal

	def __getitem__(self, key: str) -> Event:
		# if isinstance(key, basestring):  # ruleName
		# 	return self.getRule(key)
		if isinstance(key, int):  # eventId
			return self.getEvent(key)
		raise TypeError(
			f"invalid key {key!r} given to EventGroup.__getitem__",
		)

	def __setitem__(self, key: int, value: Event) -> None:
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

	def checkEventToAdd(self, event: Event) -> bool:
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
		self.showInStatusIcon = False
		self.showInTimeLine = True
		self.uuid = None
		self.idByUuid = {}
		self.color = (0, 0, 0)  # FIXME
		# self.defaultNotifyBefore = (10, 60)  # FIXME
		if len(self.acceptsEventTypes) == 1:
			self.defaultEventType = self.acceptsEventTypes[0]
			cls = classes.event.byName[self.defaultEventType]
			icon = cls.getDefaultIcon()
			if icon:
				self.icon = icon
		else:
			self.defaultEventType = "custom"
		self.eventTextSep = core.eventTextSep
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
		# self.remoteIds is (accountId, groupId) or None
		self.remoteIds = None
		# remote groupId can be an integer or string,
		# depending on remote account type
		self.remoteSyncEnable = False
		self.remoteSyncDuration = (1, 3600)
		# remoteSyncDuration (value, unit) where value and unit are both ints
		self.remoteSyncData = {}
		# remoteSyncData is a dict {remoteIds => (syncStartEpoch, syncEndEpoch)}
		# self.eventIdByRemoteIds = {}
		self.deletedRemoteEvents = {}

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

	def getSyncDurationSec(self) -> int:
		"""Return Sync Duration in seconds (int)."""
		value, unit = self.remoteSyncDuration
		return value * unit

	def afterSync(self, startEpoch: int | None = None) -> None:
		endEpoch = now()
		if startEpoch is None:
			startEpoch = endEpoch
		self.remoteSyncData[self.remoteIds] = (startEpoch, endEpoch)

	def getLastSync(self) -> int | None:
		"""Return a tuple (startEpoch, endEpoch) or None."""
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
		if ident is None or ident < 0:
			ident = state.lastIds.group + 1  # FIXME
			state.lastIds.group = ident
		elif ident > state.lastIds.group:
			state.lastIds.group = ident
		self.id = ident
		self.file = self.getFile(self.id)

	def setTitle(self, title: str) -> None:
		self.title = title

	def setColor(self, color: tuple[int, int, int]) -> None:
		self.color = color

	def getData(self) -> dict[str, Any]:
		data = EventContainer.getData(self)
		data["type"] = self.name
		for attr in (
			"remoteSyncData",
			# "eventIdByRemoteIds",
			"deletedRemoteEvents",
		):
			if isinstance(data[attr], dict):
				data[attr] = sorted(data[attr].items())
		return data

	def setData(self, data: dict[str, Any]) -> None:
		eventCacheSize = self.eventCacheSize
		if "showInCal" in data:  # for compatibility
			data["showInDCal"] = data["showInWCal"] = data["showInMCal"] = data[
				"showInCal"
			]
			del data["showInCal"]
		EventContainer.setData(self, data)
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

	def setToCache(self, event: Event) -> None:
		if not self.eventCache:
			return
		self.eventCache[event.id] = event

	def getEvent(self, eid: int) -> Event:
		if eid not in self.idList:
			raise ValueError(f"{self} does not contain {eid!r}")
		if self.eventCache:
			event = self.eventCache.get(eid)
			if event is not None:
				return event
		event = EventContainer.getEvent(self, eid)
		event.rulesHash = event.getRulesHash()
		if self.enable:
			self.setToCache(event)
		return event

	def create(self, eventType: str) -> Event:
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
	def remove(self, event: Event) -> int:
		index = EventContainer.remove(self, event)
		self.removeFromCache(event.id)
		if event.remoteIds:
			self.deletedRemoteEvents[event.id] = (now(),) + event.remoteIds
		# try:
		# 	del self.eventIdByRemoteIds[event.remoteIds]
		# except:
		# 	pass
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
		self.occur.clear()
		self.occurCount = 0

	def postAdd(self, event: Event) -> None:
		EventContainer.postAdd(self, event)
		self.setToCache(event)
		# if event.remoteIds:
		# 	self.eventIdByRemoteIds[event.remoteIds] = event.id
		# need to update self.occur?
		# its done in event.afterModify() right?
		# not when moving event from another group
		if self.enable:
			self.updateOccurrenceEvent(event)

	def updateCache(self, event: Event) -> None:
		if self.eventCache and self.eventCache.get(event.id) is not None:
			self.setToCache(event)
		event.afterModify()

	def copy(self) -> EventGroup:
		newGroup = SObj.copy(self)
		newGroup.removeAll()
		return newGroup

	def copyFrom(self, other: EventGroup) -> None:
		EventContainer.copyFrom(self, other)
		self.enable = other.enable

	def copyAs(self, newGroupType: str) -> EventGroup:
		newGroup = classes.group.byName[newGroupType]()
		newGroup.fs = self.fs
		newGroup.copyFrom(self)
		newGroup.removeAll()
		return newGroup

	def deepCopy(self) -> EventGroup:
		newGroup = self.copy()
		for event in self:
			newEvent = event.copy()
			newEvent.save()
			newGroup.append(newEvent)
		return newGroup

	def deepConvertTo(self, newGroupType: str) -> EventGroup:
		newGroup = self.copyAs(newGroupType)
		newEventType = newGroup.acceptsEventTypes[0]
		newGroup.enable = False  # to prevent per-event node update
		for event in self:
			newEvent = newGroup.create(newEventType)
			newEvent.changeCalType(event.calType)  # FIXME needed?
			newEvent.copyFrom(event, True)
			newEvent.setId(event.id)
			newEvent.save()
			newGroup.append(newEvent)
		newGroup.enable = self.enable
		self.removeAll()
		# events with the same id"s, can not be contained by two groups
		return newGroup

	def calcGroupOccurrences(self) -> Iterator[tuple[Event, OccurSet]]:
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

	def updateOccurrenceEvent(self, event: Event) -> None:
		log.debug(
			f"updateOccurrenceEvent: id={self.id} title={self.title} eid={event.id}",
		)
		eid = event.id
		self.occurCount -= self.occur.delete(eid)

		occur = event.calcEventOccurrence()
		if not occur:
			return

		for t0, t1 in occur.getTimeRangeList():
			self.addOccur(t0, t1, eid)

		if event.notifiers:
			self.notificationEnabled = True
			for t0, t1 in occur.getTimeRangeList():
				self.notifyOccur.add(t0 - event.getNotifyBeforeSec(), t1, event.id)

	def initOccurrence(self) -> None:
		from scal3.event_search_tree import EventSearchTree

		# from scal3.time_line_tree import TimeLineTree
		# self.occur = TimeLineTree(offset=self.getEpochFromJd(self.endJd))
		self.occur = EventSearchTree()
		# self.occurLoaded = False
		self.occurCount = 0
		self.notifyOccur = EventSearchTree()

	def clear(self) -> None:
		self.occur.clear()
		self.occurCount = 0
		self.notificationEnabled = False

	def addOccur(self, t0: float, t1: float, eid: int) -> None:
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
			for t0, t1 in occur.getTimeRangeList():
				self.addOccur(t0, t1, event.id)
			if event.notifiers:
				notificationEnabled = True
				for t0, t1 in occur.getTimeRangeList():
					self.notifyOccur.add(t0 - event.getNotifyBeforeSec(), t1, event.id)
		self.notificationEnabled = notificationEnabled

		# self.occurLoaded = True
		log.debug(f"time = {(perf_counter() - stm0) * 1000} ms")
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
		fp: io.TextIOBase,
		event: Event,
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

	def exportToIcsFp(self, fp: io.TextIOBase) -> None:
		currentTimeStamp = ics.getIcsTimeByEpoch(now())
		for event in self:
			self._exportToIcsFpEvent(fp, event, currentTimeStamp)

	def exportData(self) -> dict[str, Any]:
		data = self.getData()
		for attr in self.importExportExclude:
			del data[attr]
		data = makeOrderedData(data, self.paramsOrder)
		data["events"] = []
		for eventId in self.idList:
			event = EventContainer.getEvent(self, eventId)
			modified = event.modified
			if event.uuid is None:
				event.save()
			eventData = event.getDataOrdered()
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
			self.idByUuid[event.uuid] = event.id
		return self.idByUuid

	def appendByData(self, eventData: dict[str, int]) -> Event:
		event = self.create(eventData["type"])
		event.setData(eventData)
		event.save()
		self.append(event)
		return event

	def importData(
		self,
		data: dict[str, Any],
		importMode: int = IMPORT_MODE_APPEND,
	) -> EventGroupsImportResult:
		"""The caller must call group.save() after this."""
		if not self.dataIsSet:
			self.setData(data)
			# self.clearRemoteAttrs() # FIXME
		elif importMode == IMPORT_MODE_OVERRIDE_MODIFIED:
			self.setData(data, force=True)

		res = EventGroupsImportResult()
		gid = self.id

		if importMode == IMPORT_MODE_APPEND:
			for eventData in data["events"]:
				event = self.appendByData(eventData)
				res.newEventIds.add((gid, event.id))
			return res

		idByUuid = self.loadEventIdByUuid()

		for eventData in data["events"]:
			modified = eventData.get("modified")
			uuid = eventData.get("uuid")
			if modified is None or uuid is None:
				event = self.appendByData(eventData)
				res.newEventIds.add((gid, event.id))
				continue

			eid = idByUuid.get(uuid)
			if eid is None:
				log.debug(f"appending event uuid = {uuid}")
				event = self.appendByData(eventData)
				res.newEventIds.add((gid, event.id))
				continue

			if importMode != IMPORT_MODE_OVERRIDE_MODIFIED:
				# assumed IMPORT_MODE_SKIP_MODIFIED
				log.debug(f"skipping to override existing uuid={uuid!r}, eid={eid!r}")
				continue

			event = self.getEvent(eid)
			event.setData(eventData, force=True)
			event.save()
			res.modifiedEventIds.add((gid, event.id))
			log.debug(f"overriden existing uuid={uuid!r}, eid={eid!r}")

		return res

	def _searchTimeFilter(self, conds: dict[str, Any]) -> Iterator[int]:
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

		for item in self.occur.search(time_from, time_to):
			yield item.eid

	def search(self, conds: dict[str, Any]) -> Iterator[Event]:
		conds = dict(conds)  # take a copy, we may modify it

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
							"newEventData": event.getServerData(),
						},
					)
				else:
					sinceHash = None
					for tmpEpoch, tmpHash in eventHist:
						sinceHash = tmpHash
						if tmpEpoch <= sinceEpoch:
							break
					patchList.append(
						event.createPatchByHash(sinceHash),
					)

		return patchList


@classes.group.register
class TaskList(EventGroup):
	name = "taskList"
	desc = _("Task List")
	acceptsEventTypes = (
		"task",
		"allDayTask",
	)
	# actions = EventGroup.actions + []
	sortBys = EventGroup.sortBys + (
		("start", _("Start"), True),
		("end", _("End"), True),
	)
	sortByDefault = "start"

	def getSortByValue(self, event: Event, attr: str) -> Any:
		if event.name in self.acceptsEventTypes:
			if attr == "start":
				return event.getStartEpoch()
			if attr == "end":
				return event.getEndEpoch()
		return EventGroup.getSortByValue(self, event, attr)

	def __init__(self, ident: int | None = None) -> None:
		EventGroup.__init__(self, ident)
		self.defaultDuration = (0, 1)  # (value, unit)

	def copyFrom(self, other: EventGroup) -> None:
		EventGroup.copyFrom(self, other)
		if other.name == self.name:
			self.defaultDuration = other.defaultDuration[:]

	def getData(self) -> dict[str, Any]:
		data = EventGroup.getData(self)
		data["defaultDuration"] = durationEncode(*self.defaultDuration)
		return data

	def setData(self, data: dict[str, Any]) -> None:
		EventGroup.setData(self, data)
		if "defaultDuration" in data:
			self.defaultDuration = durationDecode(data["defaultDuration"])


@classes.group.register
class NoteBook(EventGroup):
	name = "noteBook"
	desc = _("Note Book")
	acceptsEventTypes = ("dailyNote",)
	canConvertTo = (
		"yearly",
		"taskList",
	)
	# actions = EventGroup.actions + []
	sortBys = EventGroup.sortBys + (("date", _("Date"), True),)
	sortByDefault = "date"

	def getSortByValue(self, event: Event, attr: str) -> Any:
		if event.name in self.acceptsEventTypes and attr == "date":
			return event.getJd()
		return EventGroup.getSortByValue(self, event, attr)


@classes.group.register
class YearlyGroup(EventGroup):
	name = "yearly"
	desc = _("Yearly Events Group")
	acceptsEventTypes = ("yearly",)
	canConvertTo = ("noteBook",)
	params = EventGroup.params + ("showDate",)

	def __init__(self, ident: int | None = None) -> None:
		EventGroup.__init__(self, ident)
		self.showDate = True


class WeeklyScheduleItem(NamedTuple):
	name: str  # Course Name
	weekNumMode: str  # values: "odd", "even", "any"


@classes.group.register
class UniversityTerm(EventGroup):
	name = "universityTerm"
	desc = _("University Term (Semester)")
	acceptsEventTypes = (
		"universityClass",
		"universityExam",
	)
	actions = EventGroup.actions + [
		("View Weekly Schedule", "viewWeeklySchedule"),
	]
	sortBys = EventGroup.sortBys + (
		("course", _("Course"), True),
		("time", _("Time"), True),
	)
	sortByDefault = "time"
	params = EventGroup.params + ("courses",)
	paramsOrder = EventGroup.paramsOrder + (
		"classTimeBounds",
		"classesEndDate",
		"courses",
	)
	noCourseError = _(
		"Edit University Term and define some Courses before you add a Class/Exam",
	)

	def getSortByValue(self, event: Event, attr: str) -> Any:
		if event.name in self.acceptsEventTypes:
			if attr == "course":
				return event.courseId
			if attr == "time":
				if event.name == "universityClass":
					weekDay, ok = event["weekDay"]
					if not ok:
						raise RuntimeError("no weekDay rule")
					wd = weekDay.weekDayList[0]
					dayTimeRange, ok = event["dayTimeRange"]
					if not ok:
						raise RuntimeError("no dayTimeRange rule")
					return (
						(wd - core.firstWeekDay) % 7,
						dayTimeRange.getHourRange(),
					)
				if event.name == "universityExam":
					date, ok = event["date"]
					if not ok:
						raise RuntimeError("no date rule")
					dayTimeRange, ok = event["dayTimeRange"]
					if not ok:
						raise RuntimeError("no dayTimeRange rule")
					return date.getJd(), dayTimeRange.getHourRange()
		return EventGroup.getSortByValue(self, event, attr)

	def __init__(self, ident: int | None = None) -> None:
		EventGroup.__init__(self, ident)
		self.classesEndDate = getSysDate(self.calType)  # FIXME
		self.setCourses([])  # list of (courseId, courseName, courseUnits)
		self.classTimeBounds = [
			(8, 0),
			(10, 0),
			(12, 0),
			(14, 0),
			(16, 0),
			(18, 0),
		]  # FIXME

	def getClassBoundsFormatted(self) -> tuple[list[str], list[float]]:
		count = len(self.classTimeBounds)
		if count < 2:
			return
		titles = []
		firstTm = timeToFloatHour(*self.classTimeBounds[0])
		lastTm = timeToFloatHour(*self.classTimeBounds[-1])
		deltaTm = lastTm - firstTm
		for i in range(count - 1):
			tm0, tm1 = self.classTimeBounds[i : i + 2]
			titles.append(
				_("{start} to {end}", ctx="time range").format(
					start=textNumEncode(simpleTimeEncode(tm0)),
					end=textNumEncode(simpleTimeEncode(tm1)),
				),
			)
		tmfactors = [
			(timeToFloatHour(*tm1) - firstTm) / deltaTm for tm1 in self.classTimeBounds
		]
		return titles, tmfactors

	def getWeeklyScheduleData(
		self,
		currentWeekOnly: bool = False,
	) -> list[list[list[dict[str, Any]]]]:
		"""
		Returns `data` as a nested list that:
			data[weekDay][classIndex] = WeeklyScheduleItem(name, weekNumMode)
		where
			weekDay: int, in range(7)
			classIndex: int
			intervalIndex: int.
		"""
		boundsCount = len(self.classTimeBounds)
		boundsHour = [h + m / 60.0 for h, m in self.classTimeBounds]
		data = [[[] for i in range(boundsCount - 1)] for weekDay in range(7)]
		# ---
		if currentWeekOnly:
			currentJd = core.getCurrentJd()
			if (
				getAbsWeekNumberFromJd(currentJd) - getAbsWeekNumberFromJd(self.startJd)
			) % 2 == 1:
				currentWeekNumMode = "odd"
			else:
				currentWeekNumMode = "even"
			# log.debug(f"{currentWeekNumMode = }")
		else:
			currentWeekNumMode = ""
		# ---
		for event in self:
			if event.name != "universityClass":
				continue
			weekNumModeRule, ok = event["weekNumMode"]
			if not ok:
				raise RuntimeError("no weekNumMode rule")
			weekNumMode = weekNumModeRule.getData()
			if currentWeekNumMode:
				if weekNumMode not in {"any", currentWeekNumMode}:
					continue
				weekNumMode = ""
			elif weekNumMode == "any":
				weekNumMode = ""
			# ---
			weekDayRule, ok = event["weekDay"]
			if not ok:
				raise RuntimeError("no weekDay rule")
			weekDay = weekDayRule.weekDayList[0]
			dayTimeRangeRule, ok = event["dayTimeRange"]
			if not ok:
				raise RuntimeError("no dayTimeRange rule")
			h0, h1 = dayTimeRangeRule.getHourRange()
			startIndex = findNearestIndex(boundsHour, h0)
			endIndex = findNearestIndex(boundsHour, h1)
			# ---
			classData = WeeklyScheduleItem(
				name=self.getCourseNameById(event.courseId),
				weekNumMode=weekNumMode,
			)
			for i in range(startIndex, endIndex):
				data[weekDay][i].append(classData)

		return data

	def setCourses(self, courses: list[tuple[int, str, int]]) -> None:
		"""
		courses[index] == (
		courseId: int,
		courseName: str,
		units: int,
		).
		"""
		self.courses = courses
		# self.lastCourseId = max([1]+[course[0] for course in self.courses])
		# log.debug(f"setCourses: {self.lastCourseId=}")

	# def getCourseNamesDictById(self):
	# 	return dict([c[:2] for c in self.courses])

	def getCourseNameById(self, courseId: int) -> str:
		for course in self.courses:
			if course[0] == courseId:
				return course[1]
		return _("Deleted Course")

	def setDefaults(self) -> None:
		calType = calTypes.names[self.calType]
		# odd term or even term?
		jd = core.getCurrentJd()
		year, month, day = jd_to(jd, self.calType)
		md = (month, day)
		if calType == "jalali":
			# 0/07/01 to 0/11/01
			# 0/11/15 to 1/03/20
			if (1, 1) <= md < (4, 1):
				self.startJd = to_jd(year - 1, 11, 15, self.calType)
				self.classesEndDate = (year, 3, 20)
				self.endJd = to_jd(year, 4, 10, self.calType)
			elif (4, 1) <= md < (10, 1):
				self.startJd = to_jd(year, 7, 1, self.calType)
				self.classesEndDate = (year, 11, 1)
				self.endJd = to_jd(year, 11, 1, self.calType)
			else:  # md >= (10, 1)
				self.startJd = to_jd(year, 11, 15, self.calType)
				self.classesEndDate = (year + 1, 3, 1)
				self.endJd = to_jd(year + 1, 3, 20, self.calType)
		# elif calType=="gregorian":
		# 	pass

	# def getNewCourseID(self) -> int:
	# 	self.lastCourseId += 1
	# 	log.info(f"getNewCourseID: {self.lastCourseId=}")
	# 	return self.lastCourseId

	def copyFrom(self, other: EventGroup) -> None:
		EventGroup.copyFrom(self, other)
		if other.name == self.name:
			self.classesEndDate = other.classesEndDate[:]
			self.classTimeBounds = other.classTimeBounds[:]

	def getData(self) -> dict[str, Any]:
		data = EventGroup.getData(self)
		data.update(
			{
				"classTimeBounds": [hmEncode(hm) for hm in self.classTimeBounds],
				"classesEndDate": dateEncode(self.classesEndDate),
			},
		)
		return data

	def setData(self, data: dict[str, Any]) -> None:
		EventGroup.setData(self, data)
		# self.setCourses(data["courses"])
		if "classesEndDate" in data:
			try:
				self.classesEndDate = dateDecode(data["classesEndDate"])
			except ValueError:
				log.exception("")
		if "classTimeBounds" in data:
			self.classTimeBounds = sorted(
				hmDecode(hm) for hm in data["classTimeBounds"]
			)

	def afterModify(self) -> None:
		EventGroup.afterModify(self)
		for event in self:
			try:
				event.updateSummary()
			except AttributeError:  # noqa: PERF203
				pass
			else:
				event.save()


@classes.group.register
class LifetimeGroup(EventGroup):
	name = "lifetime"
	nameAlias = "lifeTime"
	desc = _("Lifetime Events Group")
	acceptsEventTypes = ("lifetime",)
	sortBys = EventGroup.sortBys + (("start", _("Start"), True),)
	params = EventGroup.params + ("showSeparateYmdInputs",)

	def getSortByValue(self, event: Event, attr: str) -> Any:
		if event.name in self.acceptsEventTypes:
			if attr == "start":
				return event.getStartJd()
			if attr == "end":
				return event.getEndJd()
		return EventGroup.getSortByValue(self, event, attr)

	def __init__(self, ident: int | None = None) -> None:
		self.showSeparateYmdInputs = False
		EventGroup.__init__(self, ident)

	def setData(self, data: dict[str, Any]) -> None:
		if "showSeperatedYmdInputs" in data:
			# misspell in < 3.1.x
			data["showSeparateYmdInputs"] = data["showSeperatedYmdInputs"]
		if "showSeparatedYmdInputs" in data:
			data["showSeparateYmdInputs"] = data["showSeparatedYmdInputs"]
		EventGroup.setData(self, data)

	def setDefaults(self) -> None:
		# only show in time line
		self.showInDCal = False
		self.showInWCal = False
		self.showInMCal = False
		self.showInStatusIcon = False


@classes.group.register
class LargeScaleGroup(EventGroup):
	name = "largeScale"
	desc = _("Large Scale Events Group")
	acceptsEventTypes = ("largeScale",)
	sortBys = EventGroup.sortBys + (
		("start", _("Start"), True),
		("end", _("End"), True),
	)
	sortByDefault = "start"

	def getSortByValue(self, event: Event, attr: str) -> Any:
		if event.name in self.acceptsEventTypes:
			if attr == "start":
				return event.start * event.scale
			if attr == "end":
				return event.getEnd() * event.scale
		return EventGroup.getSortByValue(self, event, attr)

	def __init__(self, ident: int | None = None) -> None:
		self.scale = 1  # 1, 1000, 1000**2, 1000**3
		EventGroup.__init__(self, ident)

	def setDefaults(self) -> None:
		self.startJd = 0
		self.endJd = self.startJd + self.scale * 9999
		# only show in time line
		self.showInDCal = False
		self.showInWCal = False
		self.showInMCal = False
		self.showInStatusIcon = False

	def copyFrom(self, other: EventGroup) -> None:
		EventGroup.copyFrom(self, other)
		if other.name == self.name:
			self.scale = other.scale

	def getData(self) -> dict[str, Any]:
		data = EventGroup.getData(self)
		data["scale"] = self.scale
		return data

	def setData(self, data: dict[str, Any]) -> None:
		EventGroup.setData(self, data)
		with suppress(KeyError):
			self.scale = data["scale"]

	def getStartValue(self) -> float:
		return jd_to(self.startJd, self.calType)[0] // self.scale

	def getEndValue(self) -> float:
		return jd_to(self.endJd, self.calType)[0] // self.scale

	def setStartValue(self, start: float) -> None:
		self.startJd = int(
			to_jd(
				start * self.scale,
				1,
				1,
				self.calType,
			),
		)

	def setEndValue(self, end: float) -> None:
		self.endJd = int(
			to_jd(
				end * self.scale,
				1,
				1,
				self.calType,
			),
		)
