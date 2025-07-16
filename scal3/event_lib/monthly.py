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

from scal3.cal_types import jd_to
from scal3.locale_man import tr as _

from .common import getCurrentJd
from .event_base import Event
from .register import classes
from .rules import (
	DayOfMonthEventRule,
	DayTimeRangeEventRule,
	EndEventRule,
	StartEventRule,
)

if TYPE_CHECKING:
	from typing import Any

	from scal3.event_lib.pytypes import EventGroupType

__all__ = ["MonthlyEvent"]


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

	def setDefaults(self, group: EventGroupType | None = None) -> None:
		super().setDefaults(group=group)
		year, month, day = jd_to(getCurrentJd(), self.calType)
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
