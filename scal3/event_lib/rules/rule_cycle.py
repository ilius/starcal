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

from typing import TYPE_CHECKING

from scal3 import logger
from scal3.event_lib.occur import JdOccurSet, TimeListOccurSet
from scal3.event_lib.register import classes
from scal3.locale_man import tr as _
from scal3.time_utils import (
	getSecondsFromHms,
	timeDecode,
	timeEncode,
)

from .rule_base import EventRule

if TYPE_CHECKING:
	from collections.abc import Sequence
	from typing import Any

	from scal3.event_lib.pytypes import EventType, OccurSetType, RuleContainerType

__all__ = ["CycleLenEventRule", "CycleWeeksEventRule"]

log = logger.get()

dayLen = 86400


def cycleDaysCalcOccurrence(
	days: int,
	startJd: int,
	endJd: int,
	event: EventType,
) -> OccurSetType:
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
		super().__init__(parent)
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
	) -> OccurSetType:
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
		super().__init__(parent)
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
	) -> OccurSetType:
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
	provide: Sequence[str] = ("time",)
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
		super().__init__(parent)
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
	) -> OccurSetType:
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
