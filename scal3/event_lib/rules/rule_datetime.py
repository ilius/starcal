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
from scal3.cal_types import convert
from scal3.date_utils import dateDecode, dateEncode
from scal3.event_lib.exceptions import BadEventFile
from scal3.event_lib.occur import IntervalOccurSet
from scal3.event_lib.register import classes
from scal3.locale_man import tr as _
from scal3.time_utils import timeDecode, timeEncode

from .rule_date import DateEventRule

if TYPE_CHECKING:
	from collections.abc import Sequence
	from typing import Any

	from scal3.event_lib.pytypes import EventType, OccurSetType, RuleContainerType


log = logger.get()

__all__ = ["DateAndTimeEventRule", "EndEventRule", "StartEventRule"]


class DateAndTimeEventRule(DateEventRule):
	"""Rule that specifies both a date and a time of day for an event."""

	sgroup = 1
	params = [
		"date",
		"time",
	]

	def getServerString(self) -> str:
		"""Return date and time as a 'YYYY/MM/DD HH:MM:SS' string."""
		y, m, d = self.date
		H, M, S = self.time
		return f"{y:04d}/{m:02d}/{d:02d} {H:02d}:{M:02d}:{S:02d}"

	def __init__(self, parent: RuleContainerType) -> None:
		super().__init__(parent)
		self.time = localtime()[3:6]

	def getEpoch(self) -> int:
		"""Return the epoch timestamp for this date and time."""
		return self.parent.getEpochFromJhms(
			self.getJd(),
			self.time[0],
			self.time[1],
			self.time[2],
		)

	def setEpoch(self, epoch: int) -> None:
		"""Set the date and time from an epoch timestamp."""
		jd, hms = self.parent.getJhmsFromEpoch(epoch)
		self.setJd(jd)
		self.time = hms.tuple()

	def setJdExact(self, jd: int) -> None:
		"""Set the date from a Julian day, resetting time to midnight."""
		self.setJd(jd)
		self.time = (0, 0, 0)

	def setDate(self, date: tuple[int, int, int]) -> None:
		"""Set the date, resetting time to midnight."""
		if len(date) != 3:
			raise ValueError(f"DateAndTimeEventRule.setDate: bad {date = }")
		self.date = date
		self.time = (0, 0, 0)

	def getDate(self, calType: int) -> tuple[int, int, int]:
		"""Return the date converted to the given calendar type."""
		return convert(
			self.date[0],
			self.date[1],
			self.date[2],
			self.getCalType(),
			calType,
		)

	def getRuleValue(self) -> Any:
		"""Return date and time as a serializable dictionary."""
		return {
			"date": dateEncode(self.date),
			"time": timeEncode(self.time),
		}

	def setRuleValue(self, arg: dict[str, str] | str) -> None:
		"""Set date and time from serialized data, raising BadEventFile on bad input."""
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
		"""Return a human-readable description of this rule."""
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
class StartEventRule(DateAndTimeEventRule):
	"""Rule that marks the start date and time of an event."""

	name = "start"
	desc = _("Start")
	conflict: Sequence[str] = ("date",)

	# def getServerString(self) -> str: # in DateAndTimeEventRule

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,  # noqa: ARG002
	) -> OccurSetType:
		"""Return the interval from the start rule through the range end."""
		return IntervalOccurSet.newFromStartEnd(
			max(self.getEpochFromJd(startJd), self.getEpoch()),
			self.getEpochFromJd(endJd),
		)


@classes.rule.register
class EndEventRule(DateAndTimeEventRule):
	"""Rule that marks the end date and time of an event."""

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
	) -> OccurSetType:
		"""Return the interval from the range start through the end rule."""
		return IntervalOccurSet.newFromStartEnd(
			self.getEpochFromJd(startJd),
			min(self.getEpochFromJd(endJd), self.getEpoch()),
		)
