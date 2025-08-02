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
from scal3.event_lib.occur import IntervalOccurSet
from scal3.event_lib.register import classes
from scal3.locale_man import floatEncode
from scal3.locale_man import tr as _
from scal3.time_utils import (
	durationDecode,
	durationEncode,
)

from .rule_base import EventRule

if TYPE_CHECKING:
	from collections.abc import Sequence
	from typing import Any

	from scal3.event_lib.pytypes import EventType, OccurSetType, RuleContainerType

__all__ = ["DurationEventRule"]

log = logger.get()

dayLen = 86400


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
		super().__init__(parent)
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
	) -> OccurSetType:
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
