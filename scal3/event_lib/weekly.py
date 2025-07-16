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

from scal3.locale_man import tr as _

from .common import getCurrentJd
from .event_base import Event
from .register import classes
from .rules import (
	CycleWeeksEventRule,
	DayTimeRangeEventRule,
	EndEventRule,
	StartEventRule,
)

if TYPE_CHECKING:
	from typing import Any

	from scal3.event_lib.pytypes import EventGroupType

__all__ = ["WeeklyEvent"]


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
