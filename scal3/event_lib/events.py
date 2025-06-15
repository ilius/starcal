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

from time import localtime
from typing import TYPE_CHECKING

from scal3 import core, ics
from scal3.cal_types import (
	GREGORIAN,
	getSysDate,
	jd_to,
	to_jd,
)
from scal3.date_utils import jwday
from scal3.locale_man import getMonthName
from scal3.locale_man import tr as _
from scal3.time_utils import (
	getFloatJdFromEpoch,
	jsonTimeFromEpoch,
	roundEpochToDay,
)
from scal3.utils import iceil, ifloor

from .event_base import Event
from .occur import IntervalOccurSet, JdOccurSet
from .register import classes
from .rules import (
	CycleWeeksEventRule,
	DateAndTimeEventRule,
	DateEventRule,
	DayOfMonthEventRule,
	DayTimeEventRule,
	DayTimeRangeEventRule,
	DurationEventRule,
	EndEventRule,
	MonthEventRule,
	StartEventRule,
	WeekDayEventRule,
	WeekNumberModeEventRule,
)

if TYPE_CHECKING:
	from typing import Any

	from .event_container import EventContainer
	from .groups import EventGroup, TaskList, UniversityTerm, YearlyGroup
	from .occur import OccurSet
	from .pytypes import EventRuleType


__all__ = [
	"AllDayTaskEvent",
	"DailyNoteEvent",
	"Event",
	"LargeScaleEvent",
	"LifetimeEvent",
	"MonthlyEvent",
	"SingleStartEndEvent",
	"TaskEvent",
	"UniversityClassEvent",
	"UniversityExamEvent",
	"WeeklyEvent",
	"YearlyEvent",
]


dayLen = 24 * 3600
icsMinStartYear = 1970
# icsMaxEndYear = 2050


class SingleStartEndEvent(Event):
	isSingleOccur = True

	def setStartEpoch(self, epoch: int) -> None:
		start = StartEventRule.addOrGetFrom(self)
		start.setEpoch(epoch)

	def setEndEpoch(self, epoch: int) -> None:
		end = EndEventRule.addOrGetFrom(self)
		end.setEpoch(epoch)

	def setJd(self, jd: int) -> None:
		start = StartEventRule.addOrGetFrom(self)
		start.setJd(jd)

	def setJdExact(self, jd: int) -> None:
		start = StartEventRule.addOrGetFrom(self)
		end = EndEventRule.addOrGetFrom(self)
		start.setJdExact(jd)
		end.setJdExact(jd + 1)

	def getIcsData(self, prettyDateTime: bool = False) -> list[tuple[str, str]] | None:
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
	requiredRules: list[str] = ["start"]
	supportedRules = [
		"start",
		"end",
		"duration",
	]
	isAllDay = False

	def getV4Dict(self) -> dict[str, Any]:
		duration = DurationEventRule.getFrom(self)
		if duration is None:
			durationUnit = 0
		else:
			durationUnit = duration.unit

		data = Event.getV4Dict(self)
		data.update(
			{
				"startTime": jsonTimeFromEpoch(self.getStartEpoch()),
				"endTime": jsonTimeFromEpoch(self.getEndEpoch()),
				"durationUnit": durationUnit,
			},
		)
		return data

	def _setDefaultDuration(self, group: EventGroup | None) -> None:
		if group is None or group.name != "taskList":
			self.setEnd("duration", 1, 3600)
			return
		if TYPE_CHECKING:
			assert isinstance(group, TaskList)

		value, unit = group.defaultDuration
		if value == 0:
			value, unit = 1, 3600
		self.setEnd("duration", value, unit)

	def setDefaults(self, group: EventGroup | None = None) -> None:
		Event.setDefaults(self, group=group)
		tt = localtime()
		self.setStart(
			getSysDate(self.calType),
			(tt.tm_hour, tt.tm_min, tt.tm_sec),
		)
		self._setDefaultDuration(group)

	def setJdExact(self, jd: int) -> None:
		start = StartEventRule.getFrom(self)
		assert start is not None
		start.setJdExact(jd)
		self.setEnd("duration", 24, 3600)

	def setStart(
		self,
		date: tuple[int, int, int],
		dayTime: tuple[int, int, int],
	) -> None:
		start = StartEventRule.getFrom(self)
		if start is None:
			raise KeyError('rule "start" not found')
		start.date = date
		start.time = dayTime

	def setEnd(
		self,
		endType: str,
		*values,  # noqa: ANN002
	) -> None:
		self.removeSomeRuleTypes("end", "duration")
		rule: EventRuleType
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

	def getStart(self) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
		start = StartEventRule.getFrom(self)
		if start is None:
			raise KeyError('rule "start" not found')
		return (start.date, start.time)

	def getEnd(
		self,
	) -> tuple[
		str,
		tuple[tuple[int, int, int], tuple[int, int, int]] | tuple[float, int],
	]:
		end = EndEventRule.getFrom(self)
		if end is not None:
			return ("date", (end.date, end.time))
		duration = DurationEventRule.getFrom(self)
		if duration is not None:
			return ("duration", (duration.value, duration.unit))
		raise ValueError("no end date neither duration specified for task")

	def getEndEpoch(self) -> int:
		end = EndEventRule.getFrom(self)
		if end is not None:
			return end.getEpoch()
		duration = DurationEventRule.getFrom(self)
		if duration is not None:
			start = StartEventRule.getFrom(self)
			if start is not None:
				return start.getEpoch() + duration.getSeconds()
			raise RuntimeError("found duration rule without start rule")
		raise ValueError("no end date neither duration specified for task")

	def setEndEpoch(self, epoch: int) -> None:
		end = EndEventRule.getFrom(self)
		if end is not None:
			end.setEpoch(epoch)
			return
		duration = DurationEventRule.getFrom(self)
		if duration is not None:
			start = StartEventRule.getFrom(self)
			if start is not None:
				duration.setSeconds(epoch - start.getEpoch())
			else:
				raise RuntimeError("found duration rule without start rule")
			return
		raise ValueError("no end date neither duration specified for task")

	def modifyPos(self, newStartEpoch: int) -> None:
		start = StartEventRule.getFrom(self)
		if start is None:
			raise KeyError
		end = EndEventRule.getFrom(self)
		if end is not None:
			end.setEpoch(end.getEpoch() + newStartEpoch - start.getEpoch())
		start.setEpoch(newStartEpoch)

	def modifyStart(self, newStartEpoch: int) -> None:
		start = StartEventRule.getFrom(self)
		if start is None:
			raise KeyError
		duration = DurationEventRule.getFrom(self)
		if duration is not None:
			duration.value -= (newStartEpoch - start.getEpoch()) / duration.unit
		start.setEpoch(newStartEpoch)

	def modifyEnd(self, newEndEpoch: int) -> None:
		end = EndEventRule.getFrom(self)
		if end is not None:
			end.setEpoch(newEndEpoch)
		else:
			duration = DurationEventRule.getFrom(self)
			if duration is not None:
				duration.value = (newEndEpoch - self.getStartEpoch()) / duration.unit
			else:
				raise RuntimeError("no end rule nor duration rule")

	def copyFrom(
		self,
		other: Event,
		*a,  # noqa: ANN002
		**kw,  # noqa: ANN003
	) -> None:
		Event.copyFrom(self, other, *a, **kw)
		myStart = StartEventRule.getFrom(self)
		if myStart is None:
			raise KeyError
		# --
		if other.name == self.name:
			assert isinstance(other, TaskEvent)
			endType, values = other.getEnd()
			self.setEnd(endType, *values)
		elif other.name == "dailyNote":
			myStart.time = (0, 0, 0)
			self.setEnd("duration", 24, 3600)
		elif other.name == "allDayTask":
			self.removeSomeRuleTypes("end", "duration")
			self.copySomeRuleTypesFrom(other, "start", "end", "duration")
		else:
			otherDayTime = DayTimeEventRule.getFrom(self)
			if otherDayTime is not None:
				myStart.time = otherDayTime.dayTime

	def setIcsData(self, data: dict[str, str]) -> bool:
		self.setStartEpoch(ics.getEpochByIcsTime(data["DTSTART"]))
		self.setEndEpoch(ics.getEpochByIcsTime(data["DTEND"]))  # FIXME
		return True


@classes.event.register
class AllDayTaskEvent(SingleStartEndEvent):
	# overwrites getEndEpoch from SingleStartEndEvent
	name = "allDayTask"
	desc = _("All-Day Task")
	iconName = "task"
	requiredRules = ["start"]
	supportedRules = [
		"start",
		"end",
		"duration",
	]
	isAllDay = True

	def getV4Dict(self) -> dict[str, Any]:
		if DurationEventRule.getFrom(self) is None:
			durationEnable = False
		else:
			durationEnable = True

		data = Event.getV4Dict(self)
		data.update(
			{
				"startJd": self.getStartJd(),
				"endJd": self.getEndJd(),
				"durationEnable": durationEnable,
			},
		)
		return data

	def setJd(self, jd: int) -> None:
		start = StartEventRule.addOrGetFrom(self)
		start.setJdExact(jd)

	def setStartDate(self, date: tuple[int, int, int]) -> None:
		start = StartEventRule.addOrGetFrom(self)
		start.setDate(date)

	def setJdExact(self, jd: int) -> None:
		self.setJd(jd)
		self.setEnd("duration", 1)

	def setDefaults(self, group: EventGroup | None = None) -> None:
		Event.setDefaults(self, group=group)
		jd = core.getCurrentJd()
		self.setJd(jd)
		self.setEnd("duration", 1)
		# if group and group.name == "taskList":
		# 	value, unit = group.defaultAllDayDuration
		# 	if value > 0:
		# 		self.setEnd("duration", value)

	def setEnd(self, endType: str, value: tuple[int, int, int] | float) -> None:
		self.removeSomeRuleTypes("end", "duration")
		rule: EventRuleType
		if endType == "date":
			assert isinstance(value, tuple)
			rule = EndEventRule(self)
			rule.setDate(value)
		elif endType == "jd":
			assert isinstance(value, int)
			rule = EndEventRule(self)
			rule.setJd(value)
		elif endType == "epoch":
			assert isinstance(value, int)
			rule = EndEventRule(self)
			rule.setJd(self.getJdFromEpoch(value))
		elif endType == "duration":
			assert isinstance(value, float)
			rule = DurationEventRule(self)
			rule.value = value
			rule.unit = dayLen
		else:
			raise ValueError(f"invalid {endType=}")
		self.addRule(rule)

	def getEnd(self) -> tuple[str, tuple[int, int, int] | float]:
		end = EndEventRule.getFrom(self)
		if end is not None:
			return ("date", end.date)
		duration = DurationEventRule.getFrom(self)
		if duration is not None:
			return ("duration", duration.value)
		raise ValueError("no end date neither duration specified for task")

	def getEndJd(self) -> int:
		end = EndEventRule.getFrom(self)
		if end is not None:
			# assert isinstance(end.getJd(), int)
			return end.getJd()
		duration = DurationEventRule.getFrom(self)
		if duration is not None:
			start = StartEventRule.getFrom(self)
			if start is None:
				raise RuntimeError("no start rule")
			# assert isinstance(start.getJd(), int)
			return start.getJd() + duration.getSeconds() // dayLen
		raise ValueError("no end date neither duration specified for task")

	def getEndEpoch(self) -> int:
		# if not isinstance(self.getEndJd(), int):
		# 	raise TypeError(f"{self}.getEndJd() returned non-int: {self.getEndJd()}")
		return self.getEpochFromJd(self.getEndJd())

	# def setEndJd(self, jd):
	# 	EndEventRule.getFrom(self).setJdExact(jd)

	def setEndJd(self, jd: int) -> None:
		end = EndEventRule.getFrom(self)
		if end is not None:
			end.setJd(jd)
			return
		duration = DurationEventRule.getFrom(self)
		if duration is not None:
			start = StartEventRule.getFrom(self)
			if start is not None:
				duration.setSeconds(dayLen * (jd - start.getJd()))
				return
		raise ValueError("no end date neither duration specified for task")

	def getIcsData(self, prettyDateTime: bool = False) -> list[tuple[str, str]] | None:
		return [
			("DTSTART", ics.getIcsDateByJd(self.getJd(), prettyDateTime)),
			("DTEND", ics.getIcsDateByJd(self.getEndJd(), prettyDateTime)),
			("TRANSP", "OPAQUE"),
			("CATEGORIES", self.name),  # FIXME
		]

	def setIcsData(self, data: dict[str, str]) -> bool:
		self.setJd(ics.getJdByIcsDate(data["DTSTART"]))
		self.setEndJd(ics.getJdByIcsDate(data["DTEND"]))  # FIXME
		return True

	def copyFrom(self, other: Event) -> None:
		SingleStartEndEvent.copyFrom(self, other)
		if other.name == self.name:
			assert isinstance(other, AllDayTaskEvent)
			kind, value = other.getEnd()
			self.setEnd(kind, value)


@classes.event.register
class DailyNoteEvent(Event):
	name = "dailyNote"
	desc = _("Daily Note")
	isSingleOccur = True
	iconName = "note"
	requiredRules = ["date"]
	supportedRules = ["date"]
	isAllDay = True

	def getV4Dict(self) -> dict[str, Any]:
		data = Event.getV4Dict(self)
		data.update(
			{
				"jd": self.getJd(),
			},
		)
		return data

	def getDate(self) -> tuple[int, int, int] | None:
		rule = DateEventRule.getFrom(self)
		if rule is not None:
			return rule.date
		return None

	def setDate(self, year: int, month: int, day: int) -> None:
		rule = DateEventRule.getFrom(self)
		if rule is None:
			raise KeyError("no date rule")
		rule.date = (year, month, day)

	def getJd(self) -> int:
		rule = DateEventRule.getFrom(self)
		if rule is not None:
			return rule.getJd()
		return self.getStartJd()

	def setJd(self, jd: int) -> None:
		rule = DateEventRule.getFrom(self)
		if rule is None:
			log.error("DailyNoteEvent: setJd: no date rule")
			return
		rule.setJd(jd)

	def setDefaults(self, group: EventGroup | None = None) -> None:
		Event.setDefaults(self, group=group)
		self.setDate(*getSysDate(self.calType))

	# startJd and endJd can be float jd
	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSet:
		jd = self.getJd()
		return JdOccurSet(
			{jd} if startJd <= jd < endJd else set(),
		)

	def getIcsData(self, prettyDateTime: bool = False) -> list[tuple[str, str]] | None:
		jd = self.getJd()
		return [
			("DTSTART", ics.getIcsDateByJd(jd, prettyDateTime)),
			("DTEND", ics.getIcsDateByJd(jd + 1, prettyDateTime)),
			("TRANSP", "TRANSPARENT"),
			("CATEGORIES", self.name),  # FIXME
		]

	def setIcsData(self, data: dict[str, str]) -> bool:
		self.setJd(ics.getJdByIcsDate(data["DTSTART"]))
		return True


@classes.event.register
class YearlyEvent(Event):
	name = "yearly"
	desc = _("Yearly Event")
	iconName = "birthday"
	requiredRules = [
		"month",
		"day",
	]
	supportedRules = requiredRules + ["start"]
	paramsOrder: list[str] = Event.paramsOrder + [
		"startYear",
		"month",
		"day",
	]
	isAllDay = True

	def getV4Dict(self) -> dict[str, Any]:
		data = Event.getV4Dict(self)
		data.update(
			{
				"month": self.getMonth(),
				"day": self.getDay(),
			},
		)
		start = StartEventRule.getFrom(self)
		if start is not None:
			data["startYear"] = int(start.date[0])
			data["startYearEnable"] = True
		else:
			data["startYearEnable"] = False
		return data

	def getMonth(self) -> int | None:
		rule = MonthEventRule.getFrom(self)
		if rule is not None:
			return rule.values[0]
		return None

	def setMonth(self, month: int) -> MonthEventRule:
		rule = MonthEventRule.addOrGetFrom(self)
		rule.setRuleValue(month)
		return rule

	def getDay(self) -> int | None:
		rule = DayOfMonthEventRule.getFrom(self)
		if rule is None:
			return None
		value = rule.values[0]
		if isinstance(value, int):
			return value
		if isinstance(value, tuple):
			return value[0]
		log.error(f"invalid DayOfMonthEventRule values = {rule.values}")
		return None

	def setDay(self, day: int) -> DayOfMonthEventRule:
		rule = DayOfMonthEventRule.addOrGetFrom(self)
		rule.setRuleValue(day)
		return rule

	def setDefaults(self, group: EventGroup | None = None) -> None:
		Event.setDefaults(self, group=group)
		_y, m, d = getSysDate(self.calType)
		self.setMonth(m)
		self.setDay(d)

	def getJd(self) -> int:  # used only for copyFrom
		assert self.calType is not None
		startRule = StartEventRule.getFrom(self)
		if startRule is not None:
			y = startRule.getDate(self.calType)[0]
		else:
			y = getSysDate(self.calType)[0]
		month = self.getMonth()
		assert month is not None
		day = self.getDay()
		assert day is not None
		return to_jd(y, month, day, self.calType)

	def setJd(self, jd: int) -> None:  # used only for copyFrom
		y, m, d = jd_to(jd, self.calType)
		self.setMonth(m)
		self.setDay(d)
		start = StartEventRule.addOrGetFrom(self)
		start.date = (y, 1, 1)

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSet:
		# startJd and endJd can be float? or they are just int? FIXME
		calType = self.calType
		month = self.getMonth()
		day = self.getDay()
		if month is None:
			log.error(f"month is None for eventId={self.id}")
			return JdOccurSet()
		if day is None:
			log.error(f"day is None for eventId={self.id}")
			return JdOccurSet()
		startRule = StartEventRule.getFrom(self)
		if startRule is not None:
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

	def getDict(self) -> dict[str, Any]:
		data = Event.getDict(self)
		start = StartEventRule.getFrom(self)
		if start is not None:
			data["startYear"] = int(start.date[0])
		data["month"] = self.getMonth()
		data["day"] = self.getDay()
		del data["rules"]
		return data

	def setDict(self, data: dict[str, Any]) -> None:
		Event.setDict(self, data)
		try:
			startYear = int(data["startYear"])
		except KeyError:
			pass
		except Exception as e:
			log.info(str(e))
		else:
			start = StartEventRule.addOrGetFrom(self)
			start.date = (startYear, 1, 1)
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

	def getSuggestedStartYear(self) -> int:
		if self.parent is None:
			startJd = core.getCurrentJd()
		else:
			startJd = self.parent.startJd
		return jd_to(startJd, self.calType)[0]

	def getSummary(self) -> str:
		summary = Event.getSummary(self)
		if self.parent and self.parent.name == "yearly":
			if TYPE_CHECKING:
				assert isinstance(self.parent, YearlyGroup)
			showDate = self.parent.showDate
		else:
			showDate = True
		if showDate:
			newParts: list[str] = []
			day = self.getDay()
			month = self.getMonth()
			if day is not None and month is not None:
				newParts = [
					_(day),
					getMonthName(self.calType, month),
				]
			start = StartEventRule.getFrom(self)
			if start is not None:
				newParts.append(_(start.date[0]))
			summary = " ".join(newParts) + ": " + summary
		return summary

	def getIcsData(self, prettyDateTime: bool = False) -> list[tuple[str, str]] | None:
		if self.calType != GREGORIAN:
			return None
		month = self.getMonth()
		day = self.getDay()
		assert month is not None
		assert day is not None
		startYear = icsMinStartYear
		startRule = StartEventRule.getFrom(self)
		if startRule is not None:
			startYear = startRule.getDate(GREGORIAN)[0]
		elif getattr(self.parent, "startJd", None):
			assert self.parent is not None
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

	def setIcsData(self, data: dict[str, str]) -> bool:
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
	requiredRules = [
		"start",
		"end",
		"day",
		"dayTimeRange",
	]
	supportedRules = requiredRules
	isAllDay = False

	def getV4Dict(self) -> dict[str, Any]:
		data = Event.getV4Dict(self)
		dayTimeRange = DayTimeRangeEventRule.getFrom(self)
		assert dayTimeRange is not None
		startSec, endSec = dayTimeRange.getSecondsRange()
		start = StartEventRule.getFrom(self)
		assert start is not None
		end = EndEventRule.getFrom(self)
		assert end is not None
		data.update(
			{
				"startJd": start.getJd(),
				"endJd": end.getJd(),
				"day": self.getDay(),
				"dayStartSeconds": startSec,
				"dayEndSeconds": endSec,
			},
		)
		return data

	def setDefaults(self, group: EventGroup | None = None) -> None:
		Event.setDefaults(self, group=group)
		year, month, day = jd_to(core.getCurrentJd(), self.calType)
		start = StartEventRule.getFrom(self)
		if start is not None:
			start.setDate((year, month, 1))
		else:
			raise RuntimeError("no start rule")
		end = EndEventRule.getFrom(self)
		if end is not None:
			end.setDate((year + 1, month, 1))
		else:
			raise RuntimeError("no end rule")
		self.setDay(day)

	def getDay(self) -> int:
		rule = DayOfMonthEventRule.getFrom(self)
		if rule is None:
			raise RuntimeError("no day rule")
		if not rule.values:
			return 1
		value = rule.values[0]
		if isinstance(value, int):
			return value
		if isinstance(value, tuple):
			return value[0]
		raise RuntimeError(f"bad {rule.values}")

	def setDay(self, day: int) -> None:
		rule = DayOfMonthEventRule.getFrom(self)
		if rule is None:
			raise RuntimeError("no day rule")
		rule.values = [day]


@classes.event.register
class WeeklyEvent(Event):
	name = "weekly"
	desc = _("Weekly Event")
	iconName = ""
	requiredRules = [
		"start",
		"end",
		"cycleWeeks",
		"dayTimeRange",
	]
	supportedRules = requiredRules
	isAllDay = False

	def getV4Dict(self) -> dict[str, Any]:
		data = Event.getV4Dict(self)
		dayTimeRange = DayTimeRangeEventRule.getFrom(self)
		assert dayTimeRange is not None
		startSec, endSec = dayTimeRange.getSecondsRange()
		start = StartEventRule.getFrom(self)
		assert start is not None
		end = EndEventRule.getFrom(self)
		assert end is not None
		cycleWeeks = CycleWeeksEventRule.getFrom(self)
		assert cycleWeeks is not None
		data.update(
			{
				"startJd": start.getJd(),
				"endJd": end.getJd(),
				"cycleWeeks": cycleWeeks.getRuleValue(),
				"dayStartSeconds": startSec,
				"dayEndSeconds": endSec,
			},
		)
		return data

	def setDefaults(self, group: EventGroup | None = None) -> None:
		Event.setDefaults(self, group=group)
		jd = core.getCurrentJd()
		start = StartEventRule.getFrom(self)
		if start is None:
			raise RuntimeError("no start rule")
		end = EndEventRule.getFrom(self)
		if end is None:
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
	requiredRules = [
		"weekNumMode",
		"weekDay",
		"dayTimeRange",
	]
	supportedRules = [
		"weekNumMode",
		"weekDay",
		"dayTimeRange",
	]
	params: list[str] = Event.params + ["courseId"]
	isAllDay = False

	def getV4Dict(self) -> dict[str, Any]:
		data = Event.getV4Dict(self)
		dayTimeRange = DayTimeRangeEventRule.getFrom(self)
		assert dayTimeRange is not None
		startSec, endSec = dayTimeRange.getSecondsRange()
		weekNumMode = WeekNumberModeEventRule.getFrom(self)
		assert weekNumMode is not None
		weekDay = WeekDayEventRule.getFrom(self)
		assert weekDay is not None
		data.update(
			{
				"weekNumMode": weekNumMode.getRuleValue(),
				"weekDayList": weekDay.getRuleValue(),
				"dayStartSeconds": startSec,
				"dayEndSeconds": endSec,
				"courseId": self.courseId,
			},
		)
		return data

	def __init__(
		self,
		ident: int | None = None,
		parent: EventContainer | None = None,
	) -> None:
		# assert parent is not None
		Event.__init__(self, ident, parent)
		self.courseId: int | None = None  # FIXME

	def setDefaults(
		self,
		group: EventGroup | None = None,
	) -> None:
		Event.setDefaults(self, group=group)
		if group and group.name == "universityTerm":
			if TYPE_CHECKING:
				assert isinstance(group, UniversityTerm)
			try:
				tm0, tm1 = group.classTimeBounds[:2]
			except ValueError:
				log.exception("")
			else:
				rule = DayTimeRangeEventRule.getFrom(self)
				if rule is None:
					raise RuntimeError("no dayTimeRange rule")
				rule.setRange(
					tm0 + (0,),
					tm1 + (0,),
				)

	def getCourseName(self) -> str:
		assert self.parent is not None
		assert self.courseId is not None
		return self.parent.getCourseNameById(self.courseId)

	def getWeekDayName(self) -> str:
		rule = WeekDayEventRule.getFrom(self)
		if rule is None:
			raise RuntimeError("no weekDay rule")
		return core.weekDayName[rule.weekDayList[0]]

	def updateSummary(self) -> None:
		self.summary = (
			_("{courseName} Class").format(courseName=self.getCourseName())
			+ " ("
			+ self.getWeekDayName()
			+ ")"
		)

	def setJd(self, jd: int) -> None:
		rule = WeekDayEventRule.getFrom(self)
		if rule is None:
			raise RuntimeError("no weekDay rule")
		rule.weekDayList = [jwday(jd)]
		# set weekNumMode from absWeekNumber FIXME

	def getIcsData(self, prettyDateTime: bool = False) -> list[tuple[str, str]] | None:
		start = StartEventRule.getFrom(self)
		if start is None:
			raise RuntimeError("no start rule")
		end = EndEventRule.getFrom(self)
		if end is None:
			raise RuntimeError("no end rule")
		startJd = start.getJd()
		endJd = end.getJd()
		occur = self.calcEventOccurrenceIn(startJd, endJd)
		tRangeList = occur.getTimeRangeList()
		if not tRangeList:
			return None
		weekNumMode = WeekNumberModeEventRule.getFrom(self)
		if weekNumMode is None:
			raise RuntimeError("no weekNumMode rule")
		weekDay = WeekDayEventRule.getFrom(self)
		if weekDay is None:
			raise RuntimeError("no weekDay rule")
		until = ics.getIcsDateByJd(endJd, prettyDateTime)
		interval = 1 if weekNumMode.getRuleValue() == "any" else 2
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
	requiredRules = [
		"date",
		"dayTimeRange",
	]
	supportedRules = [
		"date",
		"dayTimeRange",
	]
	params = DailyNoteEvent.params + ["courseId"]
	isAllDay = False

	def getV4Dict(self) -> dict[str, Any]:
		data = Event.getV4Dict(self)
		dayTimeRange = DayTimeRangeEventRule.getFrom(self)
		assert dayTimeRange is not None
		startSec, endSec = dayTimeRange.getSecondsRange()
		data.update(
			{
				"jd": self.getJd(),
				"dayStartSeconds": startSec,
				"dayEndSeconds": endSec,
				"courseId": self.courseId,
			},
		)
		return data

	def __init__(
		self,
		ident: int | None = None,
		parent: EventContainer | None = None,
	) -> None:
		# assert group is not None  # FIXME
		DailyNoteEvent.__init__(self, ident, parent)
		self.courseId: int | None = None  # FIXME

	def setDefaults(self, group: EventGroup | None = None) -> None:
		DailyNoteEvent.setDefaults(self, group=group)
		dayTimeRange = DayTimeRangeEventRule.getFrom(self)
		if dayTimeRange is None:
			raise RuntimeError("no dayTimeRange rule")
		dayTimeRange.setRange((9, 0, 0), (11, 0, 0))  # FIXME
		if group and group.name == "universityTerm":
			self.setJd(group.endJd)  # FIXME

	def getCourseName(self) -> str:
		assert self.parent is not None
		assert self.courseId is not None
		return self.parent.getCourseNameById(self.courseId)

	def updateSummary(self) -> None:
		self.summary = _("{courseName} Exam").format(
			courseName=self.getCourseName(),
		)

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSet:
		jd = self.getJd()
		if not startJd <= jd < endJd:
			return IntervalOccurSet()

		epoch = self.getEpochFromJd(jd)
		dayTimeRange = DayTimeRangeEventRule.getFrom(self)
		if dayTimeRange is None:
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

	def getIcsData(self, prettyDateTime: bool = False) -> list[tuple[str, str]] | None:
		date = DateEventRule.getFrom(self)
		if date is None:
			raise RuntimeError("no date rule")
		dayStart = date.getEpoch()
		dayTimeRange = DayTimeRangeEventRule.getFrom(self)
		if dayTimeRange is None:
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
	requiredRules = [
		"start",
		"end",
	]
	supportedRules = [
		"start",
		"end",
	]
	isAllDay = True

	# def setDefaults(self):
	# 	start = StartEventRule.getFrom(self)
	# 	if XX is not None:
	# 		start.date = ...

	def getV4Dict(self) -> dict[str, str]:
		data = Event.getV4Dict(self)
		data.update(
			{
				"startJd": self.getStartJd(),
				"endJd": self.getEndJd(),
			},
		)
		return data

	def setJd(self, jd: int) -> None:
		StartEventRule.addOrGetFrom(self).setJdExact(jd)
		EndEventRule.addOrGetFrom(self).setJdExact(jd)

	def addRule(self, rule: EventRuleType) -> None:
		if rule.name in {"start", "end"}:
			assert isinstance(rule, DateAndTimeEventRule)
			rule.time = (0, 0, 0)
		SingleStartEndEvent.addRule(self, rule)

	def modifyPos(self, newStartEpoch: int) -> None:
		start = StartEventRule.getFrom(self)
		assert start is not None
		end = EndEventRule.getFrom(self)
		assert end is not None
		newStartJd = round(getFloatJdFromEpoch(newStartEpoch))
		end.setJdExact(end.getJd() + newStartJd - start.getJd())
		start.setJdExact(newStartJd)

	def modifyStart(self, newEpoch: int) -> None:
		start = StartEventRule.getFrom(self)
		if start is None:
			raise RuntimeError("no start rule")
		start.setEpoch(roundEpochToDay(newEpoch))

	def modifyEnd(self, newEpoch: int) -> None:
		end = EndEventRule.getFrom(self)
		if end is None:
			raise RuntimeError("no end rule")
		end.setEpoch(roundEpochToDay(newEpoch))


@classes.event.register
class LargeScaleEvent(Event):  # or MegaEvent? FIXME
	name = "largeScale"
	desc = _("Large Scale Event")
	isSingleOccur = True
	_myParams = [
		"scale",
		"start",
		"end",
		"endRel",
	]
	params = Event.params + _myParams
	paramsOrder = Event.paramsOrder + _myParams

	def __bool__(self) -> bool:
		return True

	isAllDay = True

	def getV4Dict(self) -> dict[str, Any]:
		data = Event.getV4Dict(self)
		data.update(
			{
				"scale": self.scale,
				"start": self.start,
				"end": self.end,
				"durationEnable": self.endRel,
			},
		)
		return data

	def __init__(
		self,
		ident: int | None = None,
		parent: EventContainer | None = None,
	) -> None:
		self.scale = 1  # 1, 1000, 1000**2, 1000**3
		self.start = 0
		self.end = 1
		self.endRel = True
		Event.__init__(self, ident, parent)

	def setDict(self, data: dict[str, Any]) -> None:
		Event.setDict(self, data)
		if "duration" in data:
			data["end"] = data["duration"]
			data["endRel"] = True

	def getRulesHash(self) -> int:
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

	def getEnd(self) -> int:
		return self.start + self.end if self.endRel else self.end

	def setDefaults(self, group: EventGroup | None = None) -> None:
		Event.setDefaults(self, group=group)
		if group and group.name == "largeScale":
			if TYPE_CHECKING:
				assert isinstance(group, LargeScaleEvent)
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

	def getV4Dict(self) -> dict[str, Any]:
		data = Event.getV4Dict(self)
		data.update(
			{
				"rules": [
					{
						"type": ruleName,
						"value": rule.getServerString(),
					}
					for ruleName, rule in self.rulesDict.items()
				],
			},
		)
		return data
