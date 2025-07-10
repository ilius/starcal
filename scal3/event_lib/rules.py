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

from scal3 import locale_man, logger

from .pytypes import EventRuleType

log = logger.get()

import json
from time import localtime
from typing import TYPE_CHECKING, Self

from scal3.cal_types import (
	convert,
	getSysDate,
	jd_to,
	to_jd,
)
from scal3.core import (
	firstWeekDay,
	getAbsWeekNumberFromJd,
	weekDayName,
)
from scal3.date_utils import (
	checkDate,
	dateDecode,
	dateEncode,
	jwday,
)
from scal3.filesystem import null_fs
from scal3.interval_utils import simplifyNumList
from scal3.locale_man import floatEncode, textNumEncode
from scal3.locale_man import tr as _
from scal3.s_object import SObjBase
from scal3.time_utils import (
	durationDecode,
	durationEncode,
	getEpochFromJd,
	getSecondsFromHms,
	timeDecode,
	timeEncode,
	timeToFloatHour,
)
from scal3.utils import numRangesEncode, s_join

from .common import weekDayNameEnglish
from .exceptions import BadEventFile
from .occur import IntervalOccurSet, JdOccurSet, OccurSet, TimeListOccurSet
from .register import classes

if TYPE_CHECKING:
	from collections.abc import Sequence
	from typing import Any

	from .pytypes import EventType, RuleContainerType

	# _ruleDymmy: EventRuleType = EventRule(Event())


__all__ = [
	"CycleLenEventRule",
	"CycleWeeksEventRule",
	"DateAndTimeEventRule",
	"DateEventRule",
	"DayOfMonthEventRule",
	"DayTimeEventRule",
	"DayTimeRangeEventRule",
	"DurationEventRule",
	"EndEventRule",
	"EventRule",
	"ExDatesEventRule",
	"MonthEventRule",
	"StartEventRule",
	"WeekDayEventRule",
	"WeekMonthEventRule",
	"WeekNumberModeEventRule",
	"YearEventRule",
]
dayLen = 86400

# def checkTypes() -> None:
# 	rule: EventRuleType = WeekNumberModeEventRule(Event())  # OK
# 	ruleCls: type[EventRuleType] = WeekNumberModeEventRule  # OK


# Should not be registered, or instantiate directly
@classes.rule.setMain
class EventRule(SObjBase, EventRuleType):
	name = ""
	tname = ""
	nameAlias = ""
	desc = ""
	provide: Sequence[str] = ()
	need: Sequence[str] = ()
	conflict: Sequence[str] = ()
	sgroup = -1
	expand = False
	params: list[str] = []
	WidgetClass: Any

	def getServerString(self) -> str:
		raise NotImplementedError

	def __bool__(self) -> bool:
		return True

	def __init__(self, parent: RuleContainerType) -> None:
		"""Parent can be an event for now (maybe later a group too)."""
		self.parent = parent
		self.fs = null_fs

	def getRuleValue(self) -> Any:
		log.warning(f"No implementation for {self.__class__.__name__}.getRuleValue")
		return None

	def setRuleValue(self, data: Any) -> None:  # noqa: ARG002
		log.warning(f"No implementation for {self.__class__.__name__}.setRuleValue")

	def copy(self) -> Self:
		newObj = self.__class__(self.parent)
		newObj.fs = getattr(self, "fs", None)  # type: ignore[assignment]
		newObj.copyFrom(self)
		return newObj

	def getCalType(self) -> int:
		return self.parent.calType

	def changeCalType(self, calType: int) -> bool:  # noqa: ARG002, PLR6301
		return True

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,
	) -> OccurSet:
		raise NotImplementedError

	def getInfo(self) -> str:
		return self.desc + f": {self}"

	def getEpochFromJd(self, jd: int) -> int:
		return getEpochFromJd(
			jd,
			tz=self.parent.getTimeZoneObj(),
		)

	def getEpoch(self) -> int:
		raise NotImplementedError

	def getJd(self) -> int:
		raise NotImplementedError

	@classmethod
	def getFrom(cls, container: RuleContainerType) -> Self | None:
		return container.rulesDict.get(cls.name)  # type: ignore[return-value]

	@classmethod
	def addOrGetFrom(cls, container: RuleContainerType) -> Self:
		return container.getAddRule(cls.name)  # type: ignore[return-value]


class AllDayEventRule(EventRule):
	def jdMatches(self, jd: int) -> bool:  # noqa: ARG002, PLR6301
		return True

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,  # noqa: ARG002
	) -> OccurSet:
		# improve performance FIXME
		jds = set()
		for jd in range(startJd, endJd):
			if self.jdMatches(jd):
				jds.add(jd)  # benchmark FIXME
		return JdOccurSet(jds)


# Should not be registered, or instantiate directly
class MultiValueAllDayEventRule(AllDayEventRule):
	conflict: Sequence[str] = ("date",)
	params = ["values"]
	expand = True  # FIXME

	def __init__(self, parent: RuleContainerType) -> None:
		EventRule.__init__(self, parent)
		self.values: list[int | tuple[int, int]] = []

	def getRuleValue(self) -> Any:
		return self.values

	def setRuleValue(self, data: Any) -> None:
		if not isinstance(data, tuple | list):
			data = [data]
		self.values = data

	def __str__(self) -> str:
		return textNumEncode(numRangesEncode(self.values, ", "))

	def hasValue(self, value: Any) -> bool:
		for item in self.values:
			if isinstance(item, tuple | list):
				if item[0] <= value <= item[1]:
					return True
			elif item == value:
				return True
		return False

	def getValuesPlain(self) -> list[int | tuple[int, int]]:
		ls: list[int | tuple[int, int]] = []
		for item in self.values:
			if isinstance(item, tuple | list):
				ls += list(range(item[0], item[1] + 1))
			else:
				ls.append(item)
		return ls

	def setValuesPlain(self, values: list[int]) -> None:
		self.values = simplifyNumList(values)

	def changeCalType(self, _calType: int) -> bool:  # noqa: PLR6301
		return False


@classes.rule.register
class YearEventRule(MultiValueAllDayEventRule):
	name = "year"
	desc = _("Year")
	params = ["values"]

	def getServerString(self) -> str:
		return numRangesEncode(self.values, " ")  # no comma

	def __init__(self, parent: RuleContainerType) -> None:
		MultiValueAllDayEventRule.__init__(self, parent)
		self.values = [getSysDate(self.getCalType())[0]]

	def jdMatches(self, jd: int) -> bool:
		return self.hasValue(jd_to(jd, self.getCalType())[0])

	def newCalTypeValues(
		self,
		newCalType: int,
	) -> list[int | tuple[int, int]]:
		def yearConv(year: int) -> int:
			return convert(year, 7, 1, curCalType, newCalType)[0]

		curCalType = self.getCalType()
		values2: list[int | tuple[int, int]] = []
		for item in self.values:
			if isinstance(item, tuple | list):
				values2.append(
					(
						yearConv(item[0]),
						yearConv(item[1]),
					),
				)
			else:
				values2.append(yearConv(item))
		return values2

	def changeCalType(self, calType: int) -> bool:
		self.values = self.newCalTypeValues(calType)
		return True


# FIXME: directly inherit from AllDayEventRule
@classes.rule.register
class MonthEventRule(MultiValueAllDayEventRule):
	name = "month"
	desc = _("Month")
	conflict: Sequence[str] = (
		"date",
		"weekMonth",
	)
	params = ["values"]

	def getServerString(self) -> str:
		# return numRangesEncode(self.values, " ")  # no comma
		return " ".join(str(n) for n in self.values)

	def __init__(self, parent: RuleContainerType) -> None:
		MultiValueAllDayEventRule.__init__(self, parent)
		self.values: list[int] = [1]  # type: ignore[assignment]

	def jdMatches(self, jd: int) -> bool:
		return self.hasValue(jd_to(jd, self.getCalType())[1])


@classes.rule.register
class DayOfMonthEventRule(MultiValueAllDayEventRule):
	name = "day"
	desc = _("Day of Month")
	params = ["values"]

	def getServerString(self) -> str:
		return numRangesEncode(self.values, " ")  # no comma

	def __init__(self, parent: RuleContainerType) -> None:
		MultiValueAllDayEventRule.__init__(self, parent)
		self.values = [1]

	def jdMatches(self, jd: int) -> bool:
		return self.hasValue(jd_to(jd, self.getCalType())[2])


@classes.rule.register
class WeekNumberModeEventRule(EventRule):
	name = "weekNumMode"
	desc = _("Week Number")
	need: Sequence[str] = ("start",)  # FIXME
	conflict: Sequence[str] = (
		"date",
		"weekMonth",
	)
	params = ["weekNumMode"]
	EVERY_WEEK, ODD_WEEKS, EVEN_WEEKS = list(range(3))
	# remove EVERY_WEEK? FIXME
	weekNumModeNames = ("any", "odd", "even")

	def getServerString(self) -> str:
		return self.weekNumModeNames[self.weekNumMode]

	def __init__(self, parent: RuleContainerType) -> None:
		EventRule.__init__(self, parent)
		self.weekNumMode = self.EVERY_WEEK

	def getRuleValue(self) -> Any:
		return self.weekNumModeNames[self.weekNumMode]

	def setRuleValue(self, wnModeName: str) -> None:
		if wnModeName not in self.weekNumModeNames:
			raise BadEventFile(
				f"bad rule value {wnModeName=}, "
				"the value for weekNumMode must be "
				f"one of {self.weekNumModeNames!r}",
			)
		self.weekNumMode = self.weekNumModeNames.index(wnModeName)

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,
	) -> OccurSet:
		# improve performance FIXME
		startAbsWeekNum = getAbsWeekNumberFromJd(event.getStartJd()) - 1
		# 1st week # FIXME
		if self.weekNumMode == self.EVERY_WEEK:
			return JdOccurSet(
				set(range(startJd, endJd)),
			)
		if self.weekNumMode == self.ODD_WEEKS:
			return JdOccurSet(
				{
					jd
					for jd in range(startJd, endJd)
					if (getAbsWeekNumberFromJd(jd) - startAbsWeekNum) % 2 == 1
				},
			)
		if self.weekNumMode == self.EVEN_WEEKS:
			return JdOccurSet(
				{
					jd
					for jd in range(startJd, endJd)
					if (getAbsWeekNumberFromJd(jd) - startAbsWeekNum) % 2 == 0
				},
			)
		log.error(f"calcOccurrence: invalid weekNumMode={self.weekNumMode}")
		return JdOccurSet()

	def __str__(self) -> str:
		return self.weekNumModeNames[self.weekNumMode]

	def getInfo(self) -> str:
		if self.weekNumMode == self.EVERY_WEEK:
			return ""
		if self.weekNumMode == self.ODD_WEEKS:
			return _("Odd Weeks")
		if self.weekNumMode == self.EVEN_WEEKS:
			return _("Even Weeks")
		log.error(f"getInfo: invalid weekNumMode={self.weekNumMode}")
		return ""


@classes.rule.register
class WeekDayEventRule(AllDayEventRule):
	name = "weekDay"
	desc = _("Day of Week")
	conflict: Sequence[str] = (
		"date",
		"weekMonth",
	)
	params = ["weekDayList"]

	def getServerString(self) -> str:
		return s_join(self.weekDayList)

	def __init__(self, parent: RuleContainerType) -> None:
		EventRule.__init__(self, parent)
		self.weekDayList = list(range(7))  # or [] FIXME

	def getRuleValue(self) -> Any:
		return self.weekDayList

	def setRuleValue(self, data: int | list[int]) -> None:
		if isinstance(data, int):
			self.weekDayList = [data]
		elif isinstance(data, tuple | list):
			self.weekDayList = data
		else:
			raise BadEventFile(
				f"bad rule weekDayList={data}, "
				"value for weekDayList must be a list of integers"
				" (0 for sunday)",
			)

	def jdMatches(self, jd: int) -> bool:
		return jwday(jd) in self.weekDayList

	def __str__(self) -> str:
		if self.weekDayList == list(range(7)):
			return ""
		return ", ".join([weekDayNameEnglish[wd] for wd in self.weekDayList])

	def getInfo(self) -> str:
		if self.weekDayList == list(range(7)):
			return ""
		sep = _(",") + " "
		sep2 = " " + _("or") + " "
		return (
			_("Day of Week")
			+ ": "
			+ sep.join([weekDayName[wd] for wd in self.weekDayList[:-1]])
			+ sep2
			+ weekDayName[self.weekDayList[-1]]
		)


@classes.rule.register
class WeekMonthEventRule(EventRule):
	name = "weekMonth"
	desc = _("Week-Month")
	conflict: Sequence[str] = (
		"date",
		"month",
		"ex_month",
		"weekNumMode",
		"weekday",
		"cycleDays",
		"cycleWeeks",
		"cycleLen",
	)
	params = [
		"month",  # 0..12   0 means every month
		"wmIndex",  # 0..4
		"weekDay",  # 0..6
	]
	"""
	paramsValidators = {
		"month": lambda m: 0 <= m <= 12,
		"wmIndex": lambda m: 0 <= m <= 4,
		"weekDay": lambda m: 0 <= m <= 6,
	}
	"""
	wmIndexNamesEn = (
		"First",  # 0
		"Second",  # 1
		"Third",  # 2
		"Fourth",  # 3
		"Last",  # 4
	)
	wmIndexNames = (
		_("First"),  # 0
		_("Second"),  # 1
		_("Third"),  # 2
		_("Fourth"),  # 3
		_("Last"),  # 4
	)

	def __str__(self) -> str:
		calType = self.getCalType()
		if self.month == 0:
			monthDesc = "every month"
		else:
			monthDesc = locale_man.getMonthName(calType, self.month)
		return " ".join(
			[
				self.wmIndexNamesEn[self.wmIndex],
				weekDayNameEnglish[self.weekDay],
				"of",
				monthDesc,
			],
		)

	def __init__(self, parent: RuleContainerType) -> None:
		EventRule.__init__(self, parent)
		self.month = 1
		self.wmIndex = 4
		self.weekDay = firstWeekDay.v

	def getRuleValue(self) -> Any:
		return {
			"month": self.month,
			"wmIndex": self.wmIndex,
			"weekDay": self.weekDay,
		}

	def setRuleValue(self, data: Any) -> None:
		assert isinstance(data, dict), f"{data=}"
		self.month = data["month"]
		self.wmIndex = data["wmIndex"]
		self.weekDay = data["weekDay"]

	def getServerString(self) -> str:
		return json.dumps(
			{
				"weekIndex": self.wmIndex,
				"weekDay": self.weekDay,
				"month": self.month,
			},
		)

	# usefull? FIXME
	# def setJd(self, jd) -> None:
	# 	self.month, self.wmIndex, self.weekDay = getMonthWeekNth(
	# 	jd,
	# 	self.getCalType(),
	# )

	# def getJd(self) -> int:

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,  # noqa: ARG002
	) -> OccurSet:
		calType = self.getCalType()
		startYear, _startMonth, _startDay = jd_to(startJd, calType)
		endYear, _endMonth, _endDay = jd_to(endJd, calType)
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
				# Last (Fouth or Fifth)
				if self.wmIndex == 4 and jd_to(jd, calType)[1] != month:
					jd -= 7
				if startJd <= jd < endJd:
					jds.add(jd)
		return JdOccurSet(jds)


@classes.rule.register
class DateEventRule(EventRule):
	name = "date"
	desc = _("Date")
	need: Sequence[str] = ()
	conflict: Sequence[str] = (
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

	def __init__(self, parent: RuleContainerType) -> None:
		EventRule.__init__(self, parent)
		self.date = getSysDate(self.getCalType())

	def getRuleValue(self) -> Any:
		return str(self)

	def setRuleValue(self, data: str) -> None:
		try:
			self.date = dateDecode(data)
		except ValueError:
			log.exception("")

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
		event: EventType,  # noqa: ARG002
	) -> OccurSet:
		myJd = self.getJd()
		if startJd <= myJd < endJd:
			return JdOccurSet({myJd})
		return JdOccurSet()

	def changeCalType(self, calType: int) -> bool:
		self.date = jd_to(self.getJd(), calType)
		return True


class DateAndTimeEventRule(DateEventRule):
	sgroup = 1
	params = [
		"date",
		"time",
	]

	def getServerString(self) -> str:
		y, m, d = self.date
		H, M, S = self.time
		return f"{y:04d}/{m:02d}/{d:02d} {H:02d}:{M:02d}:{S:02d}"

	def __init__(self, parent: RuleContainerType) -> None:
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
		jd, hms = self.parent.getJhmsFromEpoch(epoch)
		self.setJd(jd)
		self.time = hms.tuple()

	def setJdExact(self, jd: int) -> None:
		self.setJd(jd)
		self.time = (0, 0, 0)

	def setDate(self, date: tuple[int, int, int]) -> None:
		if len(date) != 3:
			raise ValueError(f"DateAndTimeEventRule.setDate: bad {date = }")
		self.date = date
		self.time = (0, 0, 0)

	def getDate(self, calType: int) -> tuple[int, int, int]:
		return convert(
			self.date[0],
			self.date[1],
			self.date[2],
			self.getCalType(),
			calType,
		)

	def getRuleValue(self) -> Any:
		return {
			"date": dateEncode(self.date),
			"time": timeEncode(self.time),
		}

	def setRuleValue(self, arg: dict[str, str] | str) -> None:
		if isinstance(arg, dict):
			try:
				self.date = dateDecode(arg["date"])
			except ValueError:
				log.exception("")
			if "time" in arg:
				try:
					self.time = timeDecode(arg["time"])
				except ValueError as e:
					raise BadEventFile(str(e)) from e
		elif isinstance(arg, str):
			try:
				self.date = dateDecode(arg)
			except ValueError as e:
				raise BadEventFile(str(e)) from e
		else:
			raise BadEventFile(f"bad rule {self.name}={arg!r}")

	def getInfo(self) -> str:
		return (
			self.desc
			+ ": "
			+ dateEncode(self.date)
			+ _(",")
			+ " "
			+ _("Time")
			+ ": "
			+ timeEncode(self.time)
		)


@classes.rule.register
class DayTimeEventRule(EventRule):  # Moment Event
	name = "dayTime"
	desc = _("Time in Day")
	provide = ("time",)
	conflict: Sequence[str] = (
		"dayTimeRange",
		"cycleLen",
	)
	params = ["dayTime"]

	def getServerString(self) -> str:
		H, M, S = self.dayTime
		return f"{H:02d}:{M:02d}:{S:02d}"

	def __str__(self) -> str:
		H, M, S = self.dayTime
		return f"{H:02d}:{M:02d}:{S:02d}"

	def __init__(self, parent: RuleContainerType) -> None:
		EventRule.__init__(self, parent)
		self.dayTime = localtime()[3:6]

	def getRuleValue(self) -> Any:
		return timeEncode(self.dayTime)

	def setRuleValue(self, data: str) -> None:
		try:
			self.dayTime = timeDecode(data)
		except ValueError:
			log.exception("")

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,  # noqa: ARG002
	) -> OccurSet:
		mySec = getSecondsFromHms(*self.dayTime)
		return TimeListOccurSet.fromRange(  # FIXME
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
	conflict: Sequence[str] = (
		"dayTime",
		"cycleLen",
	)
	params = [
		"dayTimeStart",
		"dayTimeEnd",
	]

	def __str__(self) -> str:
		H1, M1, S1 = self.dayTimeStart
		H2, M2, S2 = self.dayTimeEnd
		return f"{H1:02d}:{M1:02d}:{S1:02d} - {H2:02d}:{M2:02d}:{S2:02d}"

	def getServerString(self) -> str:
		H1, M1, S1 = self.dayTimeStart
		H2, M2, S2 = self.dayTimeEnd
		return f"{H1:02d}:{M1:02d}:{S1:02d} {H2:02d}:{M2:02d}:{S2:02d}"

	def __init__(self, parent: RuleContainerType) -> None:
		EventRule.__init__(self, parent)
		self.dayTimeStart = (0, 0, 0)
		self.dayTimeEnd = (24, 0, 0)

	def setRange(
		self,
		start: tuple[int, int, int],
		end: tuple[int, int, int],
	) -> None:
		self.dayTimeStart = start
		self.dayTimeEnd = end

	def getHourRange(self) -> tuple[float, float]:
		return (
			timeToFloatHour(*self.dayTimeStart),
			timeToFloatHour(*self.dayTimeEnd),
		)

	def getSecondsRange(self) -> tuple[int, int]:
		return (
			getSecondsFromHms(*self.dayTimeStart),
			getSecondsFromHms(*self.dayTimeEnd),
		)

	def getRuleValue(self) -> Any:
		return (timeEncode(self.dayTimeStart), timeEncode(self.dayTimeEnd))

	def setRuleValue(self, data: tuple[str, str]) -> None:
		try:
			self.setRange(timeDecode(data[0]), timeDecode(data[1]))
		except ValueError:
			log.exception("")

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,  # noqa: ARG002
	) -> OccurSet:
		daySecStart = getSecondsFromHms(*self.dayTimeStart)
		daySecEnd = getSecondsFromHms(*self.dayTimeEnd)
		daySecEnd = max(daySecStart, daySecEnd)
		tmList = []
		for jd in range(startJd, endJd):
			epoch = self.getEpochFromJd(jd)
			tmList.append(
				(
					epoch + daySecStart,
					epoch + daySecEnd,
				),
			)
		return IntervalOccurSet(tmList)


@classes.rule.register
class StartEventRule(DateAndTimeEventRule):
	name = "start"
	desc = _("Start")
	conflict: Sequence[str] = ("date",)

	# def getServerString(self) -> str: # in DateAndTimeEventRule

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,  # noqa: ARG002
	) -> OccurSet:
		return IntervalOccurSet.newFromStartEnd(
			max(self.getEpochFromJd(startJd), self.getEpoch()),
			self.getEpochFromJd(endJd),
		)


@classes.rule.register
class EndEventRule(DateAndTimeEventRule):
	name = "end"
	desc = _("End")
	conflict: Sequence[str] = (
		"date",
		"duration",
	)

	# def getServerString(self) -> str: # in DateAndTimeEventRule

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,  # noqa: ARG002
	) -> OccurSet:
		return IntervalOccurSet.newFromStartEnd(
			self.getEpochFromJd(startJd),
			min(self.getEpochFromJd(endJd), self.getEpoch()),
		)


@classes.rule.register
class DurationEventRule(EventRule):
	name = "duration"
	desc = _("Duration")
	need: Sequence[str] = ("start",)
	conflict: Sequence[str] = (
		"date",
		"end",
	)
	params = [
		"value",
		"unit",
	]
	sgroup = 1
	units = (1, 60, 3600, dayLen, 7 * dayLen)

	def __str__(self) -> str:
		return f"{self.value} {self.getUnitDesc()}"

	def getInfo(self) -> str:
		return (
			self.desc
			+ ": "
			+ _(
				"{count} " + self.getUnitDesc(),
			).format(count=floatEncode(str(self.value)))
		)

	def getUnitDesc(self) -> str:
		return {
			1: "seconds",
			60: "minutes",
			3600: "hours",
			86400: "days",
			604800: "weeks",
		}[self.unit]

	def getServerString(self) -> str:
		return str(self.value) + " " + self.getUnitSymbol()

	def getUnitSymbol(self) -> str:
		return {
			1: "s",
			60: "m",
			3600: "h",
			86400: "d",
			604800: "w",
		}[self.unit]

	def __init__(self, parent: RuleContainerType) -> None:
		EventRule.__init__(self, parent)
		self.value: float = 0
		self.unit: int = 1  # seconds

	def getSeconds(self) -> int:
		return int(self.value * self.unit)

	def setSeconds(self, s: int) -> None:
		assert isinstance(s, int), f"{s=}"
		for unit in reversed(self.units):
			if s % unit == 0:
				self.value, self.unit = s // unit, unit
				return
		self.unit, self.value = s, 1

	def setRuleValue(self, data: str) -> None:
		try:
			self.value, self.unit = durationDecode(data)
		except Exception as e:
			log.error(
				f'Error while loading event rule "{self.name}": {e}',
			)

	def getRuleValue(self) -> Any:
		return durationEncode(self.value, self.unit)

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,  # noqa: ARG002
	) -> OccurSet:
		parentStart = self.parent["start"]
		if parentStart is None:
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
	event: EventType,
) -> OccurSet:
	eStartJd = event.getStartJd()
	if startJd <= eStartJd:
		startJd = eStartJd
	else:
		startJd = eStartJd + ((startJd - eStartJd - 1) // days + 1) * days
	return JdOccurSet(
		set(
			range(
				startJd,
				endJd,
				days,
			),
		),
	)


@classes.rule.register
class CycleDaysEventRule(EventRule):
	name = "cycleDays"
	desc = _("Cycle (Days)")
	need: Sequence[str] = ("start",)
	conflict: Sequence[str] = (
		"date",
		"cycleWeeks",
		"cycleLen",
		"weekMonth",
	)
	params = ["days"]

	def getServerString(self) -> str:
		return str(self.days)

	def __str__(self) -> str:
		return str(self.days)

	def __init__(self, parent: RuleContainerType) -> None:
		EventRule.__init__(self, parent)
		self.days = 7

	def getRuleValue(self) -> Any:
		return self.days

	def setRuleValue(self, days: int) -> None:
		self.days = days

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,
	) -> OccurSet:
		return cycleDaysCalcOccurrence(self.days, startJd, endJd, event)

	def getInfo(self) -> str:
		return _("Repeat: Every {days} Days").format(days=_(self.days))


@classes.rule.register
class CycleWeeksEventRule(EventRule):
	name = "cycleWeeks"
	desc = _("Cycle (Weeks)")
	need: Sequence[str] = ("start",)
	conflict: Sequence[str] = (
		"date",
		"cycleDays",
		"cycleLen",
		"weekMonth",
	)
	params = ["weeks"]

	def getServerString(self) -> str:
		return str(self.weeks)

	def __str__(self) -> str:
		return str(self.weeks)

	def __init__(self, parent: RuleContainerType) -> None:
		EventRule.__init__(self, parent)
		self.weeks = 1

	def getRuleValue(self) -> Any:
		return self.weeks

	def setRuleValue(self, weeks: int) -> None:
		self.weeks = weeks

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,
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
	provide = ("time",)
	need: Sequence[str] = ("start",)
	conflict: Sequence[str] = (
		"date",
		"dayTime",
		"dayTimeRange",
		"cycleDays",
		"cycleWeeks",
		"weekMonth",
	)
	params = [
		"days",
		"extraTime",
	]

	def getServerString(self) -> str:
		H, M, S = self.extraTime
		return f"{self.days} {H:02d}:{M:02d}:{S:02d}"

	def __str__(self) -> str:
		H, M, S = self.extraTime
		return f"{self.days} days, {H:02d}:{M:02d}:{S:02d}"

	def __init__(self, parent: RuleContainerType) -> None:
		EventRule.__init__(self, parent)
		self.days = 7
		self.extraTime = (0, 0, 0)

	def getRuleValue(self) -> Any:
		return {
			"days": self.days,
			"extraTime": timeEncode(self.extraTime),
		}

	def setRuleValue(self, arg: dict[str, Any]) -> None:
		self.days = arg["days"]
		try:
			self.extraTime = timeDecode(arg["extraTime"])
		except ValueError:
			log.exception("")

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,
	) -> OccurSet:
		startEpoch = self.getEpochFromJd(startJd)
		eventStartEpoch = event.getStartEpoch()
		# --
		cycleSec = self.days * dayLen + getSecondsFromHms(*self.extraTime)
		# --
		if startEpoch <= eventStartEpoch:
			startEpoch = eventStartEpoch
		else:
			startEpoch = eventStartEpoch + cycleSec * (
				(startEpoch - eventStartEpoch - 1) // cycleSec + 1
			)
		# --
		return TimeListOccurSet.fromRange(
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
	conflict: Sequence[str] = (
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
	# conflict: Sequence[str] =("date",)  # FIXME
	params = ["dates"]

	def getServerString(self) -> str:
		return " ".join(f"{y:04d}/{m:02d}/{d:02d}" for y, m, d in self.dates)

	def __str__(self) -> str:
		return " ".join(f"{y:04d}/{m:02d}/{d:02d}" for y, m, d in self.dates)

	def __init__(self, parent: RuleContainerType) -> None:
		EventRule.__init__(self, parent)
		self.setDates([])

	def setDates(self, dates: list[tuple[int, int, int]]) -> None:
		self.dates = dates
		self.jdList = [to_jd(y, m, d, self.getCalType()) for y, m, d in dates]

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,  # noqa: ARG002
	) -> OccurSet:
		# improve performance # FIXME
		return JdOccurSet(
			set(range(startJd, endJd)).difference(self.jdList),
		)

	def getRuleValue(self) -> Any:
		return [dateEncode(date) for date in self.dates]

	def setRuleValue(
		self,
		datesConf: str | list[str | tuple[int, int, int] | list[int]],
	) -> None:
		dates: list[tuple[int, int, int]] = []
		try:
			if isinstance(datesConf, str):
				dates = [dateDecode(date.strip()) for date in datesConf.split(",")]
			else:
				for date in datesConf:
					if isinstance(date, str):
						dates.append(dateDecode(date))  # noqa: PLW2901
					elif isinstance(date, tuple | list):
						y, m, d = date
						checkDate((y, m, d))
						dates.append((y, m, d))
					else:
						log.error(f"ExDatesEventRule: setRuleValue: invalid {date=}")
			self.setDates(dates)
		except ValueError:
			log.exception("")

	def changeCalType(self, calType: int) -> bool:
		self.dates = [jd_to(jd, calType) for jd in self.jdList]
		return True
