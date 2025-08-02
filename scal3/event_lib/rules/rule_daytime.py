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

from time import localtime
from typing import TYPE_CHECKING

from scal3 import logger
from scal3.event_lib.occur import IntervalOccurSet, TimeListOccurSet
from scal3.event_lib.register import classes
from scal3.locale_man import tr as _
from scal3.time_utils import (
	getSecondsFromHms,
	timeDecode,
	timeEncode,
	timeToFloatHour,
)

from .rule_base import EventRule

if TYPE_CHECKING:
	from collections.abc import Sequence
	from typing import Any

	from scal3.event_lib.pytypes import EventType, OccurSetType, RuleContainerType


log = logger.get()

__all__ = ["DayTimeEventRule", "DayTimeRangeEventRule"]

dayLen = 86400


@classes.rule.register
class DayTimeEventRule(EventRule):  # Moment Event
	name = "dayTime"
	desc = _("Time in Day")
	provide: Sequence[str] = ("time",)
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
		super().__init__(parent)
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
	) -> OccurSetType:
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
		super().__init__(parent)
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
	) -> OccurSetType:
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
