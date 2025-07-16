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
from scal3.event_lib.group import EventGroup

log = logger.get()

from time import localtime
from typing import TYPE_CHECKING

from scal3 import ics
from scal3.cal_types import (
	getSysDate,
)
from scal3.locale_man import tr as _
from scal3.time_utils import (
	durationDecode,
	durationEncode,
	jsonTimeFromEpoch,
)

from .common import getCurrentJd
from .event_base import Event, SingleStartEndEvent
from .register import classes
from .rules import (
	DayTimeEventRule,
	DurationEventRule,
	EndEventRule,
	StartEventRule,
)

if TYPE_CHECKING:
	from collections.abc import Sequence
	from typing import Any

	from scal3.event_lib.pytypes import EventGroupType, EventType


__all__ = ["AllDayTaskEvent", "TaskEvent", "TaskList"]

dayLen = 86400


@classes.group.register
class TaskList(EventGroup):
	name = "taskList"
	desc = _("Task List")
	params = EventGroup.params + ["defaultDuration"]
	acceptsEventTypes: Sequence[str] = (
		"task",
		"allDayTask",
	)
	# actions = EventGroup.actions + []
	sortBys = EventGroup.sortBys + [
		("start", _("Start"), True),
		("end", _("End"), True),
	]
	sortByDefault = "start"

	def getSortByValue(self, event: EventType, attr: str) -> Any:
		if event.name in self.acceptsEventTypes:
			if attr == "start":
				return event.getStartEpoch()
			if attr == "end":
				return event.getEndEpoch()
		return EventGroup.getSortByValue(self, event, attr)

	def __init__(self, ident: int | None = None) -> None:
		super().__init__(ident)
		self.defaultDuration = (0.0, 1)  # (value, unit)

	def getDict(self) -> dict[str, Any]:
		data = EventGroup.getDict(self)
		data["defaultDuration"] = durationEncode(*self.defaultDuration)
		return data

	def setDict(self, data: dict[str, Any]) -> None:
		super().setDict(data)
		if "defaultDuration" in data:
			self.defaultDuration = durationDecode(data["defaultDuration"])


@classes.event.register
class TaskEvent(SingleStartEndEvent):
	# overwrites getEndEpoch from Event
	# overwrites setEndEpoch from SingleStartEndEvent
	# overwrites setJdExact from SingleStartEndEvent
	# Methods neccessery for modifying event by hand in timeline:
	#   getStartEpoch, getEndEpoch, modifyStart, modifyEnd, modifyPos
	name = "task"
	desc = _("Task")
	iconName = "task"
	requiredRules: list[str] = ["start"]
	supportedRules = [
		"start",
		"end",
		"duration",
	]
	isAllDay = False

	def getV4Dict(self) -> dict[str, Any]:
		duration = DurationEventRule.getFrom(self)
		if duration is None:
			durationUnit = 0
		else:
			durationUnit = duration.unit

		data = Event.getV4Dict(self)
		data.update(
			{
				"startTime": jsonTimeFromEpoch(self.getStartEpoch()),
				"endTime": jsonTimeFromEpoch(self.getEndEpoch()),
				"durationUnit": durationUnit,
			},
		)
		return data

	def _setDefaultDuration(self, group: EventGroupType | None) -> None:
		if group is None or group.name != "taskList":
			self.setEndDuration(1, 3600)
			return

		# FIXME: we can't import TaskList at runtime here!
		if TYPE_CHECKING:
			assert isinstance(group, TaskList)

		value, unit = group.defaultDuration
		if value == 0:
			value, unit = 1, 3600
		self.setEndDuration(value, unit)

	def setDefaults(self, group: EventGroupType | None = None) -> None:
		super().setDefaults(group=group)
		tt = localtime()
		self.setStart(
			getSysDate(self.calType),
			(tt.tm_hour, tt.tm_min, tt.tm_sec),
		)
		self._setDefaultDuration(group)

	def setJdExact(self, jd: int) -> None:
		start = StartEventRule.getFrom(self)
		assert start is not None
		start.setJdExact(jd)
		self.setEndDuration(24, 3600)

	def setStart(
		self,
		date: tuple[int, int, int],
		dayTime: tuple[int, int, int],
	) -> None:
		start = StartEventRule.getFrom(self)
		if start is None:
			raise KeyError('rule "start" not found')
		start.date = date
		start.time = dayTime

	def setEndEpochOnly(self, epoch: int) -> None:
		self.removeSomeRuleTypes("duration")
		return super().setEndEpoch(epoch)

	def setEnd(
		self,
		endType: str,
		*values: Any,  # noqa: ANN002
	) -> None:
		if endType == "date":
			date, time = values
			self.setEndDateTime(date, time)
		elif endType == "epoch":
			self.setEndEpochOnly(values[0])
		elif endType == "duration":
			value, unit = values
			self.setEndDuration(value, unit)
		else:
			raise ValueError(f"invalid {endType=}")

	def getStart(self) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
		start = StartEventRule.getFrom(self)
		if start is None:
			raise KeyError('rule "start" not found')
		return (start.date, start.time)

	def getEnd(
		self,
	) -> tuple[
		str,
		tuple[tuple[int, int, int], tuple[int, int, int]] | tuple[float, int],
	]:
		end = EndEventRule.getFrom(self)
		if end is not None:
			return ("date", (end.date, end.time))
		duration = DurationEventRule.getFrom(self)
		if duration is not None:
			return ("duration", (duration.value, duration.unit))
		raise ValueError("no end date neither duration specified for task")

	def getEndEpoch(self) -> int:
		end = EndEventRule.getFrom(self)
		if end is not None:
			return end.getEpoch()
		duration = DurationEventRule.getFrom(self)
		if duration is not None:
			start = StartEventRule.getFrom(self)
			if start is not None:
				return start.getEpoch() + duration.getSeconds()
			raise RuntimeError("found duration rule without start rule")
		raise ValueError("no end date neither duration specified for task")

	def setEndEpoch(self, epoch: int) -> None:
		end = EndEventRule.getFrom(self)
		if end is not None:
			end.setEpoch(epoch)
			return
		duration = DurationEventRule.getFrom(self)
		if duration is not None:
			start = StartEventRule.getFrom(self)
			if start is not None:
				duration.setSeconds(epoch - start.getEpoch())
			else:
				raise RuntimeError("found duration rule without start rule")
			return
		raise ValueError("no end date neither duration specified for task")

	def modifyPos(self, newStartEpoch: int) -> None:
		start = StartEventRule.getFrom(self)
		if start is None:
			raise KeyError
		end = EndEventRule.getFrom(self)
		if end is not None:
			end.setEpoch(end.getEpoch() + newStartEpoch - start.getEpoch())
		start.setEpoch(newStartEpoch)

	def modifyStart(self, newStartEpoch: int) -> None:
		start = StartEventRule.getFrom(self)
		if start is None:
			raise KeyError
		duration = DurationEventRule.getFrom(self)
		if duration is not None:
			duration.value -= (newStartEpoch - start.getEpoch()) / duration.unit
		start.setEpoch(newStartEpoch)

	def modifyEnd(self, newEndEpoch: int) -> None:
		end = EndEventRule.getFrom(self)
		if end is not None:
			end.setEpoch(newEndEpoch)
		else:
			duration = DurationEventRule.getFrom(self)
			if duration is not None:
				duration.value = (newEndEpoch - self.getStartEpoch()) / duration.unit
			else:
				raise RuntimeError("no end rule nor duration rule")

	def copyFrom(self, other: EventType) -> None:
		super().copyFrom(other)
		myStart = StartEventRule.getFrom(self)
		if myStart is None:
			raise KeyError
		# --
		if isinstance(other, TaskEvent):
			endType, values = other.getEnd()
			self.setEnd(endType, *values)
		elif other.name == "dailyNote":
			myStart.time = (0, 0, 0)
			self.setEndDuration(24, 3600)
		elif other.name == "allDayTask":
			self.removeSomeRuleTypes("end", "duration")
			self.copySomeRuleTypesFrom(other, "start", "end", "duration")
		else:
			otherDayTime = DayTimeEventRule.getFrom(self)
			if otherDayTime is not None:
				myStart.time = otherDayTime.dayTime

	def setIcsData(self, data: dict[str, str]) -> bool:
		self.setStartEpoch(ics.getEpochByIcsTime(data["DTSTART"]))
		self.setEndEpoch(ics.getEpochByIcsTime(data["DTEND"]))  # FIXME
		return True


@classes.event.register
class AllDayTaskEvent(SingleStartEndEvent):
	# overwrites getEndEpoch from SingleStartEndEvent
	name = "allDayTask"
	desc = _("All-Day Task")
	iconName = "task"
	requiredRules = ["start"]
	supportedRules = [
		"start",
		"end",
		"duration",
	]
	isAllDay = True

	def getV4Dict(self) -> dict[str, Any]:
		if DurationEventRule.getFrom(self) is None:
			durationEnable = False
		else:
			durationEnable = True

		data = Event.getV4Dict(self)
		data.update(
			{
				"startJd": self.getStartJd(),
				"endJd": self.getEndJd(),
				"durationEnable": durationEnable,
			},
		)
		return data

	def setJd(self, jd: int) -> None:
		start = StartEventRule.addOrGetFrom(self)
		start.setJdExact(jd)

	def setStartDate(self, date: tuple[int, int, int]) -> None:
		start = StartEventRule.addOrGetFrom(self)
		start.setDate(date)

	def setJdExact(self, jd: int) -> None:
		self.setJd(jd)
		self.setEndDurationDays(1)

	def setDefaults(self, group: EventGroupType | None = None) -> None:
		super().setDefaults(group=group)
		jd = getCurrentJd()
		self.setJd(jd)
		self.setEndDurationDays(1)
		# if group and group.name == "taskList":
		# 	value, unit = group.defaultAllDayDuration
		# 	if value > 0:
		# 		self.setEndDurationDays(value)

	def setEndDurationDays(self, value: float) -> None:
		self.removeSomeRuleTypes("duration")
		rule = DurationEventRule.addOrGetFrom(self)
		rule.value = value
		rule.unit = dayLen

	def setEnd(self, endType: str, value: tuple[int, int, int] | float) -> None:
		if endType == "date":
			assert isinstance(value, tuple), f"{value=}"
			self.setEndDateTime(value, (0, 0, 0))
		elif endType == "epoch":
			assert isinstance(value, int), f"{value=}"
			self.setEndEpochOnly(value)
		elif endType == "duration":
			assert isinstance(value, float), f"{value=}"
			self.setEndDuration(value, dayLen)
		elif endType == "jd":
			assert isinstance(value, int), f"{value=}"
			self.setEndEpochOnly(self.getEpochFromJd(value))
		else:
			raise ValueError(f"invalid {endType=}")

	def getEnd(self) -> tuple[str, tuple[int, int, int] | float]:
		end = EndEventRule.getFrom(self)
		if end is not None:
			return ("date", end.date)
		duration = DurationEventRule.getFrom(self)
		if duration is not None:
			return ("duration", duration.value)
		raise ValueError("no end date neither duration specified for task")

	def getEndJd(self) -> int:
		end = EndEventRule.getFrom(self)
		if end is not None:
			# assert isinstance(end.getJd(), int)
			return end.getJd()
		duration = DurationEventRule.getFrom(self)
		if duration is not None:
			start = StartEventRule.getFrom(self)
			if start is None:
				raise RuntimeError("no start rule")
			# assert isinstance(start.getJd(), int)
			return start.getJd() + duration.getSeconds() // dayLen
		raise ValueError("no end date neither duration specified for task")

	def getEndEpoch(self) -> int:
		# if not isinstance(self.getEndJd(), int):
		# 	raise TypeError(f"{self}.getEndJd() returned non-int: {self.getEndJd()}")
		return self.getEpochFromJd(self.getEndJd())

	# def setEndJd(self, jd):
	# 	EndEventRule.getFrom(self).setJdExact(jd)

	def setEndJd(self, jd: int) -> None:
		end = EndEventRule.getFrom(self)
		if end is not None:
			end.setJd(jd)
			return
		duration = DurationEventRule.getFrom(self)
		if duration is not None:
			start = StartEventRule.getFrom(self)
			if start is not None:
				duration.setSeconds(dayLen * (jd - start.getJd()))
				return
		raise ValueError("no end date neither duration specified for task")

	def getIcsData(self, prettyDateTime: bool = False) -> list[tuple[str, str]] | None:
		return [
			("DTSTART", ics.getIcsDateByJd(self.getJd(), prettyDateTime)),
			("DTEND", ics.getIcsDateByJd(self.getEndJd(), prettyDateTime)),
			("TRANSP", "OPAQUE"),
			("CATEGORIES", self.name),  # FIXME
		]

	def setIcsData(self, data: dict[str, str]) -> bool:
		self.setJd(ics.getJdByIcsDate(data["DTSTART"]))
		self.setEndJd(ics.getJdByIcsDate(data["DTEND"]))  # FIXME
		return True

	def copyFrom(self, other: EventType) -> None:
		super().copyFrom(other)
		if other.name == self.name:
			assert isinstance(other, AllDayTaskEvent), f"{other=}"
			kind, value = other.getEnd()
			self.setEnd(kind, value)
