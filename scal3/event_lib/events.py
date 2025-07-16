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

from scal3 import ics
from scal3.cal_types import (
	GREGORIAN,
	getSysDate,
	jd_to,
	to_jd,
)
from scal3.locale_man import getMonthName
from scal3.locale_man import tr as _
from scal3.utils import iceil, ifloor

from .common import getCurrentJd
from .event_base import Event
from .occur import JdOccurSet
from .register import classes
from .rules import (
	CycleWeeksEventRule,
	DateEventRule,
	DayOfMonthEventRule,
	DayTimeRangeEventRule,
	EndEventRule,
	MonthEventRule,
	StartEventRule,
)

if TYPE_CHECKING:
	from typing import Any

	from scal3.event_lib.pytypes import EventGroupType, OccurSetType

	from .groups import YearlyGroup

__all__ = [
	"DailyNoteEvent",
	"Event",
	"WeeklyEvent",
	"YearlyEvent",
]


dayLen = 86400
icsMinStartYear = 1970
# icsMaxEndYear = 2050


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

	def setDefaults(self, group: EventGroupType | None = None) -> None:
		super().setDefaults(group=group)
		self.setDate(*getSysDate(self.calType))

	# startJd and endJd can be float jd
	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSetType:
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

	def setDefaults(self, group: EventGroupType | None = None) -> None:
		super().setDefaults(group=group)
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

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSetType:
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
		super().setDict(data)
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
			startJd = getCurrentJd()
		else:
			startJd = self.parent.startJd
		return jd_to(startJd, self.calType)[0]

	def getSummary(self) -> str:
		summary = Event.getSummary(self)
		if self.parent and self.parent.name == "yearly":
			if TYPE_CHECKING:
				assert isinstance(self.parent, YearlyGroup), f"{self.parent=}"
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

	def setDefaults(self, group: EventGroupType | None = None) -> None:
		super().setDefaults(group=group)
		jd = getCurrentJd()
		start = StartEventRule.getFrom(self)
		if start is None:
			raise RuntimeError("no start rule")
		end = EndEventRule.getFrom(self)
		if end is None:
			raise RuntimeError("no end rule")
		start.setJd(jd)
		end.setJd(jd + 8)


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
