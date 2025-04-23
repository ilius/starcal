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

from .occur import IntervalOccurSet, JdOccurSet
from .rules import DurationEventRule, EndEventRule

if TYPE_CHECKING:
	from collections.abc import Callable

	from .occur import OccurSet
	from .rules import EventRule

from os.path import join
from time import localtime
from time import time as now

import mytz
from scal3 import core, ics
from scal3.cal_types import (
	GREGORIAN,
	calTypes,
	getSysDate,
	jd_to,
	to_jd,
)
from scal3.date_utils import jwday
from scal3.event_lib import state
from scal3.locale_man import getMonthName
from scal3.locale_man import tr as _
from scal3.path import pixDir
from scal3.s_object import (
	BsonHistObj,
	FileSystem,
	SObj,
)
from scal3.time_utils import (
	durationDecode,
	durationEncode,
	getFloatJdFromEpoch,
	jsonTimeFromEpoch,
	roundEpochToDay,
)
from scal3.utils import iceil, ifloor

from .icon import (
	WithIcon,
	iconAbsToRelativelnData,
	iconRelativeToAbsInObj,
)
from .objects import BsonHistEventObj
from .register import classes
from .rule_container import RuleContainer

__all__ = ["Event", "eventsDir"]
eventsDir = join("event", "events")

dayLen = 24 * 3600
icsMinStartYear = 1970
# icsMaxEndYear = 2050


# Should not be registered, or instantiate directly
@classes.event.setMain
class Event(BsonHistEventObj, RuleContainer, WithIcon):
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
	def getFile(cls, _id):
		return join(eventsDir, f"{_id}.json")

	@classmethod
	def iterFiles(cls, fs: FileSystem):
		for _id in range(1, state.lastIds.event + 1):
			fpath = cls.getFile(_id)
			if not fs.isfile(fpath):
				continue
			yield fpath

	@classmethod
	def getSubclass(cls, _type):
		return classes.event.byName[_type]

	@classmethod
	def getDefaultIcon(cls):
		return (
			join(
				pixDir,
				"event",
				cls.iconName + ".png",
			)
			if cls.iconName
			else ""
		)

	def getPath(self):
		if self.parent is None:
			raise RuntimeError("getPath: parent is None")
		path = SObj.getPath(self)
		if len(path) != 2:
			raise RuntimeError(f"getPath: unexpected {path=}")
		return path

	def getRevision(self, revHash):
		return BsonHistObj.getRevision(self, revHash, self.id)

	def __bool__(self):
		return bool(self.rulesOd)  # FIXME

	def __repr__(self):
		return f"{self.__class__.__name__}(id={self.id!r})"

	def __str__(self) -> str:
		return f"{self.__class__.__name__}(id={self.id!r}, summary={self.summary!r})"

	def __init__(self, _id=None, parent=None):
		if _id is None:
			self.id = None
		else:
			self.setId(_id)
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

	def getShownDescription(self):
		if not self.description:
			return ""
		if self.parent is not None:
			showFull = self.parent.showFullEventDesc
		else:
			showFull = False
		if showFull:
			return self.description
		return self.description.split("\n")[0]

	def afterModify(self):
		if self.id is None:
			self.setId()
		self.modified = now()  # FIXME
		# self.parent.eventsModified = self.modified

	def afterAddedToGroup(self):
		if not (self.parent and self.id in self.parent.idList):
			self.rulesHash = ""
			return

		rulesHash = self.getRulesHash()
		if self.notifiers or rulesHash != self.rulesHash:
			self.parent.updateOccurrenceEvent(self)
			self.rulesHash = rulesHash

	def getNotifyBeforeSec(self):
		return self.notifyBefore[0] * self.notifyBefore[1]

	def getNotifyBeforeMin(self):
		return int(self.getNotifyBeforeSec() / 60)

	def setDefaults(self, group=None):
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

	def loadFiles(self):
		self.files = []
		# if os.path.isdir(self.filesDir):
		# 	for fname in self.fs.listdir(self.filesDir):
		# 		# FIXME
		# 		if isfile(join(self.filesDir, fname)) and not fname.endswith("~"):
		# 			self.files.append(fname)

	# def getUrlForFile(self, fname):
	# 	return "file:" + os.sep*2 + self.filesDir + os.sep + fname

	def getFilesUrls(self):
		baseUrl = self.getUrlForFile("")
		return [
			(
				baseUrl + fname,
				_("io.TextIOBase") + ": " + fname,
			)
			for fname in self.files
		]

	def getSummary(self):
		return self.summary

	def getDescription(self):
		return self.description

	def getTextParts(self, showDesc=True):
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

	def getText(self, showDesc=True):
		return "".join(self.getTextParts(showDesc))

	def setId(self, id_=None):
		if id_ is None or id_ < 0:
			id_ = state.lastIds.event + 1  # FIXME
			state.lastIds.event = id_
		elif id_ > state.lastIds.event:
			state.lastIds.event = id_
		self.id = id_
		self.file = self.getFile(self.id)
		# self.filesDir = join(self.dir, "files")
		self.loadFiles()

	def invalidate(self):
		# make sure it can't be written to file again, it's about to be deleted
		self.id = None
		self.file = ""

	def save(self):
		if self.id is None:
			self.setId()
		# self.fs.makeDir(self.dir)
		BsonHistEventObj.save(self)

	def copyFrom(self, other, exact=False):
		BsonHistEventObj.copyFrom(self, other)
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

	def getData(self):
		data = BsonHistEventObj.getData(self)
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

	def setData(self, data) -> None:
		BsonHistEventObj.setData(self, data)
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
			self.setRulesData(data["rules"])
		self.notifiers = []
		if "notifiers" in data:
			for notifierName, notifierData in data["notifiers"]:
				notifier = classes.notifier.byName[notifierName](self)
				notifier.setData(notifierData)
				self.notifiers.append(notifier)
		if "notifyBefore" in data:
			self.notifyBefore = durationDecode(data["notifyBefore"])
		iconRelativeToAbsInObj(self)

	def getNotifiersData(self):
		return [(notifier.name, notifier.getData()) for notifier in self.notifiers]

	def getNotifiersDict(self):
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

	def calcEventOccurrence(self):
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

		def notifierFinishFunc():
			self.n -= 1
			if self.n <= 0:
				try:
					finishFunc()
				except Exception:
					log.exception("")

		for notifier in self.notifiers:
			print(f"notifier.notify: {notifier=}")
			notifier.notify(notifierFinishFunc)

	def getIcsData(self, prettyDateTime=False):  # noqa: ARG002, PLR6301
		# FIXME
		return None

	def setIcsData(self, data):  # noqa: ARG002, PLR6301
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

	def changeCalType(self, calType) -> bool:
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

	def getStartEpoch(self):  # FIXME
		start, ok = self["start"]
		if ok:
			return start.getEpoch()
		date, ok = self["date"]
		if ok:
			return date.getEpoch()
		return self.parent.getStartEpoch()

	def getEndEpoch(self):  # FIXME
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

	def getServerData(self):
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

	def createPatchByHash(self, oldHash):
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


class SingleStartEndEvent(Event):
	isSingleOccur = True

	def setStartEpoch(self, epoch):
		return self.getAddRule("start").setEpoch(epoch)

	def setEndEpoch(self, epoch):
		return self.getAddRule("end").setEpoch(epoch)

	def setJd(self, jd: int) -> None:
		return self.getAddRule("start").setJd(jd)

	def setJdExact(self, jd: int) -> None:
		self.getAddRule("start").setJdExact(jd)
		self.getAddRule("end").setJdExact(jd + 1)

	def getIcsData(self, prettyDateTime=False):
		return [
			(
				"DTSTART",
				ics.getIcsTimeByEpoch(
					self.getStartEpoch(),
					prettyDateTime,
				),
			),
			(
				"DTEND",
				ics.getIcsTimeByEpoch(
					self.getEndEpoch(),
					prettyDateTime,
				),
			),
			("TRANSP", "OPAQUE"),
			("CATEGORIES", self.name),  # FIXME
		]

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSet:
		return IntervalOccurSet.newFromStartEnd(
			max(self.getEpochFromJd(startJd), self.getStartEpoch()),
			min(self.getEpochFromJd(endJd), self.getEndEpoch()),
		)


@classes.event.register
class TaskEvent(SingleStartEndEvent):
	# overwrites getEndEpoch from Event
	# overwrites setEndEpoch from SingleStartEndEvent
	# overwrites setJdExact from SingleStartEndEvent
	# Methods neccessery for modifying event by hand in timeline:
	#   getStartEpoch, getEndEpoch, modifyStart, modifyEnd, modifyPos
	name = "task"
	desc = _("Task")
	iconName = "task"
	requiredRules = ("start",)
	supportedRules = (
		"start",
		"end",
		"duration",
	)
	isAllDay = False

	def getServerData(self):
		try:
			durationUnit = self["duration"].unit
		except KeyError:
			durationUnit = 0

		data = Event.getServerData(self)
		data.update(
			{
				"startTime": jsonTimeFromEpoch(self["start"].getEpoch()),
				"endTime": jsonTimeFromEpoch(self.getEndEpoch()),
				"durationUnit": durationUnit,
			},
		)
		return data

	def _setDefaultDuration(self, group):
		if group is None or group.name != "taskList":
			self.setEnd("duration", 1, 3600)
			return

		value, unit = group.defaultDuration
		if value == 0:
			value, unit = 1, 3600
		self.setEnd("duration", value, unit)

	def setDefaults(self, group=None):
		Event.setDefaults(self, group=group)
		self.setStart(
			getSysDate(self.calType),
			tuple(localtime()[3:6]),
		)
		self._setDefaultDuration(group)

	def setJdExact(self, jd: int) -> None:
		self.getAddRule("start").setJdExact(jd)
		self.setEnd("duration", 24, 3600)

	def setStart(self, date, dayTime):
		start, ok = self["start"]
		if not ok:
			raise KeyError('rule "start" not found')
		start.date = date
		start.time = dayTime

	def setEnd(self, endType, *values):
		self.removeSomeRuleTypes("end", "duration")
		if endType == "date":
			rule = EndEventRule(self)
			rule.date, rule.time = values
		elif endType == "epoch":
			rule = EndEventRule(self)
			rule.setEpoch(values[0])
		elif endType == "duration":
			rule = DurationEventRule(self)
			rule.value, rule.unit = values
		else:
			raise ValueError(f"invalid {endType=}")
		self.addRule(rule)

	def getStart(self):
		start, ok = self["start"]
		if not ok:
			raise KeyError('rule "start" not found')
		return (start.date, start.time)

	def getEnd(self):
		end, ok = self["end"]
		if ok:
			return ("date", (end.date, end.time))
		duration, ok = self["duration"]
		if ok:
			return ("duration", (duration.value, duration.unit))
		raise ValueError("no end date neither duration specified for task")

	def getEndEpoch(self):
		end, ok = self["end"]
		if ok:
			return end.getEpoch()
		duration, ok = self["duration"]
		if ok:
			start, ok = self["start"]
			if ok:
				return start.getEpoch() + duration.getSeconds()
			raise RuntimeError("found duration rule without start rule")
		raise ValueError("no end date neither duration specified for task")

	def setEndEpoch(self, epoch):
		end, ok = self["end"]
		if ok:
			end.setEpoch(epoch)
			return
		duration, ok = self["duration"]
		if ok:
			start, ok = self["start"]
			if ok:
				duration.setSeconds(epoch - start.getEpoch())
			else:
				raise RuntimeError("found duration rule without start rule")
			return
		raise ValueError("no end date neither duration specified for task")

	def modifyPos(self, newStartEpoch):
		start, ok = self["start"]
		if not ok:
			raise KeyError
		end, ok = self["end"]
		if ok:
			end.setEpoch(end.getEpoch() + newStartEpoch - start.getEpoch())
		start.setEpoch(newStartEpoch)

	def modifyStart(self, newStartEpoch):
		start, ok = self["start"]
		if not ok:
			raise KeyError
		duration, ok = self["duration"]
		if ok:
			duration.value -= (newStartEpoch - start.getEpoch()) / duration.unit
		start.setEpoch(newStartEpoch)

	def modifyEnd(self, newEndEpoch):
		end, ok = self["end"]
		if ok:
			end.setEpoch(newEndEpoch)
		else:
			duration, ok = self["duration"]
			if ok:
				duration.value = (newEndEpoch - self.getStartEpoch()) / duration.unit
			else:
				raise RuntimeError("no end rule nor duration rule")

	def copyFrom(self, other, *a, **kw):
		Event.copyFrom(self, other, *a, **kw)
		myStart, ok = self["start"]
		if not ok:
			raise KeyError
		# --
		if other.name == self.name:
			endType, values = other.getEnd()
			self.setEnd(endType, *values)
		elif other.name == "dailyNote":
			myStart.time = (0, 0, 0)
			self.setEnd("duration", 24, 3600)
		elif other.name == "allDayTask":
			self.removeSomeRuleTypes("end", "duration")
			self.copySomeRuleTypesFrom(other, "start", "end", "duration")
		else:
			otherDayTime, ok = other["dayTime"]
			if ok:
				myStart.time = otherDayTime.dayTime

	def setIcsData(self, data):
		self.setStartEpoch(ics.getEpochByIcsTime(data["DTSTART"]))
		self.setEndEpoch(ics.getEpochByIcsTime(data["DTEND"]))  # FIXME
		return True


@classes.event.register
class AllDayTaskEvent(SingleStartEndEvent):
	# overwrites getEndEpoch from SingleStartEndEvent
	name = "allDayTask"
	desc = _("All-Day Task")
	iconName = "task"
	requiredRules = ("start",)
	supportedRules = (
		"start",
		"end",
		"duration",
	)
	isAllDay = True

	def getServerData(self):
		try:
			self["duration"]
		except KeyError:
			durationEnable = False
		else:
			durationEnable = True

		data = Event.getServerData(self)
		data.update(
			{
				"startJd": self["start"].getJd(),
				"endJd": self.getEndJd(),
				"durationEnable": durationEnable,
			},
		)
		return data

	def setJd(self, jd: int) -> None:
		self.getAddRule("start").setJdExact(jd)

	def setStartDate(self, date):
		self.getAddRule("start").setDate(date)

	def setJdExact(self, jd: int) -> None:
		self.setJd(jd)
		self.setEnd("duration", 1)

	def setDefaults(self, group=None):
		Event.setDefaults(self, group=group)
		jd = core.getCurrentJd()
		self.setJd(jd)
		self.setEnd("duration", 1)
		# if group and group.name == "taskList":
		# 	value, unit = group.defaultAllDayDuration
		# 	if value > 0:
		# 		self.setEnd("duration", value)

	def setEnd(self, endType, value):
		self.removeSomeRuleTypes("end", "duration")
		if endType == "date":
			rule = EndEventRule(self)
			rule.setDate(value)
		elif endType == "jd":
			rule = EndEventRule(self)
			rule.setJd(value)
		elif endType == "epoch":
			rule = EndEventRule(self)
			rule.setJd(self.getJdFromEpoch(value))
		elif endType == "duration":
			rule = DurationEventRule(self)
			rule.value = value
			rule.unit = dayLen
		else:
			raise ValueError(f"invalid {endType=}")
		self.addRule(rule)

	def getEnd(self):
		end, ok = self["end"]
		if ok:
			return ("date", end.date)
		duration, ok = self["duration"]
		if ok:
			return ("duration", duration.value)
		raise ValueError("no end date neither duration specified for task")

	def getEndJd(self) -> int:
		end, ok = self["end"]
		if ok:
			# assert isinstance(end.getJd(), int)
			return end.getJd()
		duration, ok = self["duration"]
		if ok:
			start, ok = self["start"]
			if not ok:
				raise RuntimeError("no start rule")
			# assert isinstance(start.getJd(), int)
			return start.getJd() + duration.getSeconds() // dayLen
		raise ValueError("no end date neither duration specified for task")

	def getEndEpoch(self):
		# if not isinstance(self.getEndJd(), int):
		# 	raise TypeError(f"{self}.getEndJd() returned non-int: {self.getEndJd()}")
		return self.getEpochFromJd(self.getEndJd())

	# def setEndJd(self, jd):
	# 	self.getAddRule("end").setJdExact(jd)

	def setEndJd(self, jd):
		end, ok = self["end"]
		if ok:
			end.setJd(jd)
			return
		duration, ok = self["duration"]
		if ok:
			start, ok = self["start"]
			if ok:
				duration.setSeconds(dayLen * (jd - start.getJd()))
				return
		raise ValueError("no end date neither duration specified for task")

	def getIcsData(self, prettyDateTime=False):
		return [
			("DTSTART", ics.getIcsDateByJd(self.getJd(), prettyDateTime)),
			("DTEND", ics.getIcsDateByJd(self.getEndJd(), prettyDateTime)),
			("TRANSP", "OPAQUE"),
			("CATEGORIES", self.name),  # FIXME
		]

	def setIcsData(self, data):
		self.setJd(ics.getJdByIcsDate(data["DTSTART"]))
		self.setEndJd(ics.getJdByIcsDate(data["DTEND"]))  # FIXME
		return True

	def copyFrom(self, other):
		SingleStartEndEvent.copyFrom(self, other)
		if other.name == self.name:
			self.setEnd(*other.getEnd())


@classes.event.register
class DailyNoteEvent(Event):
	name = "dailyNote"
	desc = _("Daily Note")
	isSingleOccur = True
	iconName = "note"
	requiredRules = ("date",)
	supportedRules = ("date",)
	isAllDay = True

	def getServerData(self):
		data = Event.getServerData(self)
		data.update(
			{
				"jd": self.getJd(),
			},
		)
		return data

	def getDate(self):
		rule, ok = self["date"]
		if ok:
			return rule.date
		return None

	def setDate(self, year, month, day):
		rule, ok = self["date"]
		if not ok:
			raise KeyError("no date rule")
		rule.date = (year, month, day)

	def getJd(self) -> int:
		rule, ok = self["date"]
		if ok:
			return rule.getJd()
		return None

	def setJd(self, jd: int) -> None:
		rule, ok = self["date"]
		if ok:
			return rule.setJd(jd)
		return None

	def setDefaults(self, group=None):
		Event.setDefaults(self, group=group)
		self.setDate(*getSysDate(self.calType))

	# startJd and endJd can be float jd
	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSet:
		jd = self.getJd()
		return JdOccurSet(
			[jd] if startJd <= jd < endJd else [],
		)

	def getIcsData(self, prettyDateTime=False):
		jd = self.getJd()
		return [
			("DTSTART", ics.getIcsDateByJd(jd, prettyDateTime)),
			("DTEND", ics.getIcsDateByJd(jd + 1, prettyDateTime)),
			("TRANSP", "TRANSPARENT"),
			("CATEGORIES", self.name),  # FIXME
		]

	def setIcsData(self, data):
		self.setJd(ics.getJdByIcsDate(data["DTSTART"]))
		return True


@classes.event.register
class YearlyEvent(Event):
	name = "yearly"
	desc = _("Yearly Event")
	iconName = "birthday"
	requiredRules = (
		"month",
		"day",
	)
	supportedRules = requiredRules + ("start",)
	paramsOrder = Event.paramsOrder + ("startYear", "month", "day")
	isAllDay = True

	def getServerData(self):
		data = Event.getServerData(self)
		data.update(
			{
				"month": self.getMonth(),
				"day": self.getDay(),
			},
		)
		try:
			data["startYear"] = int(self["start"].date[0])
		except KeyError:
			data["startYearEnable"] = False
		else:
			data["startYearEnable"] = True
		return data

	def getMonth(self):
		rule, ok = self["month"]
		if ok:
			return rule.values[0]
		return None

	def setMonth(self, month):
		return self.getAddRule("month").setData(month)

	def getDay(self):
		rule, ok = self["day"]
		if ok:
			return rule.values[0]
		return None

	def setDay(self, day):
		return self.getAddRule("day").setData(day)

	def setDefaults(self, group=None):
		Event.setDefaults(self, group=group)
		_y, m, d = getSysDate(self.calType)
		self.setMonth(m)
		self.setDay(d)

	def getJd(self) -> int:  # used only for copyFrom
		startRule, ok = self["start"]
		if ok:
			y = startRule.getDate(self.calType)[0]
		else:
			y = getSysDate(self.calType)[0]
		m = self.getMonth()
		d = self.getDay()
		return to_jd(y, m, d, self.calType)

	def setJd(self, jd) -> None:  # used only for copyFrom
		y, m, d = jd_to(jd, self.calType)
		self.setMonth(m)
		self.setDay(d)
		self.getAddRule("start").date = (y, 1, 1)

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSet:
		# startJd and endJd can be float? or they are just int? FIXME
		calType = self.calType
		month = self.getMonth()
		day = self.getDay()
		if month is None:
			log.error(f"month is None for eventId={self.id}")
			return
		if day is None:
			log.error(f"day is None for eventId={self.id}")
			return
		startRule, ok = self["start"]
		if ok:
			startJd = max(startJd, startRule.getJd())
		startYear = jd_to(ifloor(startJd), calType)[0]
		endYear = jd_to(iceil(endJd), calType)[0]
		jds = set()
		for year in (startYear, endYear + 1):
			jd = to_jd(year, month, day, calType)
			if startJd <= jd < endJd:
				jds.add(jd)
		jds.update(
			to_jd(year, month, day, calType) for year in range(startYear + 1, endYear)
		)
		return JdOccurSet(jds)

	def getData(self):
		data = Event.getData(self)
		start, ok = self["start"]
		if ok:
			data["startYear"] = int(start.date[0])
		data["month"] = self.getMonth()
		data["day"] = self.getDay()
		del data["rules"]
		return data

	def setData(self, data) -> None:
		Event.setData(self, data)
		try:
			startYear = int(data["startYear"])
		except KeyError:
			pass
		except Exception as e:
			log.info(str(e))
		else:
			self.getAddRule("start").date = (startYear, 1, 1)
		try:
			month = data["month"]
		except KeyError:
			pass
		else:
			self.setMonth(month)
		try:
			day = data["day"]
		except KeyError:
			pass
		else:
			self.setDay(day)

	def getSuggestedStartYear(self):
		try:
			startJd = self.parent.startJd
		except AttributeError:
			startJd = core.getCurrentJd()
		return jd_to(startJd, self.calType)[0]

	def getSummary(self):
		summary = Event.getSummary(self)
		try:
			showDate = self.parent.showDate
		except AttributeError:
			showDate = True
		if showDate:
			newParts = [
				_(self.getDay()),
				getMonthName(self.calType, self.getMonth()),
			]
			startRule, ok = self["start"]
			if ok:
				newParts.append(_(startRule.date[0]))
			summary = " ".join(newParts) + ": " + summary
		return summary

	def getIcsData(self, prettyDateTime=False):
		if self.calType != GREGORIAN:
			return None
		month = self.getMonth()
		day = self.getDay()
		startYear = icsMinStartYear
		startRule, ok = self["start"]
		if ok:
			startYear = startRule.getDate(GREGORIAN)[0]
		elif getattr(self.parent, "startJd", None):
			startYear = jd_to(self.parent.startJd, GREGORIAN)[0]
		jd = to_jd(
			startYear,
			month,
			day,
			GREGORIAN,
		)
		return [
			("DTSTART", ics.getIcsDateByJd(jd, prettyDateTime)),
			("DTEND", ics.getIcsDateByJd(jd + 1, prettyDateTime)),
			("RRULE", f"FREQ=YEARLY;BYMONTH={month};BYMONTHDAY={day}"),
			("TRANSP", "TRANSPARENT"),
			("CATEGORIES", self.name),  # FIXME
		]

	def setIcsData(self, data):
		rrule = dict(ics.splitIcsValue(data["RRULE"]))
		try:
			month = int(rrule["BYMONTH"])
			# multiple values are not supported
		except (KeyError, ValueError):
			return False
		try:
			day = int(rrule["BYMONTHDAY"])
			# multiple values are not supported
		except (KeyError, ValueError):
			return False
		self.setMonth(month)
		self.setDay(day)
		self.calType = GREGORIAN
		return True


@classes.event.register
class MonthlyEvent(Event):
	name = "monthly"
	desc = _("Monthly Event")
	iconName = ""
	requiredRules = (
		"start",
		"end",
		"day",
		"dayTimeRange",
	)
	supportedRules = requiredRules
	isAllDay = False

	def getServerData(self):
		data = Event.getServerData(self)
		startSec, endSec = self["dayTimeRange"].getSecondsRange()
		data.update(
			{
				"startJd": self["start"].getJd(),
				"endJd": self["end"].getJd(),
				"day": self.getDay(),
				"dayStartSeconds": startSec,
				"dayEndSeconds": endSec,
			},
		)
		return data

	def setDefaults(self, group=None):
		Event.setDefaults(self, group=group)
		year, month, day = jd_to(core.getCurrentJd(), self.calType)
		start, ok = self["start"]
		if ok:
			start.setDate((year, month, 1))
		else:
			raise RuntimeError("no start rule")
		end, ok = self["end"]
		if ok:
			end.setDate((year + 1, month, 1))
		else:
			raise RuntimeError("no end rule")
		self.setDay(day)

	def getDay(self):
		rule, ok = self["day"]
		if not ok:
			raise RuntimeError("no day rule")
		if not rule.values:
			return 1
		return rule.values[0]

	def setDay(self, day):
		rule, ok = self["day"]
		if not ok:
			raise RuntimeError("no day rule")
		rule.values = [day]


@classes.event.register
class WeeklyEvent(Event):
	name = "weekly"
	desc = _("Weekly Event")
	iconName = ""
	requiredRules = (
		"start",
		"end",
		"cycleWeeks",
		"dayTimeRange",
	)
	supportedRules = requiredRules
	isAllDay = False

	def getServerData(self):
		data = Event.getServerData(self)
		startSec, endSec = self["dayTimeRange"].getSecondsRange()
		data.update(
			{
				"startJd": self["start"].getJd(),
				"endJd": self["end"].getJd(),
				"cycleWeeks": self["cycleWeeks"].getData(),
				"dayStartSeconds": startSec,
				"dayEndSeconds": endSec,
			},
		)
		return data

	def setDefaults(self, group=None):
		Event.setDefaults(self, group=group)
		jd = core.getCurrentJd()
		start, ok = self["start"]
		if not ok:
			raise RuntimeError("no start rule")
		end, ok = self["end"]
		if not ok:
			raise RuntimeError("no end rule")
		start.setJd(jd)
		end.setJd(jd + 8)


# TODO
# @classes.event.register
# class UniversityCourseOwner(Event):


@classes.event.register
class UniversityClassEvent(Event):
	name = "universityClass"
	desc = _("Class")
	iconName = "university"
	requiredRules = (
		"weekNumMode",
		"weekDay",
		"dayTimeRange",
	)
	supportedRules = (
		"weekNumMode",
		"weekDay",
		"dayTimeRange",
	)
	params = Event.params + ("courseId",)
	isAllDay = False

	def getServerData(self):
		data = Event.getServerData(self)
		startSec, endSec = self["dayTimeRange"].getSecondsRange()
		data.update(
			{
				"weekNumMode": self["weekNumMode"].getData(),
				"weekDayList": self["weekDay"].getData(),
				"dayStartSeconds": startSec,
				"dayEndSeconds": endSec,
				"courseId": self.courseId,
			},
		)
		return data

	def __init__(self, _id=None, parent=None):
		# assert parent is not None
		Event.__init__(self, _id, parent)
		self.courseId = None  # FIXME

	def setDefaults(self, group=None):
		Event.setDefaults(self, group=group)
		if group and group.name == "universityTerm":
			try:
				tm0, tm1 = group.classTimeBounds[:2]
			except ValueError:
				log.exception("")
			else:
				rule, ok = self["dayTimeRange"]
				if not ok:
					raise RuntimeError("no dayTimeRange rule")
				rule.setRange(
					tm0 + (0,),
					tm1 + (0,),
				)

	def getCourseName(self):
		return self.parent.getCourseNameById(self.courseId)

	def getWeekDayName(self):
		rule, ok = self["weekDay"]
		if not ok:
			raise RuntimeError("no weekDay rule")
		return core.weekDayName[rule.weekDayList[0]]

	def updateSummary(self):
		self.summary = (
			_("{courseName} Class").format(courseName=self.getCourseName())
			+ " ("
			+ self.getWeekDayName()
			+ ")"
		)

	def setJd(self, jd: int) -> None:
		rule, ok = self["weekDay"]
		if not ok:
			raise RuntimeError("no weekDay rule")
		rule.weekDayList = [jwday(jd)]
		# set weekNumMode from absWeekNumber FIXME

	def getIcsData(self, prettyDateTime=False):
		start, ok = self["start"]
		if not ok:
			raise RuntimeError("no start rule")
		end, ok = self["end"]
		if not ok:
			raise RuntimeError("no end rule")
		startJd = start.getJd()
		endJd = end.getJd()
		occur = self.calcEventOccurrenceIn(startJd, endJd)
		tRangeList = occur.getTimeRangeList()
		if not tRangeList:
			return
		weekNumMode, ok = self["weekNumMode"]
		if not ok:
			raise RuntimeError("no weekNumMode rule")
		weekDay, ok = self["weekDay"]
		if not ok:
			raise RuntimeError("no weekDay rule")
		until = ics.getIcsDateByJd(endJd, prettyDateTime)
		interval = 1 if weekNumMode.getData() == "any" else 2
		byDay = ics.encodeIcsWeekDayList(weekDay.weekDayList)
		return [
			(
				"DTSTART",
				ics.getIcsTimeByEpoch(
					tRangeList[0][0],
					prettyDateTime,
				),
			),
			(
				"DTEND",
				ics.getIcsTimeByEpoch(
					tRangeList[0][1],
					prettyDateTime,
				),
			),
			(
				"RRULE",
				f"FREQ=WEEKLY;UNTIL={until};INTERVAL={interval};BYDAY={byDay}",
			),
			("TRANSP", "OPAQUE"),
			("CATEGORIES", self.name),  # FIXME
		]


@classes.event.register
class UniversityExamEvent(DailyNoteEvent):
	name = "universityExam"
	desc = _("Exam")
	iconName = "university"
	requiredRules = (
		"date",
		"dayTimeRange",
	)
	supportedRules = (
		"date",
		"dayTimeRange",
	)
	params = DailyNoteEvent.params + ("courseId",)
	isAllDay = False

	def getServerData(self):
		data = Event.getServerData(self)
		startSec, endSec = self["dayTimeRange"].getSecondsRange()
		data.update(
			{
				"jd": self.getJd(),
				"dayStartSeconds": startSec,
				"dayEndSeconds": endSec,
				"courseId": self.courseId,
			},
		)
		return data

	def __init__(self, _id=None, parent=None):
		# assert group is not None  # FIXME
		DailyNoteEvent.__init__(self, _id, parent)
		self.courseId = None  # FIXME

	def setDefaults(self, group=None):
		DailyNoteEvent.setDefaults(self, group=group)
		dayTimeRange, ok = self["dayTimeRange"]
		if not ok:
			raise RuntimeError("no dayTimeRange rule")
		dayTimeRange.setRange((9, 0), (11, 0))  # FIXME
		if group and group.name == "universityTerm":
			self.setJd(group.endJd)  # FIXME

	def getCourseName(self):
		return self.parent.getCourseNameById(self.courseId)

	def updateSummary(self):
		self.summary = _("{courseName} Exam").format(
			courseName=self.getCourseName(),
		)

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSet:
		jd = self.getJd()
		if not startJd <= jd < endJd:
			return IntervalOccurSet()

		epoch = self.getEpochFromJd(jd)
		dayTimeRange, ok = self["dayTimeRange"]
		if not ok:
			raise RuntimeError("no dayTimeRange rule")
		startSec, endSec = dayTimeRange.getSecondsRange()
		return IntervalOccurSet(
			[
				(
					epoch + startSec,
					epoch + endSec,
				),
			],
		)

	def getIcsData(self, prettyDateTime=False):
		date, ok = self["date"]
		if not ok:
			raise RuntimeError("no date rule")
		dayStart = date.getEpoch()
		dayTimeRange, ok = self["dayTimeRange"]
		if not ok:
			raise RuntimeError("no dayTimeRange rule")
		startSec, endSec = dayTimeRange.getSecondsRange()
		return [
			(
				"DTSTART",
				ics.getIcsTimeByEpoch(
					dayStart + startSec,
					prettyDateTime,
				),
			),
			(
				"DTEND",
				ics.getIcsTimeByEpoch(
					dayStart + endSec,
					prettyDateTime,
				),
			),
			("TRANSP", "OPAQUE"),
		]


@classes.event.register
class LifetimeEvent(SingleStartEndEvent):
	name = "lifetime"
	nameAlias = "lifeTime"
	desc = _("Lifetime Event")
	requiredRules = (
		"start",
		"end",
	)
	supportedRules = (
		"start",
		"end",
	)
	isAllDay = True

	# def setDefaults(self):
	# 	start, ok = self["start"]
	# 	if ok:
	# 		start.date = ...

	def getServerData(self):
		data = Event.getServerData(self)
		data.update(
			{
				"startJd": self["start"].getJd(),
				"endJd": self["end"].getJd(),
			},
		)
		return data

	def setJd(self, jd: int) -> None:
		self.getAddRule("start").setJdExact(jd)
		self.getAddRule("end").setJdExact(jd)

	def addRule(self, rule):
		if rule.name in {"start", "end"}:
			rule.time = (0, 0, 0)
		SingleStartEndEvent.addRule(self, rule)

	def modifyPos(self, newStartEpoch):
		start, _ok = self["start"]
		end, _ok = self["end"]
		newStartJd = round(getFloatJdFromEpoch(newStartEpoch))
		end.setJdExact(end.getJd() + newStartJd - start.getJd())
		start.setJdExact(newStartJd)

	def modifyStart(self, newEpoch):
		start, ok = self["start"]
		if not ok:
			raise RuntimeError("no start rule")
		start.setEpoch(roundEpochToDay(newEpoch))

	def modifyEnd(self, newEpoch):
		end, ok = self["end"]
		if not ok:
			raise RuntimeError("no end rule")
		end.setEpoch(roundEpochToDay(newEpoch))


@classes.event.register
class LargeScaleEvent(Event):  # or MegaEvent? FIXME
	name = "largeScale"
	desc = _("Large Scale Event")
	isSingleOccur = True
	_myParams = (
		"scale",
		"start",
		"end",
		"endRel",
	)
	params = Event.params + _myParams
	paramsOrder = Event.paramsOrder + _myParams

	def __bool__(self):
		return True

	isAllDay = True

	def getServerData(self):
		data = Event.getServerData(self)
		data.update(
			{
				"scale": self.scale,
				"start": self.start,
				"end": self.end,
				"durationEnable": self.endRel,
			},
		)
		return data

	def __init__(self, _id=None, parent=None):
		self.scale = 1  # 1, 1000, 1000**2, 1000**3
		self.start = 0
		self.end = 1
		self.endRel = True
		Event.__init__(self, _id, parent)

	def setData(self, data) -> None:
		Event.setData(self, data)
		if "duration" in data:
			data["end"] = data["duration"]
			data["endRel"] = True

	def getRulesHash(self):
		return hash(
			str(
				(
					self.getTimeZoneStr(),
					"largeScale",
					self.scale,
					self.start,
					self.end,
					self.endRel,
				),
			),
		)
		# hash(str(tupleObj)) is probably safer than hash(tupleObj)

	def getEnd(self):
		return self.start + self.end if self.endRel else self.end

	def setDefaults(self, group=None):
		Event.setDefaults(self, group=group)
		if group and group.name == "largeScale":
			self.scale = group.scale
			self.start = group.getStartValue()

	def getJd(self) -> int:
		return to_jd(
			self.start * self.scale,
			1,
			1,
			self.calType,
		)

	def setJd(self, jd: int) -> None:
		self.start = jd_to(jd, self.calType)[0] // self.scale

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSet:
		myStartJd = iceil(
			to_jd(
				int(self.scale * self.start),
				1,
				1,
				self.calType,
			),
		)
		myEndJd = ifloor(
			to_jd(
				int(self.scale * self.getEnd()),
				1,
				1,
				self.calType,
			),
		)
		return IntervalOccurSet.newFromStartEnd(
			max(
				self.getEpochFromJd(myStartJd),
				self.getEpochFromJd(startJd),
			),
			min(
				self.getEpochFromJd(myEndJd),
				self.getEpochFromJd(endJd),
			),
		)

	# def getIcsData(self, prettyDateTime=False):
	# 	pass


@classes.event.register
class CustomEvent(Event):
	name = "custom"
	desc = _("Custom Event")
	isAllDay = False

	def getServerData(self):
		data = Event.getServerData(self)
		data.update(
			{
				"rules": [
					{
						"type": ruleName,
						"value": rule.getServerString(),
					}
					for ruleName, rule in self.rulesOd.items()
				],
			},
		)
		return data
