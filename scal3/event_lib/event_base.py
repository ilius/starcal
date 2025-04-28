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

from os.path import join
from time import time as now
from typing import TYPE_CHECKING

import mytz
from scal3 import core
from scal3.cal_types import calTypes
from scal3.event_lib import state
from scal3.locale_man import tr as _
from scal3.path import pixDir
from scal3.s_object import (
	SObj,
	SObjBinaryModel,
)
from scal3.time_utils import durationDecode, durationEncode

from .exceptions import BadEventFile
from .icon import WithIcon, iconAbsToRelativelnData
from .objects import HistoryEventObjBinaryModel
from .occur import JdOccurSet
from .register import classes
from .rule_container import RuleContainer

if TYPE_CHECKING:
	from collections.abc import Callable, Iterator, Sequence
	from typing import Any

	from scal3.filesystem import FileSystem

	from .event_container import EventContainer
	from .groups import EventGroup
	from .occur import OccurSet
	from .rules import EventRule


__all__ = ["Event", "eventsDir"]

eventsDir = join("event", "events")


# Should not be registered, or instantiate directly
@classes.event.setMain
class Event(HistoryEventObjBinaryModel, RuleContainer, WithIcon):
	name = "custom"  # or "event" or "" FIXME
	desc = _("Custom Event")
	iconName = ""
	# requiredNotifiers = ()  # FIXME: needed?
	readOnly = False
	isAllDay = False
	isSingleOccur = False
	basicParams = (
		"uuid",
		# "modified",
		"remoteIds",
		"lastMergeSha1",  # [localSha1, remoteSha1]
		"notifiers",  # FIXME
	)
	params = RuleContainer.params + (
		"uuid",
		"icon",
		"summary",
		"description",
	)
	paramsOrder = RuleContainer.paramsOrder + (
		"uuid",
		"type",
		"calType",
		"summary",
		"description",
		"rules",
		"notifiers",
		"notifyBefore",
		"remoteIds",
		"lastMergeSha1",
		"modified",
	)

	@classmethod
	def getFile(cls, ident: int) -> str:
		return join(eventsDir, f"{ident}.json")

	@classmethod
	def iterFiles(cls, fs: FileSystem) -> Iterator[str]:
		for ident in range(1, state.lastIds.event + 1):
			fpath = cls.getFile(ident)
			if not fs.isfile(fpath):
				continue
			yield fpath

	@classmethod
	def getSubclass(cls, typeName: str) -> type:
		return classes.event.byName[typeName]

	@classmethod
	def getDefaultIcon(cls) -> str:
		return (
			join(
				pixDir,
				"event",
				cls.iconName + ".png",
			)
			if cls.iconName
			else ""
		)

	def getPath(self) -> str:
		if self.parent is None:
			raise RuntimeError("getPath: parent is None")
		path = SObj.getPath(self)
		if len(path) != 2:
			raise RuntimeError(f"getPath: unexpected {path=}")
		return path

	def getRevision(self, revHash: str) -> Event:
		return SObjBinaryModel.getRevision(self, revHash, self.id)

	def __bool__(self) -> bool:
		return bool(self.rulesOd)  # FIXME

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}(id={self.id!r})"

	def __str__(self) -> str:
		return f"{self.__class__.__name__}(id={self.id!r}, summary={self.summary!r})"

	def icsUID(self) -> str:
		import socket

		event_st = core.compressLongInt(hash(str(self.getData())))
		time_st = core.getCompactTime()
		host = socket.gethostname()
		return event_st + "_" + time_st + "@" + host

	def __init__(
		self,
		ident: int | None = None,
		parent: EventContainer | None = None,
	) -> None:
		if ident is None:
			self.id = None
		else:
			self.setId(ident)
		self.fs = None
		self.uuid = None
		self.parent = parent
		if parent is not None:
			self.calType = parent.calType
		else:
			self.calType = calTypes.primary
		self.icon = self.__class__.getDefaultIcon()
		self.summary = self.desc  # + " (" + _(self.id) + ")"  # FIXME
		self.description = ""
		self.files = []
		# ------
		RuleContainer.__init__(self)
		self.timeZoneEnable = not self.isAllDay
		self.notifiers = []
		self.notifyBefore = (30, 60)  # (value, unit) like DurationEventRule
		# self.snoozeTime = (5, 60)  # (value, unit) like DurationEventRule, FIXME
		self.addRequirements()
		self.setDefaults(group=parent)
		# ------
		self.modified = now()  # FIXME
		self.remoteIds = None
		# remoteIds is (accountId, groupId, eventId)
		# 		   OR (accountId, groupId, eventId, sha1)
		# remote groupId and eventId both can be integer or string
		# (depending on remote account type)

		# self.lastMergeSha1 is [localSha1, remoteSha1] or None
		self.lastMergeSha1 = None

	def create(self, ruleName: str) -> EventRule:
		rule = classes.rule.byName[ruleName](self)
		rule.fs = self.fs
		return rule

	def getShownDescription(self) -> str:
		if not self.description:
			return ""
		if self.parent is not None:
			showFull = self.parent.showFullEventDesc
		else:
			showFull = False
		if showFull:
			return self.description
		return self.description.split("\n")[0]

	def afterModify(self) -> None:
		if self.id is None:
			self.setId()
		self.modified = now()  # FIXME
		# self.parent.eventsModified = self.modified

	def afterAddedToGroup(self) -> None:
		if not (self.parent and self.id in self.parent.idList):
			self.rulesHash = ""
			return

		rulesHash = self.getRulesHash()
		if self.notifiers or rulesHash != self.rulesHash:
			self.parent.updateOccurrenceEvent(self)
			self.rulesHash = rulesHash

	def getNotifyBeforeSec(self) -> int:
		return self.notifyBefore[0] * self.notifyBefore[1]

	def getNotifyBeforeMin(self) -> int:
		return int(self.getNotifyBeforeSec() / 60)

	def setDefaults(self, group: EventGroup | None = None) -> None:
		"""
		Sets default values that depends on event type and group type
		as well as common parameters, like those are set in __init__
		should call this method from parent event class.
		"""
		if group:
			self.timeZone = group.getTimeZoneStr()
			if group.icon:  # and not self.icon FIXME
				self.icon = group.icon

	def getInfo(self) -> str:
		calType = self.calType
		calType, ok = calTypes[calType]
		if not ok:
			raise RuntimeError(f"cal type '{calType}' not found")
		rulesDict = self.rulesOd.copy()
		lines = [
			_("Type") + ": " + self.desc,
			_("Calendar Type") + ": " + calType.desc,
			_("Summary") + ": " + self.getSummary(),
			_("Description") + ": " + self.description,
		] + [rule.getInfo() for rule in rulesDict.values()]
		# "notifiers",
		# "notifyBefore",
		# "remoteIds",
		# "lastMergeSha1",
		# "modified",
		return "\n".join(lines)

	# def addRequirements(self):
	# 	RuleContainer.addRequirements(self)
	# 	notifierNames = (notifier.name for notifier in self.notifiers)
	# 	for name in self.requiredNotifiers:
	# 		if not name in notifierNames:
	# 			self.notifiers.append(classes.notifier.byName[name](self))

	def loadFiles(self) -> None:
		self.files = []
		# if os.path.isdir(self.filesDir):
		# 	for fname in self.fs.listdir(self.filesDir):
		# 		# FIXME
		# 		if isfile(join(self.filesDir, fname)) and not fname.endswith("~"):
		# 			self.files.append(fname)

	# def getUrlForFile(self, fname):
	# 	return "file:" + os.sep*2 + self.filesDir + os.sep + fname

	def getFilesUrls(self) -> list[str]:
		baseUrl = self.getUrlForFile("")
		return [
			(
				baseUrl + fname,
				_("io.TextIOBase") + ": " + fname,
			)
			for fname in self.files
		]

	def getSummary(self) -> str:
		return self.summary

	def getDescription(self) -> str:
		return self.description

	def getTextParts(self, showDesc: bool = True) -> Sequence[str]:
		summary = self.getSummary()
		# --
		if self.timeZoneEnable and self.timeZone and mytz.gettz(self.timeZone) is None:
			invalidTZ = _("Invalid Time Zone: {timeZoneName}").format(
				timeZoneName=self.timeZone,
			)
			summary = "(" + invalidTZ + ")" + summary
		# ----
		description = self.getDescription()
		if showDesc and description:
			if self.parent is not None:
				sep = self.parent.eventTextSep
			else:
				sep = core.eventTextSep
			return (summary, sep, description)

		return (summary,)

	def getText(self, showDesc: bool = True) -> str:
		return "".join(self.getTextParts(showDesc))

	def setId(self, ident: int | None = None) -> None:
		if ident is None or ident < 0:
			ident = state.lastIds.event + 1  # FIXME
			state.lastIds.event = ident
		elif ident > state.lastIds.event:
			state.lastIds.event = ident
		self.id = ident
		self.file = self.getFile(self.id)
		# self.filesDir = join(self.dir, "files")
		self.loadFiles()

	def invalidate(self) -> None:
		# make sure it can't be written to file again, it's about to be deleted
		self.id = None
		self.file = ""

	def save(self) -> None:
		if self.id is None:
			self.setId()
		# self.fs.makeDir(self.dir)
		HistoryEventObjBinaryModel.save(self)

	def copyFrom(self, other: Event, exact: bool = False) -> None:
		HistoryEventObjBinaryModel.copyFrom(self, other)
		self.calType = other.calType
		self.notifyBefore = other.notifyBefore[:]
		# self.files = other.files[:]
		self.notifiers = other.notifiers[:]  # FIXME
		self.copyRulesFrom(other)
		self.addRequirements()
		# ----
		# copy dates between different rule types in different event types
		if self.name != other.name:
			jd = other.getJd()
			if jd is not None:
				if exact:
					self.setJdExact(jd)
				else:
					self.setJd(jd)

	def getData(self) -> dict[str, Any]:
		data = HistoryEventObjBinaryModel.getData(self)
		data.update(
			{
				"type": self.name,
				"calType": calTypes.names[self.calType],
				"rules": self.getRulesData(),
				"notifiers": self.getNotifiersData(),
				"notifyBefore": durationEncode(*self.notifyBefore),
			},
		)
		iconAbsToRelativelnData(data)
		return data

	def setData(self, data: dict[str, Any]) -> None:
		HistoryEventObjBinaryModel.setData(self, data)
		if self.remoteIds:
			self.remoteIds = tuple(self.remoteIds)
		if "id" in data:
			self.setId(data["id"])
		if "calType" in data:
			calType = data["calType"]
			try:
				self.calType = calTypes.names.index(calType)
			except ValueError:
				raise ValueError(f"Invalid calType: '{calType}'") from None
		self.clearRules()
		if "rules" in data:
			try:
				self.setRulesData(data["rules"])
			except BadEventFile:
				log.exception(f"{data=}")
		self.notifiers = []
		if "notifiers" in data:
			for notifierName, notifierData in data["notifiers"]:
				notifier = classes.notifier.byName[notifierName](self)
				notifier.setData(notifierData)
				self.notifiers.append(notifier)
		if "notifyBefore" in data:
			self.notifyBefore = durationDecode(data["notifyBefore"])
		self.iconRelativeToAbsInObj()

	def getNotifiersData(self) -> list[tuple[str, dict[str, Any]]]:
		return [(notifier.name, notifier.getData()) for notifier in self.notifiers]

	def getNotifiersDict(self) -> dict[str, dict[str, Any]]:
		return dict(self.getNotifiersData())

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSet:
		"""StartJd and endJd are float jd."""
		# cache Occurrences  # FIXME
		rules = list(self.rulesOd.values())
		if not rules:
			return JdOccurSet()
		occur = rules[0].calcOccurrence(startJd, endJd, self)
		for rule in rules[1:]:
			try:
				ruleStartJd = occur.getStartJd()
			except NotImplementedError:
				ruleStartJd = startJd
			else:
				if ruleStartJd is None:
					ruleStartJd = startJd
			try:
				ruleEndJd = occur.getEndJd()
			except NotImplementedError:
				ruleEndJd = endJd
			else:
				if ruleEndJd is None:
					ruleEndJd = endJd
			occur = occur.intersection(
				rule.calcOccurrence(
					ruleStartJd,
					ruleEndJd,
					self,
				),
			)
		occur.event = self
		return occur  # FIXME

	def calcEventOccurrence(self) -> OccurSet:
		return self.calcEventOccurrenceIn(self.parent.startJd, self.parent.endJd)

	# FIXME: too tricky!
	# def calcFirstOccurrenceAfterJd(self, startJd):

	def checkNotify(self, finishFunc: Callable) -> None:
		"""To be called from notification scheduler."""
		if not self.parent:
			return
		firstOccur: tuple[int, int] | None = self.parent.occur.getFirstOfEvent(self.id)
		if firstOccur is None:
			return
		start, end = firstOccur
		tm = now()
		if end < tm:  # TODO: add a self.parent.notificationMaxDelay
			log.debug(f"checkNotify: event has past, event={self}")
			return
		if start > tm + self.getNotifyBeforeSec():
			log.debug(f"checkNotify: event notif time has not reached, event={self}")
			return
		self.notify(finishFunc)

	def notify(self, finishFunc: Callable) -> None:
		# FIXME: get rid of self.n ??
		self.n = len(self.notifiers)

		def notifierFinishFunc() -> None:
			self.n -= 1
			if self.n <= 0:
				try:
					finishFunc()
				except Exception:
					log.exception("")

		for notifier in self.notifiers:
			print(f"notifier.notify: {notifier=}")
			notifier.notify(notifierFinishFunc)

	def getIcsData(self, prettyDateTime: bool = False) -> None:  # noqa: ARG002, PLR6301
		# FIXME
		return None

	def setIcsData(self, data: dict[str, Any]) -> bool:  # noqa: ARG002, PLR6301
		# if "T" in data["DTSTART"]:
		# 	return False
		# if "T" in data["DTEND"]:
		# 	return False
		# startJd = ics.getJdByIcsDate(data["DTSTART"])
		# endJd = ics.getJdByIcsDate(data["DTEND"])
		# if "RRULE" in data:
		# 	rrule = dict(ics.splitIcsValue(data["RRULE"]))
		# 	if rrule["FREQ"] == "YEARLY":
		# 		y0, m0, d0 = jd_to(startJd, self.calType)
		# 		y1, m1, d1 = jd_to(endJd, self.calType)
		# 		if y0 != y1:  # FIXME
		# 			return False
		# 		yr = self.getAddRule("year")
		# 		interval = int(rrule.get("INTERVAL", 1)).

		# 	elif rrule["FREQ"] == "MONTHLY":
		# 		pass
		# 	elif rrule["FREQ"] == "WEEKLY":
		# 		pass
		return False

	def changeCalType(self, calType: int) -> bool:
		backupRulesOd = RuleContainer.copyRulesDict(self.rulesOd)
		if calType != self.calType:
			for rule in self.rulesOd.values():
				if not rule.changeCalType(calType):
					log.info(
						f"changeCalType: failed because of rule {rule.name}={rule}",
					)
					self.rulesOd = backupRulesOd
					return False
			self.calType = calType
		return True

	def getStartJd(self) -> int:  # FIXME
		start, ok = self["start"]
		if ok:
			return start.getJd()
		date, ok = self["date"]
		if ok:
			return date.getJd()
		return self.parent.startJd

	def getEndJd(self) -> int:  # FIXME
		end, ok = self["end"]
		if ok:
			return end.getJd()
		date, ok = self["date"]
		if ok:
			return date.getJd()
		return self.parent.endJd

	def getStartEpoch(self) -> int:
		start, ok = self["start"]
		if ok:
			return start.getEpoch()
		date, ok = self["date"]
		if ok:
			return date.getEpoch()
		return self.parent.getStartEpoch()

	def getEndEpoch(self) -> int:
		end, ok = self["end"]
		if ok:
			return end.getEpoch()
		date, ok = self["date"]
		if ok:
			return date.getEpoch()
		return self.parent.getEndEpoch()

	def getJd(self) -> int:
		return self.getStartJd()

	def setJd(self, jd: int) -> None:  # noqa: ARG002, PLR6301
		return None

	def setJdExact(self, jd: int) -> None:
		return self.setJd(jd)

	def getServerData(self) -> dict[str, Any]:
		data = {
			"summary": self.getSummary(),
			"description": self.getDescription(),
			"calType": calTypes.names[self.calType],
			"icon": self.getIcon(),
			"timeZone": self.timeZone,
			"timeZoneEnable": self.timeZoneEnable,
		}
		iconAbsToRelativelnData(data)
		return data

	def createPatchByHash(self, oldHash: str) -> dict[str, Any]:
		oldEvent = self.getRevision(oldHash)
		patch = {
			"eventId": self.id,
			"eventType": oldEvent.name,
			"action": "modify",
		}
		if oldEvent.name != self.name:
			patch["newEventType"] = self.name

		oldData = oldEvent.getServerData()
		newData = self.getServerData()

		items = []
		for fieldName, newValue in newData.items():
			oldValue = oldData.get(fieldName, None)
			if oldValue != newValue:
				items.append(
					{
						"fieldName": fieldName,
						"oldValue": oldValue,
						"newValue": newValue,
					},
				)
		patch["items"] = items

		return patch
