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
from scal3.event_lib.groups import EventGroup

log = logger.get()

from typing import TYPE_CHECKING, Any

from scal3.locale_man import tr as _
from scal3.time_utils import (
	getFloatJdFromEpoch,
	roundEpochToDay,
)

from .event_base import Event, SingleStartEndEvent
from .register import classes
from .rules import (
	DateAndTimeEventRule,
	EndEventRule,
	StartEventRule,
)

if TYPE_CHECKING:
	from collections.abc import Sequence

	from scal3.event_lib.pytypes import EventType

	from .pytypes import EventRuleType

__all__ = ["LifetimeEvent", "LifetimeGroup"]


@classes.group.register
class LifetimeGroup(EventGroup):
	name = "lifetime"
	nameAlias = "lifeTime"
	desc = _("Lifetime Events Group")
	acceptsEventTypes: Sequence[str] = ("lifetime",)
	sortBys = EventGroup.sortBys + [
		("start", _("Start"), True),
	]
	params = EventGroup.params + ["showSeparateYmdInputs"]

	def getSortByValue(self, event: EventType, attr: str) -> Any:
		if event.name in self.acceptsEventTypes:
			if attr == "start":
				return event.getStartJd()
			if attr == "end":
				return event.getEndJd()
		return EventGroup.getSortByValue(self, event, attr)

	def __init__(self, ident: int | None = None) -> None:
		self.showSeparateYmdInputs = False
		super().__init__(ident)

	def setDict(self, data: dict[str, Any]) -> None:
		if "showSeperatedYmdInputs" in data:
			# misspell in < 3.1.x
			data["showSeparateYmdInputs"] = data["showSeperatedYmdInputs"]
		if "showSeparatedYmdInputs" in data:
			data["showSeparateYmdInputs"] = data["showSeparatedYmdInputs"]
		super().setDict(data)

	def setDefaults(self) -> None:
		# only show in time line
		self.showInDCal = False
		self.showInWCal = False
		self.showInMCal = False
		self.showInStatusIcon = False


@classes.event.register
class LifetimeEvent(SingleStartEndEvent):
	name = "lifetime"
	nameAlias = "lifeTime"
	desc = _("Lifetime Event")
	requiredRules = [
		"start",
		"end",
	]
	supportedRules = [
		"start",
		"end",
	]
	isAllDay = True

	# def setDefaults(self):
	# 	start = StartEventRule.getFrom(self)
	# 	if XX is not None:
	# 		start.date = ...

	def getV4Dict(self) -> dict[str, str]:
		data = Event.getV4Dict(self)
		data.update(
			{
				"startJd": self.getStartJd(),
				"endJd": self.getEndJd(),
			},
		)
		return data

	def setJd(self, jd: int) -> None:
		StartEventRule.addOrGetFrom(self).setJdExact(jd)
		EndEventRule.addOrGetFrom(self).setJdExact(jd)

	def addRule(self, rule: EventRuleType) -> None:
		if rule.name in {"start", "end"}:
			assert isinstance(rule, DateAndTimeEventRule), f"{rule=}"
			rule.time = (0, 0, 0)
		super().addRule(rule)

	def modifyPos(self, newStartEpoch: int) -> None:
		start = StartEventRule.getFrom(self)
		assert start is not None
		end = EndEventRule.getFrom(self)
		assert end is not None
		newStartJd = round(getFloatJdFromEpoch(newStartEpoch))
		end.setJdExact(end.getJd() + newStartJd - start.getJd())
		start.setJdExact(newStartJd)

	def modifyStart(self, newEpoch: int) -> None:
		start = StartEventRule.getFrom(self)
		if start is None:
			raise RuntimeError("no start rule")
		start.setEpoch(roundEpochToDay(newEpoch))

	def modifyEnd(self, newEpoch: int) -> None:
		end = EndEventRule.getFrom(self)
		if end is None:
			raise RuntimeError("no end rule")
		end.setEpoch(roundEpochToDay(newEpoch))
