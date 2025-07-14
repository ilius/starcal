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
from scal3.event_lib.events import DailyNoteEvent
from scal3.event_lib.occur import IntervalOccurSet

log = logger.get()

from typing import TYPE_CHECKING, NamedTuple

from scal3 import ics
from scal3.cal_types import (
	calTypes,
	getSysDate,
	jd_to,
	to_jd,
)
from scal3.date_utils import dateDecode, dateEncode, jwday
from scal3.event_lib.groups import EventGroup
from scal3.locale_man import textNumEncode
from scal3.locale_man import tr as _
from scal3.time_utils import (
	hmDecode,
	hmEncode,
	simpleTimeEncode,
	timeToFloatHour,
)
from scal3.utils import findNearestIndex

from .common import (
	firstWeekDay,
	getAbsWeekNumberFromJd,
	getCurrentJd,
	weekDayName,
)
from .event_base import Event
from .register import classes
from .rules import (
	DateEventRule,
	DayTimeRangeEventRule,
	EndEventRule,
	StartEventRule,
	WeekDayEventRule,
	WeekNumberModeEventRule,
)

if TYPE_CHECKING:
	from collections.abc import Sequence
	from typing import Any

	from scal3.event_lib.pytypes import EventContainerType, EventGroupType, OccurSetType

	from .pytypes import EventType

__all__ = [
	"UniversityClassEvent",
	"UniversityExamEvent",
	"UniversityTerm",
	"WeeklyScheduleItem",
]


class WeeklyScheduleItem(NamedTuple):
	name: str  # Course Name
	weekNumMode: str  # values: "odd", "even", "any"


@classes.group.register
class UniversityTerm(EventGroup):
	name = "universityTerm"
	desc = _("University Term (Semester)")
	acceptsEventTypes: Sequence[str] = (
		"universityClass",
		"universityExam",
	)
	actions = EventGroup.actions + [
		("View Weekly Schedule", "viewWeeklySchedule"),
	]
	sortBys = EventGroup.sortBys + [
		("course", _("Course"), True),
		("time", _("Time"), True),
	]
	sortByDefault = "time"
	params = EventGroup.params + ["courses"]
	paramsOrder = EventGroup.paramsOrder + [
		"classTimeBounds",
		"classesEndDate",
		"courses",
	]
	noCourseError = _(
		"Edit University Term and define some Courses before you add a Class/Exam",
	)

	def getSortByValue(self, event: EventType, attr: str) -> Any:
		if event.name in self.acceptsEventTypes:
			if attr == "course":
				assert isinstance(event, UniversityClassEvent | UniversityExamEvent), (
					f"{event=}"
				)
				return event.courseId
			if attr == "time":
				if event.name == "universityClass":
					assert isinstance(event, UniversityClassEvent), f"{event=}"
					weekDay = WeekDayEventRule.getFrom(event)
					if weekDay is None:
						raise RuntimeError("no weekDay rule")
					wd = weekDay.weekDayList[0]
					dayTimeRange = DayTimeRangeEventRule.getFrom(event)
					if dayTimeRange is None:
						raise RuntimeError("no dayTimeRange rule")
					return (
						(wd - firstWeekDay.v) % 7,
						dayTimeRange.getHourRange(),
					)
				if event.name == "universityExam":
					assert isinstance(event, UniversityExamEvent), f"{event=}"
					date = DateEventRule.getFrom(event)
					if date is None:
						raise RuntimeError("no date rule")
					dayTimeRange = DayTimeRangeEventRule.getFrom(event)
					if dayTimeRange is None:
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

	def getClassBoundsFormatted(self) -> tuple[list[str], list[float]] | None:
		count = len(self.classTimeBounds)
		if count < 2:
			return None
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
	) -> list[list[list[WeeklyScheduleItem]]]:
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
		data: list[list[list[WeeklyScheduleItem]]] = [
			[[] for i in range(boundsCount - 1)] for weekDay in range(7)
		]
		# ---
		if currentWeekOnly:
			currentJd = getCurrentJd()
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
			assert isinstance(event, UniversityClassEvent), f"{event=}"
			assert event.courseId is not None
			weekNumModeRule = WeekNumberModeEventRule.getFrom(event)
			if weekNumModeRule is None:
				raise RuntimeError("no weekNumMode rule")
			weekNumMode: str = weekNumModeRule.getRuleValue()
			if currentWeekNumMode:
				if weekNumMode not in {"any", currentWeekNumMode}:
					continue
				weekNumMode = ""
			elif weekNumMode == "any":
				weekNumMode = ""
			# ---
			weekDayRule = WeekDayEventRule.getFrom(event)
			if weekDayRule is None:
				raise RuntimeError("no weekDay rule")
			weekDay = weekDayRule.weekDayList[0]
			dayTimeRangeRule = DayTimeRangeEventRule.getFrom(event)
			if dayTimeRangeRule is None:
				raise RuntimeError("no dayTimeRange rule")
			h0, h1 = dayTimeRangeRule.getHourRange()
			startIndex = findNearestIndex(boundsHour, h0)
			endIndex = findNearestIndex(boundsHour, h1)
			assert startIndex is not None
			assert endIndex is not None
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
		jd = getCurrentJd()
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
			assert isinstance(other, UniversityTerm), f"{other=}"
			self.classesEndDate = other.classesEndDate[:]
			self.classTimeBounds = other.classTimeBounds[:]

	def getDict(self) -> dict[str, Any]:
		data = EventGroup.getDict(self)
		data.update(
			{
				"classTimeBounds": [hmEncode(hm) for hm in self.classTimeBounds],
				"classesEndDate": dateEncode(self.classesEndDate),
			},
		)
		return data

	def setDict(self, data: dict[str, Any]) -> None:
		EventGroup.setDict(self, data)
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
		parent: EventContainerType | None = None,
	) -> None:
		# assert parent is not None
		Event.__init__(self, ident, parent)
		self.courseId: int | None = None  # FIXME

	def setDefaults(
		self,
		group: EventGroupType | None = None,
	) -> None:
		Event.setDefaults(self, group=group)
		if group and group.name == "universityTerm":
			if TYPE_CHECKING:
				assert isinstance(group, UniversityTerm), f"{group=}"
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
		# assert self.parent is not None
		assert isinstance(self.parent, UniversityTerm), f"{self.parent=}"
		assert self.courseId is not None
		return self.parent.getCourseNameById(self.courseId)

	def getWeekDayName(self) -> str:
		rule = WeekDayEventRule.getFrom(self)
		if rule is None:
			raise RuntimeError("no weekDay rule")
		return weekDayName[rule.weekDayList[0]]

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
		parent: EventContainerType | None = None,
	) -> None:
		# assert group is not None  # FIXME
		DailyNoteEvent.__init__(self, ident, parent)
		self.courseId: int | None = None  # FIXME

	def setDefaults(self, group: EventGroupType | None = None) -> None:
		DailyNoteEvent.setDefaults(self, group=group)
		dayTimeRange = DayTimeRangeEventRule.getFrom(self)
		if dayTimeRange is None:
			raise RuntimeError("no dayTimeRange rule")
		dayTimeRange.setRange((9, 0, 0), (11, 0, 0))  # FIXME
		if group and group.name == "universityTerm":
			self.setJd(group.endJd)  # FIXME

	def getCourseName(self) -> str:
		# assert self.parent is not None
		assert isinstance(self.parent, UniversityTerm), f"{self.parent=}"
		assert self.courseId is not None
		return self.parent.getCourseNameById(self.courseId)

	def updateSummary(self) -> None:
		self.summary = _("{courseName} Exam").format(
			courseName=self.getCourseName(),
		)

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSetType:
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
