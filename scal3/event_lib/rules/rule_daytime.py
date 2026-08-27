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

from scal3.event_lib.common import dayLen


@classes.rule.register
class DayTimeEventRule(EventRule):  # Moment Event
	"""Rule that specifies a single time of day, recurring daily at that moment."""

	name = "dayTime"
	desc = _("Time in Day")
	provide: Sequence[str] = ("time",)
	conflict: Sequence[str] = (
		"dayTimeRange",
		"cycleLen",
	)
	params = ["dayTime"]

	def getServerString(self) -> str:
		"""Return the time of day as an 'HH:MM:SS' string."""
		H, M, S = self.dayTime
		return f"{H:02d}:{M:02d}:{S:02d}"

	def __str__(self) -> str:
		H, M, S = self.dayTime
		return f"{H:02d}:{M:02d}:{S:02d}"

	def __init__(self, parent: RuleContainerType) -> None:
		super().__init__(parent)
		self.dayTime = localtime()[3:6]

	def getRuleValue(self) -> Any:
		"""Return the time of day as an encoded string."""
		return timeEncode(self.dayTime)

	def setRuleValue(self, data: str) -> None:
		"""Set the time of day from an encoded string."""
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
		"""Return one moment per day at this time of day."""
		mySec = getSecondsFromHms(*self.dayTime)
		return TimeListOccurSet.fromRange(  # FIXME
			self.getEpochFromJd(startJd) + mySec,
			self.getEpochFromJd(endJd) + mySec + 1,
			dayLen,
		)

	def getInfo(self) -> str:
		"""Return a human-readable description of the time of day."""
		return _("Time in Day") + ": " + timeEncode(self.dayTime)


@classes.rule.register
class DayTimeRangeEventRule(EventRule):
	"""Rule that specifies a time range within each day (e.g. 09:00 to 17:00)."""

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
		"""Return the time range as a space-separated string."""
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
		"""Set the start and end time of the daily range."""
		self.dayTimeStart = start
		self.dayTimeEnd = end

	def getHourRange(self) -> tuple[float, float]:
		"""Return the start and end times as fractional hours."""
		return (
			timeToFloatHour(*self.dayTimeStart),
			timeToFloatHour(*self.dayTimeEnd),
		)

	def getSecondsRange(self) -> tuple[int, int]:
		"""Return the start and end times as seconds since midnight."""
		return (
			getSecondsFromHms(*self.dayTimeStart),
			getSecondsFromHms(*self.dayTimeEnd),
		)

	def getRuleValue(self) -> Any:
		"""Return start and end times as a tuple of encoded strings."""
		return (timeEncode(self.dayTimeStart), timeEncode(self.dayTimeEnd))

	def setRuleValue(self, data: tuple[str, str]) -> None:
		"""Set the time range from encoded start and end strings."""
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
		"""Return one interval per day covering the time range."""
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
