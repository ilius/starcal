#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from scal3 import logger
log = logger.get()

import os
import os.path
from os.path import join, split, dirname, splitext, isabs
from os import listdir
import math
from time import time as now

from typing import Tuple, List, Dict, Set, Any, ClassVar, Callable, Iterator

import natz

from collections import OrderedDict

from .path import *

from scal3.utils import (
	ifloor,
	iceil,
	findNearestIndex,
	toStr,
	s_join,
	numRangesEncode,
)
from scal3.interval_utils import *
from scal3.time_utils import *
from scal3.date_utils import *
from scal3.json_utils import jsonToData


from scal3.s_object import *

from scal3.cal_types import (
	calTypes,
	jd_to,
	to_jd,
	convert,
	GREGORIAN,
	getSysDate,
)
from scal3 import ics
from scal3.locale_man import tr as _
from scal3.locale_man import getMonthName, textNumEncode
from scal3 import core
from scal3.core import (
	log,
	getAbsWeekNumberFromJd,
	jd_to_primary,
)

##########################

(
	IMPORT_MODE_APPEND,
	IMPORT_MODE_SKIP_MODIFIED,
	IMPORT_MODE_OVERRIDE_MODIFIED,
) = range(3)

##########################


dayLen = 24 * 3600

icsMinStartYear = 1970
icsMaxEndYear = 2050

eventsDir = join("event", "events")
groupsDir = join("event", "groups")
accountsDir = join("event", "accounts")

##########################

lockPath = join(confDir, "event", "lock.json")
allReadOnly = False


###################################################


def init(fs: FileSystem) -> None:
	global allReadOnly, info, lastIds

	fs.makeDir(objectDir)
	fs.makeDir(eventsDir)
	fs.makeDir(groupsDir)
	fs.makeDir(accountsDir)

	import scal3.account.starcal
	from scal3.lockfile import checkAndSaveJsonLockFile
	allReadOnly = checkAndSaveJsonLockFile(lockPath)
	if allReadOnly:
		log.info(f"Event lock file {lockPath} exists, EVENT DATA IS READ-ONLY")

	info = InfoWrapper.load(fs)
	lastIds = LastIdsWrapper.load(fs)
	lastIds.scan()


class JsonEventObj(JsonSObj):
	def save(self) -> None:
		if allReadOnly:
			log.info(f"events are read-only, ignored file {self.file}")
			return
		JsonSObj.save(self)


class Smallest:
	def __eq__(self, other: Any) -> bool:
		if isinstance(other, Smallest):
			return True
		return False

	def __lt__(self, other: Any) -> bool:
		return True

	def __gt__(self, other: Any) -> bool:
		return False


smallest = Smallest()


class BsonHistEventObj(BsonHistObj):
	def set_uuid(self) -> None:
		from uuid import uuid4
		self.uuid = uuid4().hex

	def save(self, *args) -> None:
		if allReadOnly:
			log.info(f"events are read-only, ignored file {self.file}")
			return
		if hasattr(self, "uuid"):
			if self.uuid is None:
				self.set_uuid()
		return BsonHistObj.save(self, *args)


class InfoWrapper(JsonEventObj):
	file = join(confDir, "event", "info.json")
	skipLoadNoFile = True
	params = (
		"version",
		"last_run",
	)
	paramsOrder = (
		"version",
		"last_run",
	)

	def __init__(self) -> None:
		self.version = ""
		self.last_run = 0

	def update(self) -> None:
		self.version = core.VERSION
		self.last_run = int(now())

	def updateAndSave(self) -> None:
		self.update()
		self.save()


info = None  # type: InfoWrapper

###################################################


class LastIdsWrapper(JsonEventObj):
	skipLoadNoFile = True
	file = join(confDir, "event", "last_ids.json")
	params = (
		"event",
		"group",
		"account",
	)
	paramsOrder = (
		"event",
		"group",
		"account",
	)

	def __init__(self) -> None:
		self.event = 0
		self.group = 0
		self.account = 0

	def __str__(self) -> str:
		return (
			"LastIds(" +
			f"event={self.event}, " +
			f"group={self.group}, " +
			f"account={self.account}" +
			")"
		)

	def scanDir(self, dpath: str) -> int:
		lastId = 0
		for fname in self.fs.listdir(dpath):
			idStr, ext = splitext(fname)
			if ext != ".json":
				continue
			try:
				_id = int(idStr)
			except ValueError:
				log.error(f"invalid file name: {dpath}")
				continue
			if _id > lastId:
				lastId = _id
		return lastId

	def scan(self) -> None:
		t0 = now()
		self.event = self.scanDir("event/events")
		self.group = self.scanDir("event/groups")
		self.account = self.scanDir("event/accounts")
		self.save()
		log.info(f"Scanning last_ids took {now() - t0:.3f} seconds, {self}")


lastIds = None  # type: LastIdsWrapper

###########################################################################


def removeUnusedObjects(fs: FileSystem):
	global allReadOnly
	if allReadOnly:
		raise RuntimeError("removeUnusedObjects: EVENTS ARE READ-ONLY")

	def do_removeUnusedObjects():
		hashSet = set()
		for cls in (Account, EventTrash, EventGroup, Event):
			for fpath in cls.iterFiles(fs):
				with fs.open(fpath) as fp:
					jsonStr = fp.read()
				data = jsonToData(jsonStr)
				history = data.get("history")
				if not history:
					log.error(f"No history in file: {fpath}")
					continue
				for revTime, revHash in history:
					hashSet.add(revHash)

		log.info(f"Found {len(hashSet)} used objects")
		removedCount = 0
		for _hash, fpath in iterObjectFiles(fs):
			if _hash not in hashSet:
				log.debug(f"Removing file: {fpath}")
				removedCount += 1
				fs.removeFile(fpath)
		log.info(f"Removed {removedCount} objects")

	allReadOnly = True
	try:
		tm0 = now()
		do_removeUnusedObjects()
		log.info(f"removeUnusedObjects: took {now() - tm0}")
	finally:
		allReadOnly = False


###########################################################################

class ClassGroup(list):
	def __init__(self, tname: str) -> None:
		list.__init__(self)
		self.tname = tname
		self.names = []
		self.byName = {}
		self.byDesc = {}
		self.main = None

	def register(self, cls: ClassVar) -> ClassVar:
		assert cls.name != ""
		cls.tname = self.tname
		self.append(cls)
		self.names.append(cls.name)
		self.byName[cls.name] = cls
		self.byDesc[cls.desc] = cls
		if hasattr(cls, "nameAlias"):
			self.byName[cls.nameAlias] = cls
		return cls

	def setMain(self, cls: ClassVar) -> ClassVar:
		self.main = cls
		return cls


class classes:
	rule = ClassGroup("rule")
	notifier = ClassGroup("notifier")
	event = ClassGroup("event")
	group = ClassGroup("group")
	account = ClassGroup("account")


defaultEventTypeIndex = 0  # FIXME
defaultGroupTypeIndex = 0  # FIXME

__plugin_api_get__ = [
	"classes", "defaultEventTypeIndex", "defaultGroupTypeIndex",
	"EventRule", "EventNotifier", "Event", "EventGroup", "Account",
]


###########################################################################

# FIXME move this o Event class
def getEventUID(event: "Event") -> str:
	import socket
	event_st = core.compressLongInt(hash(str(event.getData())))
	time_st = core.getCompactTime()
	host = socket.gethostname()
	return event_st + "_" + time_st + "@" + host


class BadEventFile(Exception):  # FIXME
	pass


class OccurSet(SObj):
	def __init__(self) -> None:
		self.event = None

	def intersection(self) -> None:
		raise NotImplementedError

	def getDaysJdList(self) -> List[int]:
		return []  # make generator FIXME

	def getTimeRangeList(self) -> List[Tuple[int, int]]:
		return []  # make generator FIXME

	def getFloatJdRangeList(self) -> List[Tuple[float, float]]:
		ls = []
		for ep0, ep1 in self.getTimeRangeList():
			ls.append((getFloatJdFromEpoch(ep0), getFloatJdFromEpoch(ep1)))
		return ls

	def getStartJd(self) -> int:
		raise NotImplementedError

	def getEndJd(self) -> int:
		raise NotImplementedError

	# def __iter__(self) -> Iterator:
	# 	return iter(self.getTimeRangeList())


class JdOccurSet(OccurSet):
	name = "jdSet"

	def __init__(self, jdSet: Optional[Set[int]] = None) -> None:
		OccurSet.__init__(self)
		if not jdSet:
			jdSet = []
		self.jdSet = set(jdSet)

	def __repr__(self) -> str:
		return f"JdOccurSet({list(self.jdSet)})"

	def __bool__(self) -> bool:
		return bool(self.jdSet)

	def __len__(self) -> int:
		return len(self.jdSet)

	def getStartJd(self) -> int:
		if not self.jdSet:
			return
		return min(self.jdSet)

	def getEndJd(self) -> int:
		if not self.jdSet:
			return
		return max(self.jdSet) + 1

	def intersection(self, occur: OccurSet) -> OccurSet:
		if isinstance(occur, JdOccurSet):
			return JdOccurSet(
				self.jdSet.intersection(occur.jdSet)
			)
		elif isinstance(occur, IntervalOccurSet):
			return IntervalOccurSet(
				intersectionOfTwoIntervalList(
					self.getTimeRangeList(),
					occur.getTimeRangeList(),
				)
			)
		elif isinstance(occur, TimeListOccurSet):
			return occur.intersection(self)
		else:
			raise TypeError

	def getDaysJdList(self) -> List[int]:
		return sorted(self.jdSet)

	def getTimeRangeList(self) -> List[Tuple[int, int]]:
		return [
			(
				getEpochFromJd(jd),
				getEpochFromJd(jd + 1),
			) for jd in self.jdSet
		]

	def calcJdRanges(self) -> List[Tuple[int, int]]:
		jdList = sorted(self.jdSet)  # jdList is sorted
		if not jdList:
			return []
		startJd = jdList[0]
		endJd = startJd + 1
		jdRanges = []
		for jd in jdList[1:]:
			if jd == endJd:
				endJd += 1
			else:
				jdRanges.append((startJd, endJd))
				startJd = jd
				endJd = startJd + 1
		jdRanges.append((startJd, endJd))
		return jdRanges


class IntervalOccurSet(OccurSet):
	name = "timeRange"

	def __init__(self, rangeList: Optional[List[Tuple[int, int]]] = None) -> str:
		OccurSet.__init__(self)
		if not rangeList:
			rangeList = []
		self.rangeList = rangeList

	def __repr__(self) -> str:
		return f"IntervalOccurSet({self.rangeList!r})"

	def __bool__(self) -> bool:
		return bool(self.rangeList)

	def __len__(self) -> int:
		return len(self.rangeList)

	# def __getitem__(i):
	# 	self.rangeList.__getitem__(i)  # FIXME

	def getStartJd(self) -> int:
		if not self.rangeList:
			return
		return getJdFromEpoch(min(
			r[0] for r in self.rangeList
		))

	def getEndJd(self) -> int:
		if not self.rangeList:
			return
		return getJdFromEpoch(max(
			r[1] for r in self.rangeList
		))

	def intersection(self, occur: OccurSet) -> OccurSet:
		if isinstance(occur, (JdOccurSet, IntervalOccurSet)):
			return IntervalOccurSet(
				intersectionOfTwoIntervalList(
					self.getTimeRangeList(),
					occur.getTimeRangeList(),
				)
			)
		elif isinstance(occur, TimeListOccurSet):
			return occur.intersection(self)
		else:
			raise TypeError(
				f"bad type {occur.__class__.__name__} ({occur!r})"
			)

	def getDaysJdList(self) -> List[int]:
		return sorted({
			jd
			for jd in getJdListFromEpochRange(startEpoch, endEpoch)
			for startEpoch, endEpoch in self.rangeList
		})

	def getTimeRangeList(self) -> List[Tuple[int, int]]:
		return self.rangeList

	@staticmethod
	def newFromStartEnd(startEpoch: int, endEpoch: int) -> OccurSet:
		if startEpoch > endEpoch:
			return IntervalOccurSet([])
		else:
			return IntervalOccurSet([(startEpoch, endEpoch)])


class TimeListOccurSet(OccurSet):
	name = "repeativeTime"

	def __init__(self, *args) -> None:
		OccurSet.__init__(self)
		if len(args) == 0:
			self.startEpoch = 0
			self.endEpoch = 0
			self.stepSeconds = -1
			self.epochList = set()
		if len(args) == 1:
			self.epochList = set(args[0])
		elif len(args) == 3:
			self.setRange(*args)
		else:
			raise ValueError

	def __repr__(self) -> str:
		return r"TimeListOccurSet({self.epochList!r})"

	# def __bool__(self) -> bool:
	# 	return self.startEpoch == self.endEpoch

	def __bool__(self) -> bool:
		return bool(self.epochList)

	def getStartJd(self) -> int:
		if not self.epochList:
			return
		return getJdFromEpoch(min(self.epochList))

	def getEndJd(self) -> int:
		if not self.epochList:
			return
		return getJdFromEpoch(max(self.epochList) + 1)

	def setRange(self, startEpoch: int, endEpoch: int, stepSeconds: int) -> None:
		try:
			from numpy.core.multiarray import arange
		except ImportError:
			from scal3.utils import arange
		######
		self.startEpoch = startEpoch
		self.endEpoch = endEpoch
		self.stepSeconds = stepSeconds
		self.epochList = set(arange(startEpoch, endEpoch, stepSeconds))

	def intersection(self, occur: OccurSet) -> OccurSet:
		if isinstance(occur, (JdOccurSet, IntervalOccurSet)):
			epochBetween = []
			for epoch in self.epochList:
				for startEpoch, endEpoch in occur.getTimeRangeList():
					if startEpoch <= epoch < endEpoch:
						epochBetween.append(epoch)
						break
			return TimeListOccurSet(epochBetween)
		elif isinstance(occur, TimeListOccurSet):
			return TimeListOccurSet(
				self.epochList.intersection(occur.epochList)
			)
		else:
			raise TypeError

	# FIXME: improve performance
	def getDaysJdList(self) -> List[int]:
		return sorted({
			getJdFromEpoch(epoch)
			for epoch in self.epochList
		})

	def getTimeRangeList(self) -> List[Tuple[int, int]]:
		return [
			(epoch, epoch)
			for epoch in self.epochList
		]  # or end=None, FIXME


# Should not be registered, or instantiate directly
@classes.rule.setMain
class EventRule(SObj):
	name = ""
	desc = ""
	provide = ()
	need = ()
	conflict = ()
	sgroup = -1
	expand = False
	params = ()

	def getServerString(self) -> str:
		raise NotImplementedError

	def __bool__(self) -> bool:
		return True

	def __init__(self, parent: "Event"):
		"""
		parent can be an event for now (maybe later a group too)
		"""
		self.parent = parent

	def copy(self) -> "EventRule":
		newObj = self.__class__(self.parent)
		newObj.fs = getattr(self, "fs", None)
		newObj.copyFrom(self)
		return newObj

	def getCalType(self) -> int:
		return self.parent.calType

	def changeCalType(self, calType: int) -> bool:
		return True

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: "Event",
	) -> OccurSet:
		raise NotImplementedError

	def getInfo(self) -> str:
		return self.desc + f": {self}"

	def getEpochFromJd(self, jd: int) -> int:
		return getEpochFromJd(
			jd,
			tz=self.parent.getTimeZoneObj(),
		)


class AllDayEventRule(EventRule):
	def jdMatches(self, jd: int) -> bool:
		return True

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: "Event",
	) -> OccurSet:
		# improve performance FIXME
		jds = set()
		for jd in range(startJd, endJd):
			if self.jdMatches(jd):
				jds.add(jd)  # benchmark FIXME
		return JdOccurSet(jds)


# Should not be registered, or instantiate directly
class MultiValueAllDayEventRule(AllDayEventRule):
	conflict = (
		"date",
	)
	params = ("values",)
	expand = True  # FIXME

	def __init__(self, parent: "Event") -> None:
		EventRule.__init__(self, parent)
		self.values = []

	def getData(self) -> List[Any]:
		return self.values

	def setData(self, data: Any):
		if not isinstance(data, (tuple, list)):
			data = [data]
		self.values = data

	def formatValue(self, v: Any) -> str:
		return _(v)

	def __str__(self) -> str:
		return textNumEncode(numRangesEncode(self.values, ", "))

	def hasValue(self, value: Any) -> bool:
		for item in self.values:
			if isinstance(item, (tuple, list)):
				if item[0] <= value <= item[1]:
					return True
			elif item == value:
				return True
		return False

	def getValuesPlain(self) -> List[Union[int, Tuple[int, int]]]:
		ls = []
		for item in self.values:
			if isinstance(item, (tuple, list)):
				ls += list(range(item[0], item[1] + 1))
			else:
				ls.append(item)
		return ls

	def setValuesPlain(self, values: List[Union[int, Tuple[int, int]]]) -> None:
		self.values = simplifyNumList(values)

	def changeCalType(self, calType: int) -> bool:
		return False


@classes.rule.register
class YearEventRule(MultiValueAllDayEventRule):
	name = "year"
	desc = _("Year")
	params = ("values",)

	def getServerString(self) -> str:
		return numRangesEncode(self.values, " ")  # no comma

	def __init__(self, parent: "Event") -> None:
		MultiValueAllDayEventRule.__init__(self, parent)
		self.values = [getSysDate(self.getCalType())[0]]

	def jdMatches(self, jd: int) -> bool:
		return self.hasValue(jd_to(jd, self.getCalType())[0])

	def newCalTypeValues(
		self,
		newCalType: int,
	) -> List[Union[int, Tuple[int, int]]]:
		def yearConv(year):
			return convert(year, 7, 1, curCalType, newCalType)[0]

		curCalType = self.getCalType()
		values2 = []
		for item in self.values:
			if isinstance(item, (tuple, list)):
				values2.append((
					yearConv(item[0]),
					yearConv(item[1]),
				))
			else:
				values2.append(yearConv(item))
		return values2

	def changeCalType(self, calType: int) -> bool:
		self.values = self.newCalTypeValues(calType)
		return True


@classes.rule.register
class MonthEventRule(MultiValueAllDayEventRule):
	name = "month"
	desc = _("Month")
	conflict = (
		"date",
		"weekMonth",
	)
	params = ("values",)

	def getServerString(self) -> str:
		return numRangesEncode(self.values, " ")  # no comma

	def __init__(self, parent: "Event") -> None:
		MultiValueAllDayEventRule.__init__(self, parent)
		self.values = [1]

	def jdMatches(self, jd: int) -> bool:
		return self.hasValue(jd_to(jd, self.getCalType())[1])

	# overwrite __str__? FIXME


@classes.rule.register
class DayOfMonthEventRule(MultiValueAllDayEventRule):
	name = "day"
	desc = _("Day of Month")
	params = ("values",)

	def getServerString(self) -> str:
		return numRangesEncode(self.values, " ")  # no comma

	def __init__(self, parent: "Event") -> None:
		MultiValueAllDayEventRule.__init__(self, parent)
		self.values = [1]

	def jdMatches(self, jd: int) -> bool:
		return self.hasValue(jd_to(jd, self.getCalType())[2])


@classes.rule.register
class WeekNumberModeEventRule(EventRule):
	name = "weekNumMode"
	desc = _("Week Number")
	need = (
		"start",  # FIXME
	)
	conflict = (
		"date",
		"weekMonth",
	)
	params = (
		"weekNumMode",
	)
	EVERY_WEEK, ODD_WEEKS, EVEN_WEEKS = list(range(3))
	# remove EVERY_WEEK? FIXME
	weekNumModeNames = ("any", "odd", "even")

	def getServerString(self) -> str:
		return self.weekNumMode

	def __init__(self, parent: "Event") -> None:
		EventRule.__init__(self, parent)
		self.weekNumMode = self.EVERY_WEEK

	def getData(self) -> str:
		return self.weekNumModeNames[self.weekNumMode]

	def setData(self, wnModeName: str) -> None:
		if wnModeName not in self.weekNumModeNames:
			raise BadEventFile(
				f"bad rule value weekNumMode={wnModeName!r}, " +
				"the value for weekNumMode must be " +
				f"one of {self.weekNumModeNames!r}"
			)
		self.weekNumMode = self.weekNumModeNames.index(wnModeName)

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: "Event",
	) -> OccurSet:
		# improve performance FIXME
		startAbsWeekNum = getAbsWeekNumberFromJd(event.getStartJd()) - 1
		# 1st week # FIXME
		if self.weekNumMode == self.EVERY_WEEK:
			return JdOccurSet(
				range(startJd, endJd)
			)
		elif self.weekNumMode == self.ODD_WEEKS:
			return JdOccurSet({
				jd
				for jd in range(startJd, endJd)
				if (getAbsWeekNumberFromJd(jd) - startAbsWeekNum) % 2 == 1
			})
		elif self.weekNumMode == self.EVEN_WEEKS:
			return JdOccurSet({
				jd
				for jd in range(startJd, endJd)
				if (getAbsWeekNumberFromJd(jd) - startAbsWeekNum) % 2 == 0
			})

	def getInfo(self) -> None:
		if self.weekNumMode == self.EVERY_WEEK:
			return ""
		elif self.weekNumMode == self.ODD_WEEKS:
			return _("Odd Weeks")
		elif self.weekNumMode == self.EVEN_WEEKS:
			return _("Even Weeks")


@classes.rule.register
class WeekDayEventRule(AllDayEventRule):
	name = "weekDay"
	desc = _("Day of Week")
	conflict = (
		"date",
		"weekMonth",
	)
	params = (
		"weekDayList",
	)

	def getServerString(self) -> str:
		return s_join(self.weekDayList)

	def __init__(self, parent: "Event") -> None:
		EventRule.__init__(self, parent)
		self.weekDayList = list(range(7))  # or [] FIXME

	def getData(self) -> List[int]:
		return self.weekDayList

	def setData(self, data: Union[int, List[int]]) -> None:
		if isinstance(data, int):
			self.weekDayList = [data]
		elif isinstance(data, (tuple, list)):
			self.weekDayList = data
		else:
			raise BadEventFile(
				f"bad rule weekDayList={data}, " +
				"value for weekDayList must be a list of integers" +
				" (0 for sunday)"
			)

	def jdMatches(self, jd: int) -> None:
		return jwday(jd) in self.weekDayList

	def getInfo(self) -> str:
		if self.weekDayList == list(range(7)):
			return ""
		sep = _(",") + " "
		sep2 = " " + _("or") + " "
		return _("Day of Week") + ": " + \
			sep.join([
				core.weekDayName[wd] for wd in self.weekDayList[:-1]
			]) + \
			sep2 + core.weekDayName[self.weekDayList[-1]]


@classes.rule.register
class WeekMonthEventRule(EventRule):
	name = "weekMonth"
	desc = _("Week-Month")
	conflict = (
		"date",
		"month",
		"ex_month",
		"weekNumMode"
		"weekday",
		"cycleDays",
		"cycleWeeks",
		"cycleLen",
	)
	params = (
		"month",  # 0..12   0 means every month
		"wmIndex",  # 0..4
		"weekDay",  # 0..6
	)
	"""
	paramsValidators = {
		"month": lambda m: 0 <= m <= 12,
		"wmIndex": lambda m: 0 <= m <= 4,
		"weekDay": lambda m: 0 <= m <= 6,
	}
	"""
	wmIndexNames = (
		_("First"),  # 0
		_("Second"),  # 1
		_("Third"),  # 2
		_("Fourth"),  # 3
		_("Last"),  # 4
	)

	def getServerString(self) -> str:
		return json.dumps({
			"weekIndex": self.wmIndex,
			"weekDay": self.weekDay,
			"month": self.month,
		})

	def __init__(self, parent: "Event") -> None:
		EventRule.__init__(self, parent)
		self.month = 1
		self.wmIndex = 4
		self.weekDay = core.firstWeekDay

	# usefull? FIXME
	# def setJd(self, jd) -> None:
	# 	self.month, self.wmIndex, self.weekDay = core.getMonthWeekNth(
	# 	jd,
	# 	self.getCalType(),
	# )

	# def getJd(self) -> int:

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: "Event",
	) -> OccurSet:
		calType = self.getCalType()
		startYear, startMonth, startDay = jd_to(startJd, calType)
		endYear, endMonth, endDay = jd_to(endJd, calType)
		jds = set()
		monthList = range(1, 13) if self.month == 0 else [self.month]
		for year in range(startYear, endYear):
			for month in monthList:
				jd = to_jd(
					year,
					month,
					7 * self.wmIndex + 1,
					calType,
				)
				jd += (self.weekDay - jwday(jd)) % 7
				if self.wmIndex == 4:  # Last (Fouth or Fifth)
					if jd_to(jd, calType)[1] != month:
						jd -= 7
				if startJd <= jd < endJd:
					jds.add(jd)
		return JdOccurSet(jds)


@classes.rule.register
class DateEventRule(EventRule):
	name = "date"
	desc = _("Date")
	need = ()
	conflict = (
		"year",
		"month",
		"day",
		"weekNumMode",
		"weekDay",
		"start",
		"end",
		"cycleDays",
		"duration",
		"cycleLen",
	)
	# conflicts with all rules except for dayTime and dayTimeRange
	# (and possibly hourList, minuteList, secondList)
	# also conflict with "holiday" # FIXME

	def getServerString(self) -> str:
		y, m, d = self.date
		return f"{y:04d}/{m:02d}/{d:02d}"

	def __str__(self) -> str:
		return dateEncode(self.date)

	def __init__(self, parent: "Event") -> None:
		EventRule.__init__(self, parent)
		self.date = getSysDate(self.getCalType())

	def getData(self) -> str:
		return str(self)

	def setData(self, data: str) -> None:
		self.date = dateDecode(data)

	def getJd(self) -> int:
		year, month, day = self.date
		return to_jd(year, month, day, self.getCalType())

	def getEpoch(self) -> int:
		return self.getEpochFromJd(self.getJd())

	def setJd(self, jd: int) -> None:
		self.date = jd_to(jd, self.getCalType())

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: "Event",
	) -> OccurSet:
		myJd = self.getJd()
		if startJd <= myJd < endJd:
			return JdOccurSet({myJd})
		else:
			return JdOccurSet()

	def changeCalType(self, calType: int) -> bool:
		self.date = jd_to(self.getJd(), calType)
		return True


class DateAndTimeEventRule(DateEventRule):
	sgroup = 1
	params = (
		"date",
		"time",
	)

	def getServerString(self) -> str:
		y, m, d = self.date
		H, M, S = self.time
		return f"{y:04d}/{m:02d}/{d:02d} {H:02d}:{M:02d}:{S:02d}"

	def __init__(self, parent: "Event") -> None:
		DateEventRule.__init__(self, parent)
		self.time = localtime()[3:6]

	def getEpoch(self) -> int:
		return self.parent.getEpochFromJhms(
			self.getJd(),
			self.time[0],
			self.time[1],
			self.time[2],
		)

	def setEpoch(self, epoch: int) -> None:
		jd, h, m, s = self.parent.getJhmsFromEpoch(epoch)
		self.setJd(jd)
		self.time = (h, m, s)

	def setJdExact(self, jd: int) -> None:
		self.setJd(jd)
		self.time = (0, 0, 0)

	def setDate(self, date: Tuple[int, int, int]) -> None:
		if len(date) != 3:
			raise ValueError(f"DateAndTimeEventRule.setDate: bad date = {date!r}")
		self.date = date
		self.time = (0, 0, 0)

	def getDate(self, calType: int) -> Tuple[int, int, int]:
		return convert(
			self.date[0],
			self.date[1],
			self.date[2],
			self.getCalType(),
			calType,
		)

	def getData(self) -> Dict[str, str]:
		return {
			"date": dateEncode(self.date),
			"time": timeEncode(self.time),
		}

	def setData(self, arg: Union[Dict[str, str], str]) -> None:
		if isinstance(arg, dict):
			self.date = dateDecode(arg["date"])
			if "time" in arg:
				self.time = timeDecode(arg["time"])
		elif isinstance(arg, str):
			self.date = dateDecode(arg)
		else:
			raise BadEventFile(f"bad rule {self.name}={arg!r}")

	def getInfo(self) -> str:
		return (
			self.desc + ": " +
			dateEncode(self.date) + _(",") + " " +
			_("Time") + ": " + timeEncode(self.time)
		)


@classes.rule.register
class DayTimeEventRule(EventRule):  # Moment Event
	name = "dayTime"
	desc = _("Time in Day")
	provide = (
		"time",
	)
	conflict = (
		"dayTimeRange",
		"cycleLen",
	)
	params = (
		"dayTime",
	)

	def getServerString(self) -> str:
		H, M, S = self.dayTime
		return f"{H:02d}:{M:02d}:{S:02d}"

	def __init__(self, parent: "Event") -> None:
		EventRule.__init__(self, parent)
		self.dayTime = localtime()[3:6]

	def getData(self) -> str:
		return timeEncode(self.dayTime)

	def setData(self, data: str) -> None:
		self.dayTime = timeDecode(data)

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: "Event",
	) -> OccurSet:
		mySec = getSecondsFromHms(*self.dayTime)
		return TimeListOccurSet(  # FIXME
			self.getEpochFromJd(startJd) + mySec,
			self.getEpochFromJd(endJd) + mySec + 1,
			dayLen,
		)

	def getInfo(self) -> str:
		return _("Time in Day") + ": " + timeEncode(self.dayTime)


@classes.rule.register
class DayTimeRangeEventRule(EventRule):
	name = "dayTimeRange"
	desc = _("Day Time Range")
	conflict = (
		"dayTime",
		"cycleLen",
	)
	params = (
		"dayTimeStart",
		"dayTimeEnd",
	)

	def getServerString(self) -> str:
		H1, M1, S1 = self.dayTimeStart
		H2, M2, S2 = self.dayTimeEnd
		return f"{H1:02d}:{M1:02d}:{S1:02d} {H2:02d}:{M2:02d}:{S2:02d}"

	def __init__(self, parent) -> None:
		EventRule.__init__(self, parent)
		self.dayTimeStart = (0, 0, 0)
		self.dayTimeEnd = (24, 0, 0)

	def setRange(
		self,
		start: Tuple[int, int, int],
		end: Tuple[int, int, int],
	) -> None:
		self.dayTimeStart = tuple(start)
		self.dayTimeEnd = tuple(end)

	def getHourRange(self) -> Tuple[float, float]:
		return (
			timeToFloatHour(*self.dayTimeStart),
			timeToFloatHour(*self.dayTimeEnd),
		)

	def getSecondsRange(self) -> Tuple[int, int]:
		return (
			getSecondsFromHms(*self.dayTimeStart),
			getSecondsFromHms(*self.dayTimeEnd),
		)

	def getData(self) -> Tuple[str, str]:
		return (timeEncode(self.dayTimeStart), timeEncode(self.dayTimeEnd))

	def setData(self, data: Tuple[str, str]) -> None:
		return self.setRange(timeDecode(data[0]), timeDecode(data[1]))

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: "Event",
	) -> OccurSet:
		daySecStart = getSecondsFromHms(*self.dayTimeStart)
		daySecEnd = getSecondsFromHms(*self.dayTimeEnd)
		if daySecEnd <= daySecStart:
			daySecEnd = daySecStart
		tmList = []
		for jd in range(startJd, endJd):
			epoch = self.getEpochFromJd(jd)
			tmList.append((
				epoch + daySecStart,
				epoch + daySecEnd,
			))
		return IntervalOccurSet(tmList)


@classes.rule.register
class StartEventRule(DateAndTimeEventRule):
	name = "start"
	desc = _("Start")
	conflict = (
		"date",
	)

	# def getServerString(self) -> str: # in DateAndTimeEventRule

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: "Event",
	) -> OccurSet:
		return IntervalOccurSet.newFromStartEnd(
			max(self.getEpochFromJd(startJd), self.getEpoch()),
			self.getEpochFromJd(endJd),
		)


@classes.rule.register
class EndEventRule(DateAndTimeEventRule):
	name = "end"
	desc = _("End")
	conflict = (
		"date",
		"duration",
	)

	# def getServerString(self) -> str: # in DateAndTimeEventRule

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: "Event",
	) -> OccurSet:
		return IntervalOccurSet.newFromStartEnd(
			self.getEpochFromJd(startJd),
			min(self.getEpochFromJd(endJd), self.getEpoch()),
		)


@classes.rule.register
class DurationEventRule(EventRule):
	name = "duration"
	desc = _("Duration")
	need = (
		"start",
	)
	conflict = (
		"date",
		"end",
	)
	params = (
		"value",
		"unit",
	)
	sgroup = 1
	units = (1, 60, 3600, dayLen, 7 * dayLen)

	def __str__(self) -> str:
		return _("{count} " + self.getUnitDesc()).format(count=_(self.value))

	def getUnitDesc(self) -> str:
		return {
			1: "seconds",
			60: "minutes",
			3600: "hours",
			3600 * 24: "days",
			3600 * 24 * 7: "weeks",
		}[self.unit]

	def getServerString(self) -> str:
		return str(self.value) + " " + self.getUnitSymbol()

	def getUnitSymbol(self) -> str:
		return {
			1: "s",
			60: "m",
			3600: "h",
			3600 * 24: "d",
			3600 * 24 * 7: "w",
		}[self.unit]

	def __init__(self, parent: "RuleContainer") -> None:
		EventRule.__init__(self, parent)
		self.value = 0
		self.unit = 1  # seconds

	def getSeconds(self) -> str:
		return self.value * self.unit

	def setSeconds(self, s: int) -> None:
		for unit in reversed(self.units):
			if s % unit == 0:
				self.value, self.unit = int(s // unit), unit
				return
		self.unit, self.value = int(s), 1

	def setData(self, data: str) -> None:
		try:
			self.value, self.unit = durationDecode(data)
		except Exception as e:
			log.error(
				"Error while loading event rule \"{self.name}\": {e}"
			)

	def getData(self) -> str:
		return durationEncode(self.value, self.unit)

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: "Event",
	) -> OccurSet:
		parentStart, ok = self.parent["start"]
		if not ok:
			raise RuntimeError("parent has no start rule")
		myStartEpoch = parentStart.getEpoch()
		startEpoch = max(
			myStartEpoch,
			self.getEpochFromJd(startJd),
		)
		endEpoch = min(
			myStartEpoch + self.getSeconds(),
			self.getEpochFromJd(endJd),
		)
		return IntervalOccurSet.newFromStartEnd(
			startEpoch,
			endEpoch,
		)


def cycleDaysCalcOccurrence(
	days: int,
	startJd: int,
	endJd: int,
	event: "Event",
) -> OccurSet:
	eStartJd = event.getStartJd()
	if startJd <= eStartJd:
		startJd = eStartJd
	else:
		startJd = eStartJd + ((startJd - eStartJd - 1) // days + 1) * days
	return JdOccurSet(range(
		startJd,
		endJd,
		days,
	))


@classes.rule.register
class CycleDaysEventRule(EventRule):
	name = "cycleDays"
	desc = _("Cycle (Days)")
	need = (
		"start",
	)
	conflict = (
		"date",
		"cycleWeeks",
		"cycleLen",
		"weekMonth",
	)
	params = (
		"days",
	)

	def getServerString(self) -> str:
		return str(self.days)

	def __init__(self, parent: "Event") -> None:
		EventRule.__init__(self, parent)
		self.days = 7

	def getData(self) -> int:
		return self.days

	def setData(self, days: int) -> None:
		self.days = days

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: "Event",
	) -> OccurSet:
		return cycleDaysCalcOccurrence(self.days, startJd, endJd, event)

	def getInfo(self) -> str:
		return _("Repeat: Every {days} Days").format(days=_(self.days))


@classes.rule.register
class CycleWeeksEventRule(EventRule):
	name = "cycleWeeks"
	desc = _("Cycle (Weeks)")
	need = (
		"start",
	)
	conflict = (
		"date",
		"cycleDays",
		"cycleLen",
		"weekMonth",
	)
	params = (
		"weeks",
	)

	def getServerString(self) -> str:
		return str(self.weeks)

	def __init__(self, parent: "RuleContainer") -> None:
		EventRule.__init__(self, parent)
		self.weeks = 1

	def getData(self) -> int:
		return self.weeks

	def setData(self, weeks: int) -> None:
		self.weeks = weeks

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: "Event",
	) -> OccurSet:
		return cycleDaysCalcOccurrence(
			self.weeks * 7,
			startJd,
			endJd,
			event,
		)

	def getInfo(self) -> str:
		return _("Repeat: Every {weeks} Weeks").format(weeks=_(self.weeks))


@classes.rule.register
class CycleLenEventRule(EventRule):
	name = "cycleLen"  # or "cycle" FIXME
	desc = _("Cycle (Days & Time)")
	provide = (
		"time",
	)
	need = (
		"start",
	)
	conflict = (
		"date",
		"dayTime",
		"dayTimeRange",
		"cycleDays",
		"cycleWeeks",
		"weekMonth",
	)
	params = (
		"days",
		"extraTime",
	)

	def getServerString(self) -> str:
		H, M, S = self.extraTime
		return f"{self.days} {H:02d}:{M:02d}:{S:02d}"

	def __init__(self, parent: "RuleContainer") -> None:
		EventRule.__init__(self, parent)
		self.days = 7
		self.extraTime = (0, 0, 0)

	def getData(self) -> Dict[str, Any]:
		return {
			"days": self.days,
			"extraTime": timeEncode(self.extraTime),
		}

	def setData(self, arg: Dict[str, Any]) -> None:
		self.days = arg["days"]
		self.extraTime = timeDecode(arg["extraTime"])

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: "Event",
	) -> OccurSet:
		startEpoch = self.getEpochFromJd(startJd)
		eventStartEpoch = event.getStartEpoch()
		##
		cycleSec = self.days * dayLen + getSecondsFromHms(*self.extraTime)
		##
		if startEpoch <= eventStartEpoch:
			startEpoch = eventStartEpoch
		else:
			startEpoch = eventStartEpoch + cycleSec * (
				(startEpoch - eventStartEpoch - 1) // cycleSec + 1
			)
		##
		return TimeListOccurSet(
			startEpoch,
			self.getEpochFromJd(endJd),
			cycleSec,
		)

	def getInfo(self) -> str:
		return _("Repeat: Every {days} Days and {hms}").format(
			days=_(self.days),
			hms=timeEncode(self.extraTime),
		)


@classes.rule.register
class ExYearEventRule(YearEventRule):
	name = "ex_year"
	desc = "[" + _("Exception") + "] " + _("Year")

	def jdMatches(self, jd: int) -> bool:
		return not YearEventRule.jdMatches(self, jd)


@classes.rule.register
class ExMonthEventRule(MonthEventRule):
	name = "ex_month"
	desc = "[" + _("Exception") + "] " + _("Month")
	conflict = (
		"date",
		"month",
		"weekMonth",
	)

	def jdMatches(self, jd: int) -> bool:
		return not MonthEventRule.jdMatches(self, jd)


@classes.rule.register
class ExDayOfMonthEventRule(DayOfMonthEventRule):
	name = "ex_day"
	desc = "[" + _("Exception") + "] " + _("Day of Month")

	def jdMatches(self, jd: int) -> bool:
		return not DayOfMonthEventRule.jdMatches(self, jd)


@classes.rule.register
class ExDatesEventRule(EventRule):
	name = "ex_dates"
	desc = "[" + _("Exception") + "] " + _("Date")
	# conflict = ("date",)  # FIXME
	params = (
		"dates",
	)

	def getServerString(self) -> str:
		return " ".join(
			f"{y:04d}/{m:02d}/{d:02d}"
			for y, m, d in self.dates
		)

	def __init__(self, parent) -> None:
		EventRule.__init__(self, parent)
		self.setDates([])

	def setDates(self, dates: List[Tuple[int, int, int]]) -> None:
		self.dates = dates
		self.jdList = [to_jd(y, m, d, self.getCalType()) for y, m, d in dates]

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: "Event",
	) -> OccurSet:
		# improve performance # FIXME
		return JdOccurSet(
			set(range(startJd, endJd)).difference(self.jdList)
		)

	def getData(self) -> List[str]:
		datesConf = []
		for date in self.dates:
			datesConf.append(dateEncode(date))
		return datesConf

	def setData(
		self,
		datesConf: Union[str, List[Union[str, tuple, list]]],
	) -> None:
		dates = []
		if isinstance(datesConf, str):
			for date in datesConf.split(","):
				dates.append(dateDecode(date.strip()))
		else:
			for date in datesConf:
				if isinstance(date, str):
					date = dateDecode(date)
				elif isinstance(date, (tuple, list)):
					checkDate(date)
				dates.append(date)
		self.setDates(dates)

	def changeCalType(self, calType: int) -> bool:
		dates = []
		for jd in self.jdList:
			dates.append(jd_to(jd, calType))
		self.dates = dates


# TODO
# @classes.rule.register
# class HolidayEventRule(EventRule):
# 	name = "holiday"
# 	desc = _("Holiday")
# 	conflict = ("date",)


# TODO
# @classes.rule.register
# class ShowInMCalEventRule(EventRule):
# 	name = "show_cal"
# 	desc = _("Show in Calendar")

# TODO
# @classes.rule.register
# class SunTimeRule(EventRule):
# # ... minutes before Sun Rise      eval("sunRise-x")
# # ... minutes after Sun Rise       eval("sunRise+x")
# # ... minutes before Sun Set       eval("sunSet-x")
# # ... minutes after Sun Set        eval("sunSet+x")

###########################################################################
###########################################################################


# Should not be registered, or instantiate directly
@classes.notifier.setMain
class EventNotifier(SObj):
	name = ""
	desc = ""
	params = ()

	def __init__(self, event: "Event") -> None:
		self.event = event

	def getCalType(self) -> str:
		return self.event.calType

	def notify(self, finishFunc: Callable) -> None:
		pass


@classes.notifier.register
class AlarmNotifier(EventNotifier):
	name = "alarm"
	desc = _("Alarm")
	params = (
		"alarmSound",
		"playerCmd",
	)

	def __init__(self, event: "Event") -> None:
		EventNotifier.__init__(self, event)
		self.alarmSound = ""  # FIXME
		self.playerCmd = "mplayer"


@classes.notifier.register
class FloatingMsgNotifier(EventNotifier):
	name = "floatingMsg"
	desc = _("Floating Message")
	params = (
		"fillWidth",
		"speed",
		"bgColor",
		"textColor",
	)

	def __init__(self, event: "Event") -> None:
		EventNotifier.__init__(self, event)
		###
		self.fillWidth = False
		self.speed = 100
		self.bgColor = (255, 255, 0)
		self.textColor = (0, 0, 0)


@classes.notifier.register
class WindowMsgNotifier(EventNotifier):
	name = "windowMsg"
	desc = _("Message Window")  # FIXME
	params = (
		"extraMessage",
	)

	def __init__(self, event: "Event") -> None:
		EventNotifier.__init__(self, event)
		self.extraMessage = ""
		# window icon, FIXME


# @classes.notifier.register  # FIXME
class CommandNotifier(EventNotifier):
	name = "command"
	desc = _("Run a Command")
	params = (
		"command",
		"pyEval",
	)

	def __init__(self, event: "Event") -> None:
		EventNotifier.__init__(self, event)
		self.command = ""
		self.pyEval = False


###########################################################################
###########################################################################


class RuleContainer:
	requiredRules = ()
	supportedRules = None  # None means all rules are supported
	params = (
		"timeZoneEnable",
		"timeZone",
	)
	paramsOrder = (
		"timeZoneEnable",
		"timeZone",
	)

	@staticmethod
	def copyRulesDict(rulesOd: Dict[str, EventRule]) -> Dict[str, EventRule]:
		newRulesOd = OrderedDict()
		for ruleName, rule in rulesOd.items():
			newRulesOd[ruleName] = rule.copy()
		return newRulesOd

	def __init__(self) -> None:
		self.timeZoneEnable = False
		self.timeZone = ""
		###
		self.clearRules()
		self.rulesHash = None

	def clearRules(self) -> None:
		self.rulesOd = OrderedDict()

	def getRule(self, key: str) -> "EventRule":
		return self.rulesOd.__getitem__(key)

	def getRuleIfExists(self, key: str) -> "Optional[EventRule]":
		return self.rulesOd.get(key)

	def setRule(self, key: str, value: "EventRule"):
		return self.rulesOd.__setitem__(key, value)

	def iterRulesData(self) -> Iterator[Tuple[str, Any]]:
		for rule in self.rulesOd.values():
			yield rule.name, rule.getData()

	def getRulesData(self) -> List[Tuple[str, Any]]:
		return list(self.iterRulesData())

	def getRulesHash(self) -> int:
		return hash(str(
			(
				self.getTimeZoneStr(),
				sorted(self.iterRulesData()),
			)
		))

	def getRuleNames(self) -> List[str]:
		return list(self.rulesOd.keys())

	def addRule(self, rule: "EventRule") -> None:
		self.rulesOd.__setitem__(rule.name, rule)

	def addNewRule(self, ruleType: str) -> "EventRule":
		rule = classes.rule.byName[ruleType](self)
		self.addRule(rule)
		return rule

	def getAddRule(self, ruleType: str) -> "EventRule":
		rule = self.getRuleIfExists(ruleType)
		if rule is not None:
			return rule
		return self.addNewRule(ruleType)

	def removeRule(self, rule: "EventRule") -> None:
		self.rulesOd.__delitem__(rule.name)

	def __delitem__(self, key: str) -> None:
		self.rulesOd.__delitem__(key)

	# returns (rule, found) where found is boolean
	def __getitem__(self, key: str) -> Tuple[Optional["EventRule"], bool]:
		rule = self.getRuleIfExists(key)
		if rule is None:
			return None, False
		return rule, True

	def __setitem__(self, key: str, value: "EventRule") -> None:
		self.setRule(key, value)

	def __iter__(self) -> Iterator["EventRule"]:
		return iter(self.rulesOd.values())

	def setRulesData(self, rulesData: List[Tuple[str, Any]]) -> None:
		self.clearRules()
		for ruleName, ruleData in rulesData:
			rule = classes.rule.byName[ruleName](self)
			rule.setData(ruleData)
			self.addRule(rule)

	def addRequirements(self) -> None:
		for name in self.requiredRules:
			if name not in self.rulesOd:
				self.addNewRule(name)

	def checkAndAddRule(self, rule: "EventRule") -> Tuple[bool, str]:
		ok, msg = self.checkRulesDependencies(newRule=rule)
		if ok:
			self.addRule(rule)
		return (ok, msg)

	def removeSomeRuleTypes(self, *rmTypes) -> None:
		for ruleType in rmTypes:
			if ruleType in self.rulesOd:
				del self.rulesOd[ruleType]

	def checkAndRemoveRule(self, rule: "EventRule") -> Tuple[bool, str]:
		ok, msg = self.checkRulesDependencies(disabledRule=rule)
		if ok:
			self.removeRule(rule)
		return (ok, msg)

	def checkRulesDependencies(
		self,
		newRule: "Optional[EventRule]" = None,
		disabledRule: "Optional[EventRule]" = None,
		autoCheck: bool = True,
	) -> Tuple[bool, str]:
		rulesOd = self.rulesOd.copy()
		if newRule:
			rulesOd[newRule.name] = newRule
		if disabledRule:
			if disabledRule.name in rulesOd:
				del rulesOd[disabledRule.name]
		provideList = []
		for ruleName, rule in rulesOd.items():
			provideList.append(ruleName)
			provideList += rule.provide
		for rule in rulesOd.values():
			for conflictName in rule.conflict:
				if conflictName in provideList:
					return (
						False,
						_(
							"Conflict between \"{rule1}\" and \"{rule2}\""
						).format(
							rule1=_(rule.desc),
							rule2=_(rulesOd[conflictName].desc),
						),
					)
			for needName in rule.need:
				if needName not in provideList:
					# TODO: find which rule(s) provide(s) `needName`
					return (
						False,
						_("\"{rule1}\" needs \"{rule2}\"").format(
							rule1=_(rule.desc),
							rule2=_(needName),
						),
					)
		return (True, "")

	def copyRulesFrom(self, other: "EventRule") -> None:
		for ruleType, rule in other.rulesOd.items():
			if self.supportedRules is None or ruleType in self.supportedRules:
				self.getAddRule(ruleType).copyFrom(rule)

	def copySomeRuleTypesFrom(
		self,
		other: "EventRule",
		*ruleTypes: Tuple[str]
	) -> None:
		for ruleType in ruleTypes:
			if ruleType not in self.supportedRules:
				log.info(
					f"copySomeRuleTypesFrom: unsupported rule {ruleType}" +
					f" for container {self!r}"
				)
				continue
			rule = other.getRuleIfExists(ruleType)
			if rule is None:
				continue
			self.getAddRule(ruleType).copyFrom(rule)

	def getTimeZoneObj(self):
		if self.timeZoneEnable and self.timeZone:
			# natz.gettz does not raise exception, returns None if invalid
			tz = natz.gettz(self.timeZone)
			if tz:
				return tz
		return core.localTz

	def getTimeZoneStr(self):
		return str(self.getTimeZoneObj())

	def getEpochFromJd(self, jd):
		return getEpochFromJd(jd, tz=self.getTimeZoneObj())

	def getJdFromEpoch(self, jd):
		return getJdFromEpoch(jd, tz=self.getTimeZoneObj())

	def getJhmsFromEpoch(self, epoch):
		return getJhmsFromEpoch(epoch, tz=self.getTimeZoneObj())

	def getEpochFromJhms(self, jd, h, m, s):
		return getEpochFromJhms(jd, h, m, s, tz=self.getTimeZoneObj())


def iconAbsToRelativelnData(data):
	icon = data["icon"]
	iconDir, iconName = split(icon)
	if iconName == "obituary.png":
		iconName = "green_clover.svg"
	if iconDir == "event":
		icon = iconName
	elif iconDir == join(svgDir, "event"):
		icon = iconName
	elif iconDir == join(pixDir, "event"):
		icon = iconName
	data["icon"] = icon


def iconRelativeToAbsInObj(self):
	icon = self.icon
	if icon and not isabs(icon):
		if not "/" in icon:
			icon = join("event", icon)
		if icon.endswith(".png"):
			icon = join(pixDir, icon)
		else:
			icon = join(svgDir, icon)
	self.icon = icon

###########################################################################
###########################################################################


class WithIcon:
	def getIcon(self):
		return self.icon

	def getIconRel(self):
		icon = self.icon
		for direc in (svgDir, pixDir):
			if icon.startswith(direc + os.sep):
				return icon[len(direc)+1:]
		return icon


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
		for _id in range(1, lastIds.event + 1):
			fpath = cls.getFile(_id)
			if not fs.isfile(fpath):
				continue
			yield fpath

	@classmethod
	def getSubclass(cls, _type):
		return classes.event.byName[_type]

	@classmethod
	def getDefaultIcon(cls):
		return join(
			pixDir,
			"event",
			cls.iconName + ".png"
		) if cls.iconName else ""

	def getPath(self):
		if self.parent is None:
			raise RuntimeError("getPath: parent is None")
		path = SObj.getPath(self)
		if len(path) != 2:
			raise RuntimeError(f"getPath: unexpected path={path}")
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
		######
		RuleContainer.__init__(self)
		self.timeZoneEnable = not self.isAllDay
		self.notifiers = []
		self.notifyBefore = (0, 1)  # (value, unit) like DurationEventRule
		# self.snoozeTime = (5, 60)  # (value, unit) like DurationEventRule, FIXME
		self.addRequirements()
		self.setDefaults(group=parent)
		######
		self.modified = now()  # FIXME
		self.remoteIds = None
		# remoteIds is (accountId, groupId, eventId)
		#           OR (accountId, groupId, eventId, sha1)
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
		else:
			return self.description.split("\n")[0]

	def afterModify(self):
		if self.id is None:
			self.setId()
		self.modified = now()  # FIXME
		# self.parent.eventsModified = self.modified
		###
		if self.parent and self.id in self.parent.idList:
			rulesHash = self.getRulesHash()
			# what if self.notifyBefore is changed? BUG FIXME
			if rulesHash != self.rulesHash:
				self.parent.updateOccurrenceEvent(self)
				self.rulesHash = rulesHash
		else:  # None or enbale=False
			self.rulesHash = ""

	def getNotifyBeforeSec(self):
		return self.notifyBefore[0] * self.notifyBefore[1]

	def getNotifyBeforeMin(self):
		return int(self.getNotifyBeforeSec() / 60)

	def setDefaults(self, group=None):
		"""
			sets default values that depends on event type and group type
			as well as common parameters, like those are set in __init__
			should call this method from parent event class
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
		lines = []
		lines.append(_("Type") + ": " + self.desc)
		lines.append(_("Calendar Type") + ": " + calType.desc)
		lines.append(_("Summary") + ": " + self.getSummary())
		lines.append(_("Description") + ": " + self.description)
		# "notifiers",
		# "notifyBefore",
		# "remoteIds",
		# "lastMergeSha1",
		# "modified",

		rulesDict = self.rulesOd.copy()
		for rule in rulesDict.values():
			lines.append(rule.getInfo())

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
		# 	for fname in listdir(self.filesDir):
		# 		# FIXME
		# 		if isfile(join(self.filesDir, fname)) and not fname.endswith("~"):
		# 			self.files.append(fname)

	# def getUrlForFile(self, fname):
	# 	return "file:" + os.sep*2 + self.filesDir + os.sep + fname

	def getFilesUrls(self):
		data = []
		baseUrl = self.getUrlForFile("")
		for fname in self.files:
			data.append((
				baseUrl + fname,
				_("File") + ": " + fname,
			))
		return data

	def getSummary(self):
		return self.summary

	def getDescription(self):
		return self.description

	def getTextParts(self, showDesc=True):
		summary = self.getSummary()
		##
		if self.timeZoneEnable and self.timeZone:
			if natz.gettz(self.timeZone) is None:
				invalidTZ = _("Invalid Time Zone: {timeZoneName}").format(
					timeZoneName=self.timeZone,
				)
				summary = "(" + invalidTZ + ")" + summary
		####
		description = self.getDescription()
		if showDesc and description:
			if self.parent is not None:
				sep = self.parent.eventTextSep
			else:
				sep = core.eventTextSep
			return (summary, sep, description)
		else:
			return (summary,)

	def getText(self, showDesc=True):
		return "".join(self.getTextParts(showDesc))

	def setId(self, _id=None):
		if _id is None or _id < 0:
			_id = lastIds.event + 1  # FIXME
			lastIds.event = _id
		elif _id > lastIds.event:
			lastIds.event = _id
		self.id = _id
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
		####
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
		data.update({
			"type": self.name,
			"calType": calTypes.names[self.calType],
			"rules": self.getRulesData(),
			"notifiers": self.getNotifiersData(),
			"notifyBefore": durationEncode(*self.notifyBefore),
		})
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
				raise ValueError(f"Invalid calType: '{calType}'")
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

	def calcOccurrence(self, startJd: int, endJd: int) -> OccurSet:
		"""
			startJd and endJd are float jd
		"""
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
			occur = occur.intersection(rule.calcOccurrence(
				ruleStartJd,
				ruleEndJd,
				self,
			))
		occur.event = self
		return occur  # FIXME

	def calcOccurrenceAll(self):
		return self.calcOccurrence(self.parent.startJd, self.parent.endJd)

	# FIXME: too tricky!
	# def calcFirstOccurrenceAfterJd(self, startJd):

	def notify(self, finishFunc: Callable) -> None:
		self.n = len(self.notifiers)

		def notifierFinishFunc():
			self.n -= 1
			if self.n <= 0:
				try:
					finishFunc()
				except Exception:
					pass

		for notifier in self.notifiers:
			notifier.notify(notifierFinishFunc)

	def getIcsData(self, prettyDateTime=False):  # FIXME
		return None

	def setIcsData(self, data):
		"""
		if "T" in data["DTSTART"]:
			return False
		if "T" in data["DTEND"]:
			return False
		startJd = ics.getJdByIcsDate(data["DTSTART"])
		endJd = ics.getJdByIcsDate(data["DTEND"])
		if "RRULE" in data:
			rrule = dict(ics.splitIcsValue(data["RRULE"]))
			if rrule["FREQ"] == "YEARLY":
				y0, m0, d0 = jd_to(startJd, self.calType)
				y1, m1, d1 = jd_to(endJd, self.calType)
				if y0 != y1:  # FIXME
					return False
				yr = self.getAddRule("year")
				interval = int(rrule.get("INTERVAL", 1))

			elif rrule["FREQ"] == "MONTHLY":
				pass
			elif rrule["FREQ"] == "WEEKLY":
				pass
		"""
		return False

	def changeCalType(self, calType) -> bool:
		backupRulesOd = RuleContainer.copyRulesDict(self.rulesOd)
		if calType != self.calType:
			for rule in self.rulesOd.values():
				if not rule.changeCalType(calType):
					log.info(f"changeCalType: failed because of rule {rule.name}={rule}")
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

	def setJd(self, jd: int) -> None:
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
		oldEvent = self.getRevision(sinceHash)
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
				items.append({
					"fieldName": fieldName,
					"oldValue": oldValue,
					"newValue": newValue,
				})
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
			("DTSTART", ics.getIcsTimeByEpoch(
				self.getStartEpoch(),
				prettyDateTime,
			)),
			("DTEND", ics.getIcsTimeByEpoch(
				self.getEndEpoch(),
				prettyDateTime,
			)),
			("TRANSP", "OPAQUE"),
			("CATEGORIES", self.name),  # FIXME
		]

	def calcOccurrence(self, startJd: int, endJd: int) -> OccurSet:
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
	requiredRules = (
		"start",
	)
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
		data.update({
			"startTime": jsonTimeFromEpoch(self["start"].getEpoch()),
			"endTime": jsonTimeFromEpoch(self.getEndEpoch()),
			"durationUnit": durationUnit,
		})
		return data

	def setDefaults(self, group=None):
		Event.setDefaults(self, group=group)
		self.setStart(
			getSysDate(self.calType),
			tuple(localtime()[3:6]),
		)
		if group and group.name == "taskList":
			value, unit = group.defaultDuration
			self.setEnd("duration", value, unit)
		else:
			self.setEnd("duration", 1, 3600)

	def setJdExact(self, jd: int) -> None:
		self.getAddRule("start").setJdExact(jd)
		self.setEnd("duration", 24, 3600)

	def setStart(self, date, dayTime):
		start, ok = self["start"]
		if not ok:
			raise KeyError("rule \"start\" not found")
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
			raise ValueError(f"invalid endType={endType!r}")
		self.addRule(rule)

	def getStart(self):
		start, ok = self["start"]
		if not ok:
			raise KeyError("rule \"start\" not found")
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
			else:
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
			duration.value -= float(newStartEpoch - start.getEpoch()) / duration.unit
		start.setEpoch(newStartEpoch)

	def modifyEnd(self, newEndEpoch):
		end, ok = self["end"]
		if ok:
			end.setEpoch(newEndEpoch)
		else:
			duration, ok = self["duration"]
			if ok:
				duration.value = float(newEndEpoch - self.getStartEpoch()) / duration.unit
			else:
				raise RuntimeError("no end rule nor duration rule")

	def copyFrom(self, other, *a, **kw):
		Event.copyFrom(self, other, *a, **kw)
		myStart, ok = self["start"]
		if not ok:
			raise KeyError
		##
		if other.name == self.name:
			endType, values = other.getEnd()
			self.setEnd(endType, *values)
		else:
			if other.name == "dailyNote":
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
	requiredRules = (
		"start",
	)
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
		data.update({
			"startJd": self["start"].getJd(),
			"endJd": self.getEndJd(),
			"durationEnable": durationEnable,
		})
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
			rule.setJd(self.getJdFromEpoch(values[0]))
		elif endType == "duration":
			rule = DurationEventRule(self)
			rule.value = value
			rule.unit = dayLen
		else:
			raise ValueError(f"invalid endType={endType!r}")
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
			return end.getJd()
		duration, ok = self["duration"]
		if ok:
			start, ok = self["start"]
			if not ok:
				raise RuntimeError("no start rule")
			return start.getJd() + duration.getSeconds() // dayLen
		raise ValueError("no end date neither duration specified for task")

	def getEndEpoch(self):
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
	requiredRules = (
		"date",
	)
	supportedRules = (
		"date",
	)
	isAllDay = True

	def getServerData(self):
		data = Event.getServerData(self)
		data.update({
			"jd": self.getJd(),
		})
		return data

	def getDate(self):
		rule, ok = self["date"]
		if ok:
			return rule.date

	def setDate(self, year, month, day):
		rule, ok = self["date"]
		if not ok:
			raise KeyError("no date rule")
		rule.date = (year, month, day)

	def getJd(self) -> int:
		rule, ok = self["date"]
		if ok:
			return rule.getJd()

	def setJd(self, jd: int) -> None:
		rule, ok = self["date"]
		if ok:
			return rule.setJd(jd)

	def setDefaults(self, group=None):
		Event.setDefaults(self, group=group)
		self.setDate(*getSysDate(self.calType))

	# startJd and endJd can be float jd
	def calcOccurrence(self, startJd, endJd) -> OccurSet:
		jd = self.getJd()
		return JdOccurSet(
			[jd] if startJd <= jd < endJd else []
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
		data.update({
			"month": self.getMonth(),
			"day": self.getDay(),
		})
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

	def setMonth(self, month):
		return self.getAddRule("month").setData(month)

	def getDay(self):
		rule, ok = self["day"]
		if ok:
			return rule.values[0]

	def setDay(self, day):
		return self.getAddRule("day").setData(day)

	def setDefaults(self, group=None):
		Event.setDefaults(self, group=group)
		y, m, d = getSysDate(self.calType)
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

	def calcOccurrence(self, startJd, endJd) -> OccurSet:  # float jd
		calType = self.calType
		month = self.getMonth()
		day = self.getDay()
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
		for year in range(startYear + 1, endYear):
			jds.add(to_jd(year, month, day, calType))
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
		else:
			try:
				startYear = jd_to(self.parent.startJd, GREGORIAN)[0]
			except AttributeError:
				pass
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
		data.update({
			"startJd": self["start"].getJd(),
			"endJd": self["end"].getJd(),
			"day": self.getDay(),
			"dayStartSeconds": startSec,
			"dayEndSeconds": endSec,
		})
		return data

	def setJd(self, jd: int) -> None:
		year, month, day = jd_to(jd, self.calType)
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

	def setDefaults(self, group=None):
		Event.setDefaults(self, group=group)
		self.setJd(core.getCurrentJd())

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
		data.update({
			"startJd": self["start"].getJd(),
			"endJd": self["end"].getJd(),
			"cycleWeeks": self["cycleWeeks"].getData(),
			"dayStartSeconds": startSec,
			"dayEndSeconds": endSec,
		})
		return data

	def setDefaults(self, group=None):
		Event.setDefaults(self, group=group)
		self.setJd(core.getCurrentJd())

	def setJd(self, jd: int) -> None:
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
	params = Event.params + (
		"courseId",
	)
	isAllDay = False

	def getServerData(self):
		data = Event.getServerData(self)
		startSec, endSec = self["dayTimeRange"].getSecondsRange()
		data.update({
			"weekNumMode": self["weekNumMode"].getData(),
			"weekDayList": self["weekDay"].getData(),
			"dayStartSeconds": startSec,
			"dayEndSeconds": endSec,
			"courseId": self.courseId,
		})
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
			_("{courseName} Class").format(courseName=self.getCourseName()) +
			" (" + self.getWeekDayName() + ")"
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
		occur = self.calcOccurrence(startJd, endJd)
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
			("DTSTART", ics.getIcsTimeByEpoch(
				tRangeList[0][0],
				prettyDateTime,
			)),
			("DTEND", ics.getIcsTimeByEpoch(
				tRangeList[0][1],
				prettyDateTime,
			)),
			(
				"RRULE",
				f"FREQ=WEEKLY;UNTIL={until};INTERVAL={interval};BYDAY={byDay}"
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
	params = DailyNoteEvent.params + (
		"courseId",
	)
	isAllDay = False

	def getServerData(self):
		data = Event.getServerData(self)
		startSec, endSec = self["dayTimeRange"].getSecondsRange()
		data.update({
			"jd": self.getJd(),
			"dayStartSeconds": startSec,
			"dayEndSeconds": endSec,
			"courseId": self.courseId,
		})
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

	def calcOccurrence(self, startJd: int, endJd: int) -> OccurSet:
		jd = self.getJd()
		if startJd <= jd < endJd:
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
					)
				]
			)
		else:
			return IntervalOccurSet()

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
			("DTSTART", ics.getIcsTimeByEpoch(
				dayStart + startSec,
				prettyDateTime,
			)),
			("DTEND", ics.getIcsTimeByEpoch(
				dayStart + endSec,
				prettyDateTime
			)),
			("TRANSP", "OPAQUE"),
		]


@classes.event.register
class LifeTimeEvent(SingleStartEndEvent):
	name = "lifeTime"
	nameAlias = "lifetime"
	desc = _("Life Time Event")
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
		data.update({
			"startJd": self["start"].getJd(),
			"endJd": self["end"].getJd(),
		})
		return data

	def setJd(self, jd: int) -> None:
		self.getAddRule("start").setJdExact(jd)
		self.getAddRule("end").setJdExact(jd)

	def addRule(self, rule):
		if rule.name in ("start", "end"):
			rule.time = (0, 0, 0)
		SingleStartEndEvent.addRule(self, rule)

	def modifyPos(self, newStartEpoch):
		start, ok = self["start"]
		end, ok = self["end"]
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
		data.update({
			"scale": self.scale,
			"start": self.start,
			"end": self.end,
			"durationEnable": self.endRel,
		})
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
		return hash(str((
			self.getTimeZoneStr(),
			"largeScale",
			self.scale,
			self.start,
			self.end,
			self.endRel,
		)))
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

	def calcOccurrence(self, startJd: int, endJd: int) -> OccurSet:
		myStartJd = iceil(to_jd(
			int(self.scale * self.start),
			1,
			1,
			self.calType,
		))
		myEndJd = ifloor(to_jd(
			int(self.scale * self.getEnd()),
			1,
			1,
			self.calType,
		))
		return IntervalOccurSet.newFromStartEnd(
			max(
				self.getEpochFromJd(myStartJd),
				self.getEpochFromJd(startJd),
			),
			min(
				self.getEpochFromJd(myEndJd),
				self.getEpochFromJd(endJd),
			)
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
		data.update({
			"rules": [
				{
					"type": ruleName,
					"value": rule.getServerString(),
				}
				for ruleName, rule in rulesOd.items()
			],
		})
		return data

###########################################################################
###########################################################################


class EventContainer(BsonHistEventObj):
	name = ""
	desc = ""
	basicParams = (
		"idList",  # FIXME
		"uuid",
	)
	# BsonHistEventObj.params is empty
	params = (
		"timeZoneEnable",
		"timeZone",
		"icon",
		"title",
		"showFullEventDesc",
		"idList",
		"modified",
		"uuid",
	)

	def __getitem__(self, key):
		if isinstance(key, int):  # eventId
			return self.getEvent(key)
		else:
			raise TypeError(
				f"invalid key type for {key!r} " +
				"given to EventContainer.__getitem__"
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
		######
		self.uuid = None
		self.modified = now()
		# self.eventsModified = self.modified

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
				f"error while loading event file {eventFile!r}: " +
				f"file not found. eid={eid}, container={self!r}"
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
		event.setData(data)
		event.lastHash = lastHash
		event.modified = lastEpoch
		return event

	def __iter__(self):
		for eid in self.idList:
			try:
				event = self.getEvent(eid)
			except Exception as e:
				log.exception("")
			else:
				yield event

	def __len__(self):
		return len(self.idList)

	def preAdd(self, event):
		if event.id in self.idList:
			raise ValueError(f"{self} already contains {event}")
		if event.parent not in (None, self):
			raise ValueError(
				f"{event} already has a parent={event.parent}" +
				f", trying to add to {self}"
			)

	def postAdd(self, event):
		event.parent = self  # needed? FIXME

	def insert(self, index, event):
		self.preAdd(event)
		self.idList.insert(index, event.id)
		self.postAdd(event)

	def append(self, event):
		self.preAdd(event)
		self.idList.append(event.id)
		self.postAdd(event)

	def index(self, eid):
		return self.idList.index(eid)

	def moveUp(self, index):
		return self.idList.insert(index - 1, self.idList.pop(index))

	def moveDown(self, index):
		return self.idList.insert(index + 1, self.idList.pop(index))

	def remove(self, event):  # call when moving to trash
		"""
			excludes event from this container (group or trash),
			not delete event data completely
			and returns the index of (previously contained) event
		"""
		index = self.idList.index(event.id)
		self.idList.remove(event.id)
		event.parent = None
		return index

	def copyFrom(self, other):
		BsonHistEventObj.copyFrom(self, other)
		self.calType = other.calType

	def getData(self):
		data = BsonHistEventObj.getData(self)
		data["calType"] = calTypes.names[self.calType]
		iconAbsToRelativelnData(data)
		return data

	def setData(self, data) -> None:
		BsonHistEventObj.setData(self, data)
		if "calType" in data:
			calType = data["calType"]
			try:
				self.calType = calTypes.names.index(calType)
			except ValueError:
				raise ValueError(f"Invalid calType: '{calType}'")
		###
		iconRelativeToAbsInObj(self)


class EventGroupsImportResult:
	def __init__(self):
		self.newGroupIds = set()  # type: Set[int]
		self.newEventIds = set()  # type: Set[Tuple[int, int]]
		self.modifiedEventIds = set()  # type: Set[Tuple[int, int]]

	def __add__(
		self,
		other: "EventGroupsImportResult",
	) -> "EventGroupsImportResult":
		r = EventGroupsImportResult()
		r.newGroupIds = self.newGroupIds | other.newGroupIds
		r.newEventIds = self.newEventIds | other.newEventIds
		r.modifiedEventIds = self.modifiedEventIds | other.modifiedEventIds
		return r


@classes.group.register
@classes.group.setMain
class EventGroup(EventContainer):
	name = "group"
	desc = _("Event Group")
	acceptsEventTypes = (
		"yearly",
		"dailyNote",
		"task",
		"allDayTask",
		"weekly",
		"monthly",
		"lifeTime",
		"largeScale",
		"custom",
	)
	canConvertTo = ()
	actions = []  # [("Export to ICS", "exportToIcs")]
	eventActions = []  # FIXME
	sortBys = (
		# name, description, is_type_dependent
		("calType", _("Calendar Type"), False),
		("summary", _("Summary"), False),
		("description", _("Description"), False),
		("icon", _("Icon"), False),
	)
	sortByDefault = "summary"
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
	simpleFilters = {
		"text": lambda event, text:
			not text or text in event.getText(),
		"text_lower": lambda event, text:
			not text or text in event.getText().lower(),
		"modified_from": lambda event, epoch:
			event.modified >= epoch,
		"type": lambda event, _type:
			event.name == _type,
		"timezone": lambda event, timeZone:
			event.timeZone == timeZone
			if timeZone else not event.timeZoneEnable
	}

	@classmethod
	def getFile(cls, _id):
		return join(groupsDir, f"{_id}.json")

	@classmethod
	def iterFiles(cls, fs: FileSystem):
		for _id in range(1, lastIds.group + 1):
			fpath = cls.getFile(_id)
			if not fs.isfile(fpath):
				continue
			yield fpath

	@classmethod
	def getSubclass(cls, _type):
		return classes.group.byName[_type]

	def getTimeZoneObj(self):
		if self.timeZoneEnable and self.timeZone:
			tz = natz.gettz(self.timeZone)
			if tz:
				return tz
		return core.localTz

	def getEpochFromJd(self, jd):
		return getEpochFromJd(jd, tz=self.getTimeZoneObj())

	def getStartEpoch(self):
		return self.getEpochFromJd(self.startJd)

	def getEndEpoch(self):
		return self.getEpochFromJd(self.endJd)

	def showInCal(self):
		return self.showInDCal or self.showInWCal or self.showInMCal

	def getSortBys(self):
		sortBys = list(self.sortBys)
		if self.enable:
			sortBys.append(("time_last", _("Last Occurrence Time"), False))
			sortBys.append(("time_first", _("First Occurrence Time"), False))
			return "time_last", sortBys
		else:
			return self.sortByDefault, sortBys

	def getSortByValue(self, event, attr):
		if attr in ("time_last", "time_first"):
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
				else:
					log.info(f"no time_last returned for event {event.id}")
					return smallest
		return getattr(event, attr, smallest)

	def sort(self, attr="summary", reverse=False):
		isTypeDep = True
		for name, desc, dep in self.getSortBys()[1]:
			if name == attr:
				isTypeDep = dep
				break
		if isTypeDep:
			def event_key(event):
				return (event.name, self.getSortByValue(event, attr))
		else:
			def event_key(event):
				return self.getSortByValue(event, attr)

		self.idList.sort(
			key=lambda eid: event_key(self.getEventNoCache(eid)),
			reverse=reverse,
		)

	def __getitem__(self, key):
		# if isinstance(key, basestring):  # ruleName
		# 	return self.getRule(key)
		if isinstance(key, int):  # eventId
			return self.getEvent(key)
		else:
			raise TypeError(
				f"invalid key {key!r} given " +
				"to EventGroup.__getitem__"
			)

	def __setitem__(self, key, value):
		# if isinstance(key, basestring):  # ruleName
		# 	return self.setRule(key, value)
		if isinstance(key, int):  # eventId
			raise TypeError("can not assign event to group")  # FIXME
		else:
			raise TypeError(
				f"invalid key {key!r} given " +
				"to EventGroup.__setitem__"
			)

	def __delitem__(self, key):
		if isinstance(key, int):  # eventId
			self.remove(self.getEvent(key))
		else:
			raise TypeError(
				f"invalid key {key!r} given " +
				"to EventGroup.__delitem__"
			)

	def checkEventToAdd(self, event):
		return event.name in self.acceptsEventTypes

	def __repr__(self):
		return f"{self.__class__.__name__}(_id={self.id!r})"

	def __str__(self) -> str:
		return f"{self.__class__.__name__}(_id={self.id!r}, title='{self.title}')"

	def __init__(self, _id=None):
		EventContainer.__init__(self, title=self.desc)
		if _id is None:
			self.id = None
		else:
			self.setId(_id)
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
		self.eventCacheSize = 0
		self.eventTextSep = core.eventTextSep
		###
		self.eventCache = {}  # from eid to event object
		###
		year, month, day = getSysDate(self.calType)
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
		##
		self.initOccurrence()
		###
		self.setDefaults()
		###########
		self.clearRemoteAttrs()

	def setRandomColor(self):
		import random
		from scal3.color_utils import hslToRgb
		self.color = hslToRgb(random.uniform(0, 360), 1, 0.5)  # FIXME

	def clearRemoteAttrs(self):
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

	def setReadOnly(self, readOnly):
		self.__readOnly = readOnly

	def isReadOnly(self):
		return allReadOnly or self.__readOnly

	def save(self):
		if self.__readOnly:
			raise RuntimeError("event group is read-only right now")
		if self.id is None:
			self.setId()
		EventContainer.save(self)

	def getSyncDurationSec(self):
		"""
		return Sync Duration in seconds (int)
		"""
		value, unit = self.remoteSyncDuration
		return value * unit

	def afterSync(self, startEpoch=None):
		endEpoch = now()
		if startEpoch is None:
			startEpoch = endEpoch
		self.remoteSyncData[self.remoteIds] = (startEpoch, endEpoch)

	def getLastSync(self):
		"""
		return a tuple (startEpoch, endEpoch) or None
		"""
		if self.remoteIds:
			try:
				return self.remoteSyncData[self.remoteIds]
			except KeyError:
				pass

	def setDefaults(self):
		"""
			sets default values that depends on group type
			not common parameters, like those are set in __init__
		"""

	def __bool__(self):
		return self.enable  # FIXME

	def setId(self, _id=None):
		if _id is None or _id < 0:
			_id = lastIds.group + 1  # FIXME
			lastIds.group = _id
		elif _id > lastIds.group:
			lastIds.group = _id
		self.id = _id
		self.file = self.getFile(self.id)

	def setTitle(self, title):
		self.title = title

	def setColor(self, color):
		self.color = color

	def getData(self):
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

	def setData(self, data) -> None:
		if "showInCal" in data:  # for compatibility
			data["showInDCal"] = data["showInWCal"] = \
				data["showInMCal"] = data["showInCal"]
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
					if not isinstance(item[0], (tuple, list)):
						continue
					valueDict[tuple(item[0])] = item[1]
				setattr(self, attr, valueDict)
		if "id" in data:
			self.setId(data["id"])
		self.startJd = int(self.startJd)
		self.endJd = int(self.endJd)
		####
		# if "defaultEventType" in data:
		# 	self.defaultEventType = data["defaultEventType"]
		# 	if not self.defaultEventType in classes.event.names:
		# 		raise ValueError(f"Invalid defaultEventType: {self.defaultEventType!r}")

	# event objects should be accessed from outside
	# only via one of the following 3 methods

	def removeFromCache(self, eid):
		if eid in self.eventCache:
			del self.eventCache[eid]

	def getEvent(self, eid):
		if eid not in self.idList:
			raise ValueError(f"{self} does not contain {eid!r}")
		if eid in self.eventCache:
			return self.eventCache[eid]
		event = EventContainer.getEvent(self, eid)
		event.parent = self
		event.rulesHash = event.getRulesHash()
		if self.enable and len(self.eventCache) < self.eventCacheSize:
			self.eventCache[eid] = event
		return event

	def getEventNoCache(self, eid):
		"""
			no caching. and no checking if group contains eid
			used only for sorting events
		"""
		event = EventContainer._getEvent(self, eid)
		event.parent = self
		event.rulesHash = event.getRulesHash()
		return event

	def create(self, eventType):
		# if not eventType in self.acceptsEventTypes: # FIXME
		# 	raise ValueError(
		# 		f"Event type '{eventType}' not supported "
		# 		f"in group type "{self.name}""
		# 	)
		event = classes.event.byName[eventType](parent=self)  # FIXME
		event.fs = self.fs
		return event

	def copyEventWithType(self, event, eventType):  # FIXME
		newEvent = self.create(eventType)
		###
		newEvent.changeCalType(event.calType)
		newEvent.copyFrom(event)
		###
		newEvent.setId(event.id)
		event.invalidate()
		###
		return newEvent
	###############################################

	def remove(self, event):  # call when moving to trash
		index = EventContainer.remove(self, event)
		if event.id in self.eventCache:
			del self.eventCache[event.id]
		if event.remoteIds:
			self.deletedRemoteEvents[event.id] = (now(),) + event.remoteIds
		# try:
		# 	del self.eventIdByRemoteIds[event.remoteIds]
		# except:
		# 	pass
		self.occurCount -= self.occur.delete(event.id)
		return index

	def removeAll(self):  # clearEvents or excludeAll or removeAll FIXME
		for event in self.eventCache.values():
			event.parent = None  # needed? FIXME
		###
		self.idList = []
		self.eventCache = {}
		self.occur.clear()
		self.occurCount = 0

	def postAdd(self, event):
		EventContainer.postAdd(self, event)
		if len(self.eventCache) < self.eventCacheSize:
			self.eventCache[event.id] = event
		# if event.remoteIds:
		# 	self.eventIdByRemoteIds[event.remoteIds] = event.id
		# need to update self.occur?
		# its done in event.afterModify() right?
		# not when moving event from another group
		if self.enable:
			self.updateOccurrenceEvent(event)

	def updateCache(self, event):
		if event.id in self.eventCache:
			self.eventCache[event.id] = event
		event.afterModify()

	def copy(self):
		newGroup = SObj.copy(self)
		newGroup.removeAll()
		return newGroup

	def copyFrom(self, other):
		EventContainer.copyFrom(self, other)
		self.enable = other.enable

	def copyAs(self, newGroupType):
		newGroup = classes.group.byName[newGroupType]()
		newGroup.fs = self.fs
		newGroup.copyFrom(self)
		newGroup.removeAll()
		return newGroup

	def deepCopy(self):
		newGroup = self.copy()
		for event in self:
			newEvent = event.copy()
			newEvent.save()
			newGroup.append(newEvent)
		return newGroup

	def deepConvertTo(self, newGroupType):
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

	def calcOccurrenceAll(self):
		startJd = self.startJd
		endJd = self.endJd
		for event in self:
			occur = event.calcOccurrence(startJd, endJd)
			if occur:
				yield event, occur

	def afterModify(self):  # FIXME
		EventContainer.afterModify(self)
		self.initOccurrence()
		####
		if self.enable:
			self.updateOccurrence()
		else:
			self.eventCache = {}

	def updateOccurrenceEvent(self, event):
		log.debug(
			f"updateOccurrenceEvent: id={self.id}" +
			f" title={self.title} eid={event.id}"
		)
		eid = event.id
		self.occurCount -= self.occur.delete(eid)
		for t0, t1 in event.calcOccurrenceAll().getTimeRangeList():
			self.addOccur(t0, t1, eid)

	def initOccurrence(self):
		from scal3.event_search_tree import EventSearchTree
		# from scal3.time_line_tree import TimeLineTree
		# self.occur = TimeLineTree(offset=self.getEpochFromJd(self.endJd))
		self.occur = EventSearchTree()
		# self.occurLoaded = False
		self.occurCount = 0

	def clear(self):
		self.occur.clear()
		self.occurCount = 0

	def addOccur(self, t0, t1, eid):
		self.occur.add(t0, t1, eid)
		self.occurCount += 1

	def updateOccurrenceLog(self, stm0):
		log.debug(
			f"updateOccurrence, id={self.id}, title='{self.title}', " +
			f"count={self.occurCount}, time={now() - stm0}"
		)

	def updateOccurrence(self):
		stm0 = now()
		self.clear()
		for event, occur in self.calcOccurrenceAll():
			for t0, t1 in occur.getTimeRangeList():
				self.addOccur(t0, t1, event.id)
		# self.occurLoaded = True
		log.debug(f"time = {(now() - stm0) * 1000} ms")
		# log.debug(
		# 	f"updateOccurrence, id={self.id}, title={self.title}, " +
		# 	f"count={self.occurCount}, time={now()-stm0}"
		# )
		# log.debug(f"{self.id} {1000*(now()-stm0)} {self.occur.calcAvgDepth():.1f}")

	def _exportToIcsFpEvent(self, fp, event, currentTimeStamp):
		# log.debug("exportToIcsFp", event.id)

		commonText = "\n".join([
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
			"UID:" + getEventUID(event),
		]) + "\n"

		icsData = event.getIcsData()
		if icsData is not None:
			vevent = commonText
			for key, value in icsData:
				vevent += key + ":" + value + "\n"
			vevent += "END:VEVENT\n"
			fp.write(vevent)
			return

		occur = event.calcOccurrenceAll()
		if not occur:
			return
		if isinstance(occur, JdOccurSet):
			# for sectionStartJd in occur.getDaysJdList():
			# 	sectionEndJd = sectionStartJd + 1
			for sectionStartJd, sectionEndJd in occur.calcJdRanges():
				vevent = commonText
				vevent += "\n".join([
					"DTSTART;VALUE=DATE:" + ics.getIcsDateByJd(sectionStartJd),
					"DTEND;VALUE=DATE:" + ics.getIcsDateByJd(sectionEndJd),
					"TRANSP:TRANSPARENT",
					# http://www.kanzaki.com/docs/ical/transp.html
					"END:VEVENT\n"
				])
				fp.write(vevent)
		elif isinstance(occur, (IntervalOccurSet, TimeListOccurSet)):
			for startEpoch, endEpoch in occur.getTimeRangeList():
				vevent = commonText
				parts = [
					"DTSTART:" + ics.getIcsTimeByEpoch(startEpoch),
				]
				if endEpoch is not None and endEpoch - startEpoch > 1:
					endEpoch = int(endEpoch)  # why float? FIXME
					parts.append("DTEND:" + ics.getIcsTimeByEpoch(endEpoch))
				parts += [
					"TRANSP:OPAQUE",  # FIXME
					# http://www.kanzaki.com/docs/ical/transp.html
					"END:VEVENT\n",
				]
				vevent += "\n".join(parts)
				fp.write(vevent)
		else:
			raise RuntimeError

	def exportToIcsFp(self, fp):
		currentTimeStamp = ics.getIcsTimeByEpoch(now())
		for event in self:
			self._exportToIcsFpEvent(fp, event, currentTimeStamp)

	def exportData(self):
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
			try:
				del eventData["remoteIds"]  # FIXME
			except KeyError:
				pass
			if not eventData["notifiers"]:
				del eventData["notifiers"]
				del eventData["notifyBefore"]
		del data["idList"]
		return data

	def loadEventIdByUuid(self):
		existingIds = set(self.idByUuid.values())
		for eid in self.idList:
			if eid in existingIds:
				continue
			event = self.getEvent(eid)
			if event.uuid is None:
				continue
			self.idByUuid[event.uuid] = event.id
		return self.idByUuid

	def appendByData(self, eventData):
		event = self.create(eventData["type"])
		event.setData(eventData)
		event.save()
		self.append(event)
		return event

	def importData(
		self,
		data, importMode=IMPORT_MODE_APPEND,
	) -> EventGroupsImportResult:
		"""
			the caller must call group.save() after this
		"""
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
				print("appending event uuid =", uuid)
				event = self.appendByData(eventData)
				res.newEventIds.add((gid, event.id))
				continue

			if importMode != IMPORT_MODE_OVERRIDE_MODIFIED:
				# assumed IMPORT_MODE_SKIP_MODIFIED
				print("skipping to override existing uuid=%r, eid=%r" % (uuid, eid))
				continue

			event = self.getEvent(eid)
			event.setData(eventData, force=True)
			event.save()
			res.modifiedEventIds.add((gid, event.id))
			print("overriden existing uuid=%r, eid=%r" % (uuid, eid))

		return res

	def search(self, conds):
		conds = dict(conds)  # take a copy, we may modify it
		if "time_from" in conds or "time_to" in conds:
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
			idList = sorted({
				eid
				for _, _, eid, _ in self.occur.search(time_from, time_to)
			})
		else:
			idList = self.idList
		#####
		data = []
		for eid in idList:
			try:
				event = self[eid]
				# FIXME: is this check really useful?
			except KeyError:
				continue
			for key, value in conds.items():
				func = self.simpleFilters[key]
				if not func(event, value):
					break
			else:
				data.append({
					"id": eid,
					"icon": event.getIcon(),
					"summary": event.summary,
					"description": event.getShownDescription(),
				})
		#####
		return data

	def createPatchList(self, sinceEpoch):
		patchList = []

		for event in self:
			# if not event.remoteIds:  # FIXME
			eventHist = event.loadHistory()
			if not eventHist:
				log.info(f"eventHist = {eventHist!r}")
				continue
			# assert event.modified == eventHist[0][0]
			if eventHist[0][0] > sinceEpoch:
				creationEpoch = eventHist[-1][0]
				if creationEpoch > sinceEpoch:
					patchList.append({
						"eventId": event.id,
						"eventType": event.name,
						"action": "add",
						"newEventData": event.getServerData(),
					})
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

	def getSortByValue(self, event, attr):
		if event.name in self.acceptsEventTypes:
			if attr == "start":
				return event.getStartEpoch()
			elif attr == "end":
				return event.getEndEpoch()
		return EventGroup.getSortByValue(self, event, attr)

	def __init__(self, _id=None):
		EventGroup.__init__(self, _id)
		self.defaultDuration = (0, 1)  # (value, unit)
		# if defaultDuration[0] is set to zero, the checkbox for task"s end,
		# will be unchecked for new tasks

	def copyFrom(self, other):
		EventGroup.copyFrom(self, other)
		if other.name == self.name:
			self.defaultDuration = other.defaultDuration[:]

	def getData(self):
		data = EventGroup.getData(self)
		data["defaultDuration"] = durationEncode(*self.defaultDuration)
		return data

	def setData(self, data) -> None:
		EventGroup.setData(self, data)
		if "defaultDuration" in data:
			self.defaultDuration = durationDecode(data["defaultDuration"])


@classes.group.register
class NoteBook(EventGroup):
	name = "noteBook"
	desc = _("Note Book")
	acceptsEventTypes = (
		"dailyNote",
	)
	canConvertTo = (
		"yearly",
		"taskList",
	)
	# actions = EventGroup.actions + []
	sortBys = EventGroup.sortBys + (
		("date", _("Date"), True),
	)
	sortByDefault = "date"

	def getSortByValue(self, event, attr):
		if event.name in self.acceptsEventTypes:
			if attr == "date":
				return event.getJd()
		return EventGroup.getSortByValue(self, event, attr)


@classes.group.register
class YearlyGroup(EventGroup):
	name = "yearly"
	desc = _("Yearly Events Group")
	acceptsEventTypes = (
		"yearly",
	)
	canConvertTo = (
		"noteBook",
	)
	params = EventGroup.params + (
		"showDate",
	)

	def __init__(self, _id=None):
		EventGroup.__init__(self, _id)
		self.showDate = True


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
	params = EventGroup.params + (
		"courses",
	)
	paramsOrder = EventGroup.paramsOrder + (
		"classTimeBounds",
		"classesEndDate",
		"courses",
	)
	noCourseError = _(
		"Edit University Term and define some Courses " +
		"before you add a Class/Exam"
	)

	def getSortByValue(self, event, attr):
		if event.name in self.acceptsEventTypes:
			if attr == "course":
				return event.courseId
			elif attr == "time":
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
				elif event.name == "universityExam":
					date, ok = event["date"]
					if not ok:
						raise RuntimeError("no date rule")
					dayTimeRange, ok = event["dayTimeRange"]
					if not ok:
						raise RuntimeError("no dayTimeRange rule")
					return date.getJd(), dayTimeRange.getHourRange()
		return EventGroup.getSortByValue(self, event, attr)

	def __init__(self, _id=None):
		EventGroup.__init__(self, _id)
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

	def getClassBoundsFormatted(self):
		count = len(self.classTimeBounds)
		if count < 2:
			return
		titles = []
		tmfactors = []
		firstTm = timeToFloatHour(*self.classTimeBounds[0])
		lastTm = timeToFloatHour(*self.classTimeBounds[-1])
		deltaTm = lastTm - firstTm
		for i in range(count - 1):
			tm0, tm1 = self.classTimeBounds[i:i + 2]
			titles.append(
				textNumEncode(simpleTimeEncode(tm0)) +
				" " + _("to") + " " +
				textNumEncode(simpleTimeEncode(tm1))
			)
		for tm1 in self.classTimeBounds:
			tmfactors.append(
				(timeToFloatHour(*tm1) - firstTm) / deltaTm
			)
		return (titles, tmfactors)

	def getWeeklyScheduleData(self, currentWeekOnly=False):
		boundsCount = len(self.classTimeBounds)
		boundsHour = [
			h + m / 60.0
			for h, m in self.classTimeBounds
		]
		data = [
			[
				[]
				for i in range(boundsCount - 1)
			]
			for weekDay in range(7)
		]
		# data[weekDay][intervalIndex] = {
		# 	"name": "Course Name",
		# 	"weekNumMode": "odd",
		# }
		###
		if currentWeekOnly:
			currentJd = core.getCurrentJd()
			if (
				getAbsWeekNumberFromJd(currentJd) -
				getAbsWeekNumberFromJd(self.startJd)
			) % 2 == 1:
				currentWeekNumMode = "odd"
			else:
				currentWeekNumMode = "even"
			# log.debug(f"currentWeekNumMode = {currentWeekNumMode}")
		else:
			currentWeekNumMode = ""
		###
		for event in self:
			if event.name != "universityClass":
				continue
			weekNumModeRule, ok = event["weekNumMode"]
			if not ok:
				raise RuntimeError("no weekNumMode rule")
			weekNumMode = weekNumModeRule.getData()
			if currentWeekNumMode:
				if weekNumMode not in ("any", currentWeekNumMode):
					continue
				weekNumMode = ""
			else:
				if weekNumMode == "any":
					weekNumMode = ""
			###
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
			###
			classData = {
				"name": self.getCourseNameById(event.courseId),
				"weekNumMode": weekNumMode,
			}
			for i in range(startIndex, endIndex):
				data[weekDay][i].append(classData)

		return data

	def setCourses(self, courses):
		self.courses = courses
		# self.lastCourseId = max([1]+[course[0] for course in self.courses])
		# log.debug(f"setCourses: lastCourseId={self.lastCourseId}")

	# def getCourseNamesDictById(self):
	# 	return dict([c[:2] for c in self.courses])

	def getCourseNameById(self, courseId):
		for course in self.courses:
			if course[0] == courseId:
				return course[1]
		return _("Deleted Course")

	def setDefaults(self):
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

	# def getNewCourseID(self):
	# 	self.lastCourseId += 1
	# 	log.info(f"getNewCourseID: lastCourseId={self.lastCourseId}")
	# 	return self.lastCourseId

	def copyFrom(self, other):
		EventGroup.copyFrom(self, other)
		if other.name == self.name:
			self.classesEndDate = other.classesEndDate[:]
			self.classTimeBounds = other.classTimeBounds[:]

	def getData(self):
		data = EventGroup.getData(self)
		data.update({
			"classTimeBounds": [hmEncode(hm) for hm in self.classTimeBounds],
			"classesEndDate": dateEncode(self.classesEndDate),
		})
		return data

	def setData(self, data) -> None:
		EventGroup.setData(self, data)
		# self.setCourses(data["courses"])
		if "classesEndDate" in data:
			self.classesEndDate = dateDecode(data["classesEndDate"])
		if "classTimeBounds" in data:
			self.classTimeBounds = sorted(
				hmDecode(hm)
				for hm in data["classTimeBounds"]
			)

	def afterModify(self):
		EventGroup.afterModify(self)
		for event in self:
			try:
				event.updateSummary()
			except AttributeError:
				pass
			else:
				event.save()


@classes.group.register
class LifeTimeGroup(EventGroup):
	name = "lifeTime"
	nameAlias = "lifetime"
	desc = _("Life Time Events Group")
	acceptsEventTypes = (
		"lifeTime",
	)
	sortBys = EventGroup.sortBys + (
		("start", _("Start"), True),
	)
	params = EventGroup.params + (
		"showSeparatedYmdInputs",
	)

	def getSortByValue(self, event, attr):
		if event.name in self.acceptsEventTypes:
			if attr == "start":
				return event.getStartJd()
			elif attr == "end":
				return event.getEndJd()
		return EventGroup.getSortByValue(self, event, attr)

	def __init__(self, _id=None):
		self.showSeparatedYmdInputs = False
		EventGroup.__init__(self, _id)

	def setData(self, data):
		if "showSeperatedYmdInputs" in data:
			# misspell in < 3.1.x
			data["showSeparatedYmdInputs"] = data["showSeperatedYmdInputs"]
		EventGroup.setData(self, data)

	def setDefaults(self):
		# only show in time line
		self.showInDCal = False
		self.showInWCal = False
		self.showInMCal = False
		self.showInStatusIcon = False


@classes.group.register
class LargeScaleGroup(EventGroup):
	name = "largeScale"
	desc = _("Large Scale Events Group")
	acceptsEventTypes = (
		"largeScale",
	)
	sortBys = EventGroup.sortBys + (
		("start", _("Start"), True),
		("end", _("End"), True),
	)
	sortByDefault = "start"

	def getSortByValue(self, event, attr):
		if event.name in self.acceptsEventTypes:
			if attr == "start":
				return event.start * event.scale
			elif attr == "end":
				return event.getEnd() * event.scale
		return EventGroup.getSortByValue(self, event, attr)

	def __init__(self, _id=None):
		self.scale = 1  # 1, 1000, 1000**2, 1000**3
		EventGroup.__init__(self, _id)

	def setDefaults(self):
		self.startJd = 0
		self.endJd = self.startJd + self.scale * 9999
		# only show in time line
		self.showInDCal = False
		self.showInWCal = False
		self.showInMCal = False
		self.showInStatusIcon = False

	def copyFrom(self, other):
		EventGroup.copyFrom(self, other)
		if other.name == self.name:
			self.scale = other.scale

	def getData(self):
		data = EventGroup.getData(self)
		data["scale"] = self.scale
		return data

	def setData(self, data) -> None:
		EventGroup.setData(self, data)
		try:
			self.scale = data["scale"]
		except KeyError:
			pass

	def getStartValue(self):
		return jd_to(self.startJd, self.calType)[0] // self.scale

	def getEndValue(self):
		return jd_to(self.endJd, self.calType)[0] // self.scale

	def setStartValue(self, start):
		self.startJd = int(to_jd(
			start * self.scale,
			1,
			1,
			self.calType,
		))

	def setEndValue(self, end):
		self.endJd = int(to_jd(
			end * self.scale,
			1,
			1,
			self.calType,
		))


###########################################################################
###########################################################################

class VcsEpochBaseEvent(Event):
	readOnly = True
	params = Event.params + (
		"epoch",
	)

	@classmethod
	def load(cls, fs: FileSystem, *args):  # FIXME
		pass

	def __bool__(self):
		return True

	def save(self):
		pass

	def afterModify(self):
		pass

	def getInfo(self) -> str:
		return self.getText()  # FIXME

	def calcOccurrence(self, startJd: int, endJd: int) -> OccurSet:
		epoch = self.epoch
		if epoch is not None:
			if self.getEpochFromJd(startJd) <= epoch < self.getEpochFromJd(endJd):
				if not self.parent.showSeconds:
					log.info("-------- showSeconds = False")
					epoch -= (epoch % 60)
				return TimeListOccurSet(epoch)
		return TimeListOccurSet()


# @classes.event.register  # FIXME
class VcsCommitEvent(VcsEpochBaseEvent):
	name = "vcs"
	desc = _("VCS Commit")
	params = VcsEpochBaseEvent.params + (
		"author",
		"shortHash",
	)

	def __init__(self, parent, _id):
		Event.__init__(self, parent=parent)
		self.id = _id  # commit full hash
		###
		self.epoch = None
		self.author = ""
		self.shortHash = ""

	def __repr__(self):
		return f"{self.parent!r}.getEvent({self.id!r})"


class VcsTagEvent(VcsEpochBaseEvent):
	name = "vcsTag"
	desc = _("VCS Tag")
	params = VcsEpochBaseEvent.params + (
	)

	def __init__(self, parent, _id):
		Event.__init__(self, parent=parent)
		self.id = _id  # tag name
		self.epoch = None
		self.author = ""


class VcsBaseEventGroup(EventGroup):
	acceptsEventTypes = ()
	myParams = (
		"vcsType",
		"vcsDir",
		"vcsBranch",
	)

	def __init__(self, _id=None):
		self.vcsType = "git"
		self.vcsDir = ""
		self.vcsBranch = "main"
		EventGroup.__init__(self, _id)

	def __str__(self) -> str:
		return (
			f"{self.__class__.__name__}(_id={self.id!r}, " +
			f"title='{self.title}', vcsType={self.vcsType!r}, " +
			f"vcsDir={self.vcsDir!r})"
		)

	def setDefaults(self):
		self.eventTextSep = "\n"
		self.showInTimeLine = False

	def getRulesHash(self):
		return hash(str((
			self.name,
			self.vcsType,
			self.vcsDir,
			self.vcsBranch,
		)))  # FIXME

	def __getitem__(self, key):
		if key in classes.rule.names:
			return EventGroup.__getitem__(self, key)
		else:  # len(commit_id)==40 for git
			return self.getEvent(key)

	def getVcsModule(self):
		name = toStr(self.vcsType)
		# if not isinstance(name, str):
		# 	raise TypeError(f"getVcsModule({name!r}): bad type {type(name)}")
		try:
			mod = __import__("scal3.vcs_modules", fromlist=[name])
		except ImportError:
			log.exception("")
			return
		return getattr(mod, name)

	def updateVcsModuleObj(self):
		mod = self.getVcsModule()
		if mod is None:
			log.info(f"VCS module {self.vcsType!r} not found")
			return
		mod.clearObj(self)
		if self.enable and self.vcsDir:
			try:
				mod.prepareObj(self)
			except Exception:
				log.exception("")

	def afterModify(self):
		self.updateVcsModuleObj()
		EventGroup.afterModify(self)

	def setData(self, data) -> None:
		EventGroup.setData(self, data)
		self.updateVcsModuleObj()


class VcsEpochBaseEventGroup(VcsBaseEventGroup):
	myParams = VcsBaseEventGroup.myParams + (
		"showSeconds",
	)
	canConvertTo = VcsBaseEventGroup.canConvertTo + (
		"taskList",
	)

	def __init__(self, _id=None):
		self.showSeconds = True
		self.vcsIds = []
		VcsBaseEventGroup.__init__(self, _id)

	def clear(self):
		EventGroup.clear(self)
		self.vcsIds = []

	def addOccur(self, t0, t1, eid):
		EventGroup.addOccur(self, t0, t1, eid)
		self.vcsIds.append(eid)

	def getRulesHash(self):
		return hash(str((
			self.name,
			self.vcsType,
			self.vcsDir,
			self.vcsBranch,
			self.showSeconds,
		)))

	def deepConvertTo(self, newGroupType):
		newGroup = self.copyAs(newGroupType)
		if newGroupType == "taskList":
			newEventType = "task"
			newGroup.enable = False  # to prevent per-event node update
			for vcsId in self.vcsIds:
				event = self.getEvent(vcsId)
				newEvent = newGroup.create(newEventType)
				newEvent.changeCalType(event.calType)  # FIXME needed?
				newEvent.copyFrom(event, True)
				newEvent.setStartEpoch(event.epoch)
				newEvent.setEnd("duration", 0, 1)
				newEvent.save()
				newGroup.append(newEvent)
			newGroup.enable = self.enable
		return newGroup


@classes.group.register
class VcsCommitEventGroup(VcsEpochBaseEventGroup):
	name = "vcs"
	desc = _("VCS Repository (Commits)")
	myParams = VcsEpochBaseEventGroup.myParams + (
		"showAuthor",
		"showShortHash",
		"showStat",
	)
	params = EventGroup.params + myParams
	paramsOrder = EventGroup.paramsOrder + myParams

	def __init__(self, _id=None):
		VcsEpochBaseEventGroup.__init__(self, _id)
		self.showAuthor = True
		self.showShortHash = True
		self.showStat = True

	def updateOccurrence(self):
		stm0 = now()
		self.clear()
		if not self.vcsDir:
			return
		mod = self.getVcsModule()
		if mod is None:
			log.info(f"VCS module {self.vcsType!r} not found")
			return
		try:
			commitsData = mod.getCommitList(
				self,
				startJd=self.startJd,
				endJd=self.endJd,
				branch=self.vcsBranch,
			)
		except Exception:
			log.error(
				f"Error while fetching commit list of {self.vcsType} " +
				f"repository in {self.vcsDir}"
			)
			log.exception("")
			return
		for epoch, commit_id in commitsData:
			if not self.showSeconds:
				epoch -= (epoch % 60)
			self.addOccur(epoch, epoch, commit_id)
		###
		self.updateOccurrenceLog(stm0)

	def updateEventDesc(self, event):
		mod = self.getVcsModule()
		if mod is None:
			log.info(f"VCS module {self.vcsType!r} not found")
			return
		lines = []
		if event.description:
			lines.append(event.description)
		if self.showStat:
			statLine = mod.getCommitShortStatLine(self, event.id)
			if statLine:
				lines.append(statLine)  # TODO: translation
		if self.showAuthor and event.author:
			lines.append(_("Author") + ": " + event.author)
		if self.showShortHash and event.shortHash:
			lines.append(_("Hash") + ": " + event.shortHash)
		event.description = "\n".join(lines)

	# TODO: cache commit data
	def getEvent(self, commit_id):
		mod = self.getVcsModule()
		if mod is None:
			log.info(f"VCS module {self.vcsType!r} not found")
			return
		data = mod.getCommitInfo(self, commit_id)
		if not data:
			raise ValueError(f"No commit with id={commit_id!r}")
		data["summary"] = self.title + ": " + data["summary"]
		data["icon"] = self.icon
		event = VcsCommitEvent(self, commit_id)
		event.setData(data)
		self.updateEventDesc(event)
		return event


@classes.group.register
class VcsTagEventGroup(VcsEpochBaseEventGroup):
	name = "vcsTag"
	desc = _("VCS Repository (Tags)")
	myParams = VcsEpochBaseEventGroup.myParams + (
		"showStat",
	)
	params = EventGroup.params + myParams
	paramsOrder = EventGroup.paramsOrder + myParams

	def __init__(self, _id=None):
		VcsEpochBaseEventGroup.__init__(self, _id)
		self.showStat = True

	def updateOccurrence(self):
		stm0 = now()
		self.clear()
		if not self.vcsDir:
			return
		mod = self.getVcsModule()
		if mod is None:
			log.info(f"VCS module {self.vcsType!r} not found")
			return
		try:
			tagsData = mod.getTagList(self, self.startJd, self.endJd)
			# TOO SLOW, FIXME
		except Exception:
			log.error(
				f"Error while fetching tag list of {self.vcsType} " +
				f"repository in {self.vcsDir}"
			)
			log.exception("")
			return
		# self.updateOccurrenceLog(stm0)
		for epoch, tag in tagsData:
			if not self.showSeconds:
				epoch -= (epoch % 60)
			self.addOccur(epoch, epoch, tag)
		###
		self.updateOccurrenceLog(stm0)

	def updateEventDesc(self, event):
		mod = self.getVcsModule()
		if mod is None:
			log.info(f"VCS module {self.vcsType!r} not found")
			return
		tag = event.id
		lines = []
		if self.showStat:
			tagIndex = self.vcsIds.index(tag)
			if tagIndex > 0:
				prevTag = self.vcsIds[tagIndex - 1]
			else:
				prevTag = None
			statLine = mod.getTagShortStatLine(self, prevTag, tag)
			if statLine:
				lines.append(statLine)  # TODO: translation
		event.description = "\n".join(lines)

	# TODO: cache commit data
	def getEvent(self, tag):
		tag = toStr(tag)
		if tag not in self.vcsIds:
			raise ValueError(f"No tag {tag!r}")
		data = {}
		data["summary"] = self.title + " " + tag
		data["icon"] = self.icon
		event = VcsTagEvent(self, tag)
		event.setData(data)
		self.updateEventDesc(event)
		return event


class VcsDailyStatEvent(Event):
	name = "vcsDailyStat"
	desc = _("VCS Daily Stat")
	readOnly = True
	isAllDay = True
	params = Event.params + (
		"jd",
	)

	@classmethod
	def load(cls, fs: FileSystem, *args):  # FIXME
		pass

	def __bool__(self):
		return True

	def __init__(self, parent, jd):
		Event.__init__(self, parent=parent)
		self.id = jd  # ID is Julian Day

	def save(self):
		pass

	def afterModify(self):
		pass

	def getInfo(self) -> str:
		return self.getText()  # FIXME

	def calcOccurrence(self, startJd: int, endJd: int) -> OccurSet:
		jd = self.jd
		if jd is not None:
			if startJd <= jd < endJd:
				JdOccurSet({jd})
		return JdOccurSet()


@classes.group.register
class VcsDailyStatEventGroup(VcsBaseEventGroup):
	name = "vcsDailyStat"
	desc = _("VCS Repository (Daily Stat)")
	myParams = VcsBaseEventGroup.myParams + (
	)
	params = EventGroup.params + myParams
	paramsOrder = EventGroup.paramsOrder + myParams

	def __init__(self, _id=None):
		VcsBaseEventGroup.__init__(self, _id)
		self.statByJd = {}

	def clear(self):
		VcsBaseEventGroup.clear(self)
		self.statByJd = {}  # a dict of (commintsCount, lastCommitId)s

	def updateOccurrence(self):
		stm0 = now()
		self.clear()
		if not self.vcsDir:
			return
		mod = self.getVcsModule()
		if mod is None:
			log.info(f"VCS module {self.vcsType!r} not found")
			return
		####
		try:
			utc = natz.gettz("UTC")
			self.vcsMinJd = getJdFromEpoch(mod.getFirstCommitEpoch(self), tz=utc)
			self.vcsMaxJd = getJdFromEpoch(mod.getLastCommitEpoch(self), tz=utc) + 1
		except Exception:
			log.exception("")
			return
		###
		startJd = max(self.startJd, self.vcsMinJd)
		endJd = min(self.endJd, self.vcsMaxJd)
		###
		commitsByJd = {}  # type: Dict[int, List[str]]
		for epoch, commitId in mod.getCommitList(
			self,
			startJd=startJd,
			endJd=endJd + 1,
			branch=self.vcsBranch,
		):
			jd = getJdFromEpoch(epoch)
			if jd in commitsByJd:
				commitsByJd[jd].append(commitId)
			else:
				commitsByJd[jd] = [commitId]
		for jd in range(startJd, endJd + 1):
			if jd not in commitsByJd:
				continue
			epoch = getEpochFromJd(jd)
			commitIds = commitsByJd[jd]
			newCommitId = commitIds[-1]
			oldCommitId = mod.getLatestParentBefore(self, newCommitId, epoch)
			if not oldCommitId:
				log.info(f"oldCommitId is empty, jd={jd}, newCommitId={newCommitId}")
				continue
			stat = mod.getShortStat(self, oldCommitId, newCommitId)
			self.statByJd[jd] = (len(commitIds), stat)
			self.addOccur(
				getEpochFromJd(jd),
				getEpochFromJd(jd + 1),
				jd,
			)
		###
		self.updateOccurrenceLog(stm0)

	def getEvent(self, jd):
		# cache commit data FIXME
		from scal3.vcs_modules import encodeShortStat
		try:
			commitsCount, stat = self.statByJd[jd]
		except KeyError:
			raise ValueError(f"No commit for jd {jd}")
		mod = self.getVcsModule()
		if mod is None:
			log.info(f"VCS module {self.vcsType!r} not found")
			return
		event = VcsDailyStatEvent(self, jd)
		###
		event.icon = self.icon
		##
		statLine = encodeShortStat(*stat)
		event.summary = (
			self.title +
			": " +
			_("{commitsCount} commits").format(commitsCount=commitsCount)
		)
		event.summary += ", " + statLine
		# event.description = statLine
		###
		return event


###########################################################################
###########################################################################

class JsonObjectsHolder(JsonEventObj):
	# keeps all objects in memory
	# Only use to keep groups and accounts, but not events
	skipLoadNoFile = True

	def __init__(self, _id=None):
		self.fs = None
		self.clear()

	def clear(self):
		self.byId = {}
		self.idList = []

	def __iter__(self):
		for _id in self.idList:
			yield self.byId[_id]

	def __len__(self):
		return len(self.idList)

	def __bool__(self):
		return bool(self.idList)

	def index(self, _id):
		return self.idList.index(_id)
		# or get object instead of obj_id? FIXME

	def __getitem__(self, _id):
		return self.byId.__getitem__(_id)

	def byIndex(self, index):
		return self.byId[self.idList[index]]

	def __setitem__(self, _id, group):
		return self.byId.__setitem__(_id, group)

	def insert(self, index, obj):
		if obj.id in self.idList:
			raise ValueError(f"{self} already contains id={obj.id}, obj={obj}")
		self.byId[obj.id] = obj
		self.idList.insert(index, obj.id)

	def append(self, obj):
		if obj.id in self.idList:
			raise ValueError(f"{self} already contains id={obj.id}, obj={obj}")
		self.byId[obj.id] = obj
		self.idList.append(obj.id)

	def delete(self, obj):
		if obj.id not in self.idList:
			raise ValueError(f"{self} does not contains id={obj.id}, obj={obj}")
		try:
			self.fs.removeFile(obj.file)
		except Exception:
			# FileNotFoundError, PermissionError, etc
			log.exception("")
		try:
			del self.byId[obj.id]
		except KeyError:
			log.exception("")
		try:
			self.idList.remove(obj.id)
		except ValueError:
			log.exception("")
		if obj.id in self.idByUuid:
			del self.idByUuid[obj.id]

	def pop(self, index):
		return self.byId.pop(self.idList.pop(index))

	def moveUp(self, index):
		return self.idList.insert(index - 1, self.idList.pop(index))

	def moveDown(self, index):
		return self.idList.insert(index + 1, self.idList.pop(index))

	def setData(self, data) -> None:
		self.clear()
		for sid in data:
			if not isinstance(sid, int) or sid == 0:
				raise RuntimeError(f"unexpected sid={sid}, self={self}")
			_id = sid
			_id = abs(sid)
			try:
				cls = getattr(classes, self.childName).main
				obj = cls.load(self.fs, _id)
			except Exception:
				log.error(f"error loading {self.childName}")
				log.exception("")
				continue
			obj.parent = self
			obj.enable = (sid > 0)
			self.idList.append(_id)
			self.byId[obj.id] = obj

	def getData(self):
		return [
			_id if self.byId[_id] else -_id
			for _id in self.idList
		]


class EventGroupsHolder(JsonObjectsHolder):
	file = join(confDir, "event", "group_list.json")
	childName = "group"

	def __init__(self, _id=None):
		JsonObjectsHolder.__init__(self)
		self.id = None
		self.parent = None
		self.idByUuid = {}

	def create(self, groupName: str) -> EventGroup:
		group = classes.group.byName[groupName]()
		group.fs = self.fs
		return group

	def delete(self, obj):
		assert not obj.idList  # FIXME
		obj.parent = None
		JsonObjectsHolder.delete(self, obj)

	def setData(self, data) -> None:
		self.clear()
		if data:
			JsonObjectsHolder.setData(self, data)
			for group in self:
				if group.uuid is None:
					group.save()
					log.info(f"saved group {group.id} with uuid = {group.uuid}")
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
				self.idByUuid[obj.uuid] = obj.id
				self.append(obj)
			self.save()

	def getEnableIds(self):
		ids = []
		for group in self:
			if group.enable:
				ids.append(group.id)
		return ids

	def moveToTrash(self, group, trash, addToFirst=True):
		if core.eventTrashLastTop:
			trash.idList = group.idList + trash.idList
		else:
			trash.idList += group.idList
		group.idList = []
		self.delete(group)
		self.save()
		trash.save()

	def convertGroupTo(self, group, newGroupType):
		groupIndex = self.index(group.id)
		newGroup = group.deepConvertTo(newGroupType)
		newGroup.setId(group.id)
		newGroup.afterModify()
		newGroup.save()
		self.byId[newGroup.id] = newGroup
		return newGroup
		# and then never use old `group` object

	def exportData(self, gidList):
		data = OrderedDict([
			("info", OrderedDict([
				("appName", core.APP_NAME),
				("version", core.VERSION),
			])),
			("groups", []),
		])
		for gid in gidList:
			data["groups"].append(self.byId[gid].exportData())
		return data

	def importData(self, data):
		newGroups = []  # type: List[EventGroup]
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
			group.importData(gdata)
			group.save()
			self.append(group)
			res.newGroupIds.add(group.id)

		self.save()
		return res

	def importJsonFile(self, fpath):
		with self.fs.open(fpath, "rb") as fp:
			jsonStr = fp.read()
		self.importData(jsonToData(jsonStr))

	def exportToIcs(self, fpath, gidList):
		fp = self.fs.open(fpath, "w")
		fp.write(ics.icsHeader)
		for gid in gidList:
			self[gid].exportToIcsFp(fp)
		fp.write("END:VCALENDAR\n")
		fp.close()

	def checkForOrphans(self):
		newGroup = EventGroup()
		newGroup.fs = self.fs
		newGroup.setTitle(_("Orphan Events"))
		newGroup.setColor((255, 255, 0))
		newGroup.enable = False
		for gid_fname in self.fs.listdir(groupsDir):
			try:
				gid = int(splitext(gid_fname)[0])
			except ValueError:
				continue
			if gid not in self.idList:
				try:
					self.fs.removeFile(join(groupsDir, gid_fname))
				except Exception:
					log.exception("")
		######
		myEventIds = []
		for group in self:
			myEventIds += group.idList
		myEventIds = set(myEventIds)
		##
		for fname in self.fs.listdir(eventsDir):
			fname_nox, ext = splitext(fname)
			if ext != ".json":
				continue
			try:
				eid = int(fname_nox)
			except ValueError:
				continue
			if eid in myEventIds:
				continue
			newGroup.idList.append(eid)
		if newGroup.idList:
			newGroup.save()
			self.append(newGroup)
			self.save()
			return newGroup
		else:
			return


class EventAccountsHolder(JsonObjectsHolder):
	file = join(confDir, "event", "account_list.json")
	childName = "account"

	def __init__(self, _id=None):
		JsonObjectsHolder.__init__(self)
		self.id = None
		self.parent = None
		self.idByUuid = {}

	def loadClass(self, name):
		cls = classes.account.byName.get(name)
		if cls is not None:
			return cls
		try:
			__import__(f"scal3.account.{name}")
		except ImportError:
			log.exception("")
		else:
			cls = classes.account.byName.get(name)
			if cls is not None:
				return cls
		log.error(
			f"error while loading account: no account type \"{name}\""
		)

	def loadData(self, _id):
		objFile = join(accountsDir, f"{_id}.json")
		if not self.fs.isfile(objFile):
			log.error(
				f"error while loading account file {objFile!r}" +
				": file not found"
			)
			return
			# FIXME: or raise FileNotFoundError?
		with self.fs.open(objFile) as fp:
			data = jsonToData(fp.read())
		updateBasicDataFromBson(data, objFile, "account", self.fs)
		# if data["id"] != _id:
		# 	log.error(
		# 		"attribute 'id' in json file " +
		# 		f"does not match the file name: {objFile}"
		# 	)
		# del data["id"]
		return data

	def getLoadedObj(self, obj):
		_id = obj.id
		data = self.loadData(_id)
		name = data["type"]
		cls = self.loadClass(name)
		if cls is None:
			return
		obj = cls(_id)
		obj.fs = self.fs
		data = self.loadData(_id)
		obj.setData(data)
		return obj

	def replaceDummyObj(self, obj):
		_id = obj.id
		index = self.idList.index(_id)
		obj = self.getLoadedObj(obj)
		self.byId[_id] = obj
		return obj


class EventTrash(EventContainer, WithIcon):
	name = "trash"
	desc = _("Trash")
	file = join(confDir, "event", "trash.json")  # FIXME
	skipLoadNoFile = True
	id = -1  # FIXME
	defaultIcon = "./user-trash.svg"

	@classmethod
	def iterFiles(cls, fs: FileSystem):
		if fs.isfile(cls.file):
			yield cls.file

	def __init__(self):
		EventContainer.__init__(self, title=_("Trash"))
		self.icon = self.defaultIcon
		self.enable = False

	def setData(self, data):
		EventContainer.setData(self, data)
		if not os.path.isfile(self.icon):
			log.info(f"Trash icon {self.icon} does not exist, using {self.defaultIcon}")
			self.icon = self.defaultIcon

	def delete(self, eid):
		from shutil import rmtree
		# different from EventContainer.remove
		# remove() only removes event from this group,
		# but event file and data still available
		# and probably will be added to another event container
		# but after delete(), there is no event file, and not event data
		if not isinstance(eid, int):
			raise TypeError("delete takes event ID that is integer")
		assert eid in self.idList
		try:
			self.fs.removeFile(Event.getFile(eid))
		except Exception:
			log.exception("")
		else:
			self.idList.remove(eid)

	def empty(self):
		from shutil import rmtree
		idList2 = self.idList[:]
		for eid in self.idList:
			try:
				self.fs.removeFile(Event.getFile(eid))
			except Exception:
				log.exception("")
			idList2.remove(eid)
		self.idList = idList2
		self.save()


class DummyAccount:
	loaded = False
	enable = False
	params = ()
	paramsOrder = ()
	accountsDesc = {
		"google": _("Google"),
	}

	def __init__(self, _type, _id, title):
		self.name = _type
		self.desc = self.accountsDesc[_type]
		self.id = _id
		self.title = title

	def save(self):
		pass

	def load(cls, fs: FileSystem, *args):
		pass

	def getLoadedObj(self):
		pass


# Should not be registered, or instantiate directly
@classes.account.setMain
class Account(BsonHistEventObj):
	loaded = True
	name = ""
	desc = ""
	basicParams = (  # FIXME
		# "enable",
		"type",
	)
	params = (
		# "enable",
		"title",
		"remoteGroups",
	)
	paramsOrder = (
		# "enable",
		"type",
		"title",
		"remoteGroups",
	)

	@classmethod
	def getFile(cls, _id):
		return join(accountsDir, f"{_id}.json")

	@classmethod
	def iterFiles(cls, fs: FileSystem):
		for _id in range(1, lastIds.account + 1):
			fpath = cls.getFile(_id)
			if not fs.isfile(fpath):
				continue
			yield fpath

	@classmethod
	def getSubclass(cls, _type):
		return classes.account.byName[_type]

	def __bool__(self):
		return True

	def __init__(self, _id=None):
		if _id is None:
			self.id = None
		else:
			self.setId(_id)
		self.enable = True
		self.title = "Account"

		# a list of dictionarise {"id":..., "title":...}
		self.remoteGroups = []

		# example for status: {"action": "pull", "done": 10, "total": 20}
		# action values: "fetchGroups", "pull", "push"
		self.status = None

	def save(self):
		if self.id is None:
			self.setId()
		BsonHistEventObj.save(self)

	def setId(self, _id=None):
		if _id is None or _id < 0:
			_id = lastIds.account + 1  # FIXME
			lastIds.account = _id
		elif _id > lastIds.account:
			lastIds.account = _id
		self.id = _id
		self.file = self.getFile(self.id)

	def stop(self):
		self.status = None

	def fetchGroups(self):
		raise NotImplementedError

	def fetchAllEventsInGroup(self, remoteGroupId):
		raise NotImplementedError

	def sync(self, group, remoteGroupId):
		raise NotImplementedError

	def getData(self):
		data = BsonHistEventObj.getData(self)
		data["type"] = self.name
		return data


########################################################################

def getDayOccurrenceData(curJd, groups):
	data = []
	for groupIndex, group in enumerate(groups):
		if not group.enable:
			continue
		if not group.showInCal():
			continue
		# log.debug("\nupdateData: checking event", event.summary)
		gid = group.id
		color = group.color
		for epoch0, epoch1, eid, odt in group.occur.search(
			getEpochFromJd(curJd),
			getEpochFromJd(curJd + 1),
		):
			event = group[eid]
			###
			text = event.getTextParts()
			###
			timeStr = ""
			if epoch1 - epoch0 < dayLen:
				jd0, h0, m0, s0 = getJhmsFromEpoch(epoch0)
				if jd0 < curJd:
					h0, m0, s0 = 0, 0, 0
				if epoch1 - epoch0 < 1:
					timeStr = timeEncode((h0, m0, s0), True)
				else:
					jd1, h1, m1, s1 = getJhmsFromEpoch(epoch1)
					if jd1 > curJd:
						h1, m1, s1 = 24, 0, 0
					timeStr = hmsRangeToStr(h0, m0, s0, h1, m1, s1)
			###
			try:
				eventIndex = group.index(eid)
			except ValueError:
				eventIndex = event.modified  # FIXME
			data.append((
				(epoch0, epoch1, groupIndex, eventIndex),  # FIXME for sorting
				{
					"time": timeStr,
					"time_epoch": (epoch0, epoch1),
					"is_allday": epoch0 % dayLen + epoch1 % dayLen == 0,
					"text": text,
					"icon": event.getIconRel(),
					"color": color,
					"ids": (gid, eid),
					"show": (
						group.showInDCal,
						group.showInWCal,
						group.showInMCal,
					),
					"showInStatusIcon": group.showInStatusIcon,
				}
			))
	data.sort()
	return [item[1] for item in data]


def getWeekOccurrenceData(curAbsWeekNumber, groups):
	startJd = core.getStartJdOfAbsWeekNumber(absWeekNumber)
	endJd = startJd + 7
	data = []
	for group in groups:
		if not group.enable:
			continue
		for event in group:
			if not event:
				continue
			occur = event.calcOccurrence(startJd, endJd)
			if not occur:
				continue
			text = event.getText()
			icon = event.getIconRel()
			ids = (group.id, event.id)
			if isinstance(occur, JdOccurSet):
				for jd in occur.getDaysJdList():
					wnum, weekDay = core.getWeekDateFromJd(jd)
					if wnum == curAbsWeekNumber:
						data.append({
							"weekDay": weekDay,
							"time": "",
							"text": text,
							"icon": icon,
							"ids": ids,
						})
			elif isinstance(occur, IntervalOccurSet):
				for startEpoch, endEpoch in occur.getTimeRangeList():
					jd1, h1, min1, s1 = getJhmsFromEpoch(startEpoch)
					jd2, h2, min2, s2 = getJhmsFromEpoch(endEpoch)
					wnum, weekDay = core.getWeekDateFromJd(jd1)
					if wnum == curAbsWeekNumber:
						if jd1 == jd2:
							data.append({
								"weekDay": weekDay,
								"time": hmsRangeToStr(
									h1, min1, s1,
									h2, min2, s2,
								),
								"text": text,
								"icon": icon,
								"ids": ids,
							})
						else:  # FIXME
							data.append({
								"weekDay": weekDay,
								"time": hmsRangeToStr(
									h1, min1, s1,
									24, 0, 0,
								),
								"text": text,
								"icon": icon,
								"ids": ids,
							})
							for jd in range(jd1 + 1, jd2):
								wnum, weekDay = core.getWeekDateFromJd(jd)
								if wnum == curAbsWeekNumber:
									data.append({
										"weekDay": weekDay,
										"time": "",
										"text": text,
										"icon": icon,
										"ids": ids,
									})
								else:
									break
							wnum, weekDay = core.getWeekDateFromJd(jd2)
							if wnum == curAbsWeekNumber:
								data.append({
									"weekDay": weekDay,
									"time": hmsRangeToStr(
										0, 0, 0,
										h2, min2, s2,
									),
									"text": text,
									"icon": icon,
									"ids": ids,
								})
			elif isinstance(occur, TimeListOccurSet):
				for epoch in occur.epochList:
					jd, hour, minute, sec = getJhmsFromEpoch(epoch)
					wnum, weekDay = core.getWeekDateFromJd(jd)
					if wnum == curAbsWeekNumber:
						data.append({
							"weekDay": weekDay,
							"time": timeEncode((hour, minute, sec), True),
							"text": text,
							"icon": icon,
							"ids": ids,
						})
			else:
				raise TypeError
	return data


def getMonthOccurrenceData(curYear, curMonth, groups):
	startJd, endJd = core.getJdRangeForMonth(curYear, curMonth, calTypes.primary)
	data = []
	for group in groups:
		if not group.enable:
			continue
		for event in group:
			if not event:
				continue
			occur = event.calcOccurrence(startJd, endJd)
			if not occur:
				continue
			text = event.getText()
			icon = event.getIconRel()
			ids = (group.id, event.id)
			if isinstance(occur, JdOccurSet):
				for jd in occur.getDaysJdList():
					y, m, d = jd_to_primary(jd)
					if y == curYear and m == curMonth:
						data.append({
							"day": d,
							"time": "",
							"text": text,
							"icon": icon,
							"ids": ids,
						})
			elif isinstance(occur, IntervalOccurSet):
				for startEpoch, endEpoch in occur.getTimeRangeList():
					jd1, h1, min1, s1 = getJhmsFromEpoch(startEpoch)
					jd2, h2, min2, s2 = getJhmsFromEpoch(endEpoch)
					y, m, d = jd_to_primary(jd1)
					if y == curYear and m == curMonth:
						if jd1 == jd2:
							data.append({
								"day": d,
								"time": hmsRangeToStr(
									h1, min1, s1,
									h2, min2, s2,
								),
								"text": text,
								"icon": icon,
								"ids": ids,
							})
						else:  # FIXME
							data.append({
								"day": d,
								"time": hmsRangeToStr(
									h1, min1, s1,
									24, 0, 0,
								),
								"text": text,
								"icon": icon,
								"ids": ids,
							})
							for jd in range(jd1 + 1, jd2):
								y, m, d = jd_to_primary(jd)
								if y == curYear and m == curMonth:
									data.append({
										"day": d,
										"time": "",
										"text": text,
										"icon": icon,
										"ids": ids,
									})
								else:
									break
							y, m, d = jd_to_primary(jd2)
							if y == curYear and m == curMonth:
								data.append({
									"day": d,
									"time": hmsRangeToStr(
										0, 0, 0,
										h2, min2, s2,
									),
									"text": text,
									"icon": icon,
									"ids": ids,
								})
			elif isinstance(occur, TimeListOccurSet):
				for epoch in occur.epochList:
					jd, hour, minute, sec = getJhmsFromEpoch(epoch)
					y, m, d = jd_to_primary(jd1)
					if y == curYear and m == curMonth:
						data.append({
							"day": d,
							"time": timeEncode((hour, minute, sec), True),
							"text": text,
							"icon": icon,
							"ids": ids,
						})
			else:
				raise TypeError
	return data
