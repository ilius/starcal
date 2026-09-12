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
from scal3.cal_types import GREGORIAN, jd_to
from scal3.date_utils import jwday
from scal3.locale_man import tr as _

from .common import getCurrentJd
from .event_base import Event
from .register import classes
from .rules import (
	DayTimeRangeEventRule,
	EndEventRule,
	StartEventRule,
	WeekDayEventRule,
	WeekMonthEventRule,
)

if TYPE_CHECKING:
	from typing import Any

	from scal3.event_lib.pytypes import EventGroupType

__all__ = ["MonthlyWeekdayEvent", "WeeklyWeekdayEvent"]


class _WeekdayEventBase(Event):
	"""Shared date-range and time-range handling for weekday-pattern events."""

	def _getV4PatternData(self) -> dict[str, Any]:
		raise NotImplementedError

	def _setDefaultPattern(self, jd: int) -> None:
		raise NotImplementedError

	def _getRrule(self, until: str) -> str:
		raise NotImplementedError

	def _parseRrule(self, rrule: dict[str, str]) -> bool:
		raise NotImplementedError

	def getV4Dict(self) -> dict[str, Any]:
		"""Return v4 format dictionary representation."""
		data = Event.getV4Dict(self)
		start = StartEventRule.getFrom(self)
		if start is None:
			raise RuntimeError("no start rule")
		end = EndEventRule.getFrom(self)
		if end is None:
			raise RuntimeError("no end rule")
		dayTimeRange = DayTimeRangeEventRule.getFrom(self)
		if dayTimeRange is None:
			raise RuntimeError("no dayTimeRange rule")
		startSec, endSec = dayTimeRange.getSecondsRange()
		data.update(
			{
				"startJd": start.getJd(),
				"endJd": end.getJd(),
				"dayStartSeconds": startSec,
				"dayEndSeconds": endSec,
			},
		)
		data.update(self._getV4PatternData())
		return data

	def setDefaults(self, group: EventGroupType | None = None) -> None:
		"""Set default range and time to today and the next 60 days."""
		super().setDefaults(group=group)
		jd = getCurrentJd()
		start = StartEventRule.getFrom(self)
		if start is None:
			raise RuntimeError("no start rule")
		end = EndEventRule.getFrom(self)
		if end is None:
			raise RuntimeError("no end rule")
		start.setJd(jd)
		# 60 days -> a couple of occurrences. Just a default for user input.
		end.setJd(jd + 60)
		dayTimeRange = DayTimeRangeEventRule.getFrom(self)
		if dayTimeRange is None:
			raise RuntimeError("no dayTimeRange rule")
		dayTimeRange.setRange((9, 0, 0), (17, 0, 0))
		self._setDefaultPattern(jd)

	def getIcsData(self, prettyDateTime: bool = False) -> list[tuple[str, str]] | None:
		"""Return iCalendar data with a weekly or monthly weekday recurrence."""
		if self.calType != GREGORIAN:
			return None
		start = StartEventRule.getFrom(self)
		if start is None:
			raise RuntimeError("no start rule")
		end = EndEventRule.getFrom(self)
		if end is None:
			raise RuntimeError("no end rule")
		startJd = start.getJd()
		endJd = end.getJd()
		# Starcal's end date is exclusive; ICS UNTIL includes its date.
		rrule = self._getRrule(ics.getIcsDateByJd(endJd - 1, prettyDateTime))
		occur = self.calcEventOccurrenceIn(startJd, endJd)
		tRangeList = occur.getTimeRangeList()
		if not tRangeList:
			return None
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
			("RRULE", rrule),
			("TRANSP", "OPAQUE"),
			("CATEGORIES", self.name),  # FIXME
		]

	def setIcsData(self, data: dict[str, str]) -> bool:
		"""Import event data from an iCalendar dictionary."""
		try:
			rrule = dict(ics.splitIcsValue(data.get("RRULE", "")))
		except ValueError:
			return False
		if not self._parseRrule(rrule):
			return False
		untilValue = rrule.get("UNTIL")
		if untilValue:
			try:
				untilDate = untilValue.split("T", 1)[0].replace("-", "")
				if len(untilDate) != 8:
					return False
				untilJd = ics.getJdByIcsDate(untilDate)
			except ValueError:
				return False
		else:
			untilJd = None
		try:
			startEpoch = ics.getEpochByIcsTime(data["DTSTART"])
		except (KeyError, ValueError):
			return False
		try:
			endEpoch = ics.getEpochByIcsTime(data["DTEND"])
		except (KeyError, ValueError):
			endEpoch = None
		self.calType = GREGORIAN
		startJd, startHms = self.getJhmsFromEpoch(startEpoch)
		start = StartEventRule.addOrGetFrom(self)
		start.date = jd_to(startJd, GREGORIAN)
		start.time = startHms.tuple()
		end = EndEventRule.addOrGetFrom(self)
		if untilJd is not None:
			# Starcal's end date is an exclusive boundary; ICS UNTIL is inclusive.
			end.date = jd_to(untilJd + 1, GREGORIAN)
			end.time = (0, 0, 0)
		else:
			end.date = jd_to(startJd + 60, GREGORIAN)
			end.time = (0, 0, 0)
		dayTimeRange = DayTimeRangeEventRule.addOrGetFrom(self)
		dayTimeRange.dayTimeStart = startHms.tuple()
		if endEpoch is not None:
			_, endHms = self.getJhmsFromEpoch(endEpoch)
			dayTimeRange.dayTimeEnd = endHms.tuple()
		else:
			dayTimeRange.dayTimeEnd = (24, 0, 0)
		return True


@classes.event.register
class WeeklyWeekdayEvent(_WeekdayEventBase):
	"""Event recurring weekly on selected days of the week (e.g. every weekday)."""

	name = "weeklyWeekday"
	desc = _("Weekly Weekday Event")
	iconName = ""
	requiredRules = [
		"start",
		"end",
		"dayTimeRange",
		"weekDay",
	]
	supportedRules = requiredRules
	isAllDay = False

	def _getV4PatternData(self) -> dict[str, Any]:
		weekDay = WeekDayEventRule.getFrom(self)
		if weekDay is None:
			raise RuntimeError("no weekDay rule")
		return {"weekDayList": weekDay.getRuleValue()}

	def _setDefaultPattern(self, jd: int) -> None:
		weekDay = WeekDayEventRule.getFrom(self)
		if weekDay is None:
			raise RuntimeError("no weekDay rule")
		weekDay.weekDayList = [jwday(jd)]

	def setWeekDayList(self, weekDayList: list[int]) -> WeekDayEventRule:
		"""Set the selected days of the week."""
		rule = WeekDayEventRule.addOrGetFrom(self)
		rule.setRuleValue(weekDayList)
		return rule

	def _getRrule(self, until: str) -> str:
		weekDay = WeekDayEventRule.getFrom(self)
		if weekDay is None:
			raise RuntimeError("no weekDay rule")
		return (
			"FREQ=WEEKLY;UNTIL="
			+ until
			+ ";BYDAY="
			+ ics.encodeIcsWeekDayList(weekDay.weekDayList)
		)

	def _parseRrule(self, rrule: dict[str, str]) -> bool:
		if rrule.get("FREQ", "") != "WEEKLY":
			return False
		byDay = rrule.get("BYDAY", "")
		if not byDay:
			return False
		if "INTERVAL" in rrule and rrule["INTERVAL"] != "1":
			return False
		weekDayList = []
		for item in byDay.split(","):
			day = item.strip()
			if not day:
				continue
			try:
				weekDayList.append(ics.icsWeekDays.index(day))
			except ValueError:
				return False
		if not weekDayList:
			return False
		self.setWeekDayList(weekDayList)
		return True


@classes.event.register
class MonthlyWeekdayEvent(_WeekdayEventBase):
	"""Event recurring monthly on a specific weekday instance (e.g. second Tuesday)."""

	name = "monthlyWeekday"
	desc = _("Monthly Weekday Event")
	iconName = ""
	requiredRules = [
		"start",
		"end",
		"dayTimeRange",
		"weekMonth",
	]
	supportedRules = requiredRules
	isAllDay = False

	def _getV4PatternData(self) -> dict[str, Any]:
		weekMonth = WeekMonthEventRule.getFrom(self)
		if weekMonth is None:
			raise RuntimeError("no weekMonth rule")
		return {"weekMonth": weekMonth.getRuleValue()}

	def _setDefaultPattern(self, jd: int) -> None:
		weekMonth = WeekMonthEventRule.getFrom(self)
		if weekMonth is None:
			raise RuntimeError("no weekMonth rule")
		weekMonth.month = 0  # every month
		weekMonth.wmIndex = 4  # Last
		weekMonth.weekDay = jwday(jd)

	def setWeekMonthPattern(
		self,
		month: int,
		wmIndex: int,
		weekDay: int,
	) -> WeekMonthEventRule:
		"""Set the weekday instance of the month to recur on."""
		rule = WeekMonthEventRule.addOrGetFrom(self)
		rule.setRuleValue(
			{"month": month, "wmIndex": wmIndex, "weekDay": weekDay},
		)
		return rule

	def _getRrule(self, until: str) -> str:
		weekMonth = WeekMonthEventRule.getFrom(self)
		if weekMonth is None:
			raise RuntimeError("no weekMonth rule")
		icsWeekDay = ics.icsWeekDays[weekMonth.weekDay]
		if weekMonth.wmIndex == 4:
			byDay = "-1" + icsWeekDay  # "Last"
		else:
			byDay = str(weekMonth.wmIndex + 1) + icsWeekDay
		parts = ["FREQ=MONTHLY", "UNTIL=" + until, "BYDAY=" + byDay]
		if weekMonth.month != 0:
			parts.append("BYMONTH=" + str(weekMonth.month))
		return ";".join(parts)

	def _parseRrule(self, rrule: dict[str, str]) -> bool:
		if rrule.get("FREQ", "") != "MONTHLY":
			return False
		if "INTERVAL" in rrule and rrule["INTERVAL"] != "1":
			return False
		byDay = rrule.get("BYDAY", "")
		items = [item.strip() for item in byDay.split(",") if item.strip()]
		if len(items) != 1:
			return False
		item = items[0]
		if len(item) < 3:
			return False
		ordinalStr = item[:-2]
		try:
			weekDay = ics.icsWeekDays.index(item[-2:])
		except ValueError:
			return False
		if ordinalStr == "-1":
			wmIndex = 4  # Last
		else:
			try:
				ordinal = int(ordinalStr)
			except ValueError:
				return False
			if not 1 <= ordinal <= 5:
				return False
			wmIndex = ordinal - 1
		if "BYMONTH" in rrule:
			try:
				month = int(rrule["BYMONTH"])
			except ValueError:
				return False
			if not 1 <= month <= 12:
				return False
		else:
			month = 0
		self.setWeekMonthPattern(month, wmIndex, weekDay)
		return True
