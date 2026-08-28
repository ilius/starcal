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

from .common import dayLen


@classes.group.register
class TaskList(EventGroup):
	"""Group for task events with a configurable default duration."""

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
		"""Return the sort key value for the given attribute."""
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
		"""Return a dictionary representation of the group."""
		data = EventGroup.getDict(self)
		data["defaultDuration"] = durationEncode(*self.defaultDuration)
		return data

	def setDict(self, data: dict[str, Any]) -> None:
		"""Load group properties from a dictionary."""
		super().setDict(data)
		if "defaultDuration" in data:
			self.defaultDuration = durationDecode(data["defaultDuration"])


@classes.event.register
class TaskEvent(SingleStartEndEvent):
	"""Timed task with a start time and optional end time or duration."""

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
		"""Return v4 format dictionary representation."""
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
		"""Set default start to now and a duration from the group."""
		super().setDefaults(group=group)
		tt = localtime()
		self.setStart(
			getSysDate(self.calType),
			(tt.tm_hour, tt.tm_min, tt.tm_sec),
		)
		self._setDefaultDuration(group)

	def _setJdExact(self, jd: int) -> None:
		"""Set the start Julian Day and reset duration to 24 hours."""
		start = StartEventRule.getFrom(self)
		assert start is not None
		start.setJdExact(jd)
		self.setEndDuration(24, 3600)

	def setStart(
		self,
		date: tuple[int, int, int],
		dayTime: tuple[int, int, int],
	) -> None:
		"""Set the start date and time."""
		start = StartEventRule.getFrom(self)
		if start is None:
			raise KeyError('rule "start" not found')
		start.date = date
		start.time = dayTime

	def _setEndEpochOnly(self, epoch: int) -> None:
		"""Set the end time by epoch, removing any duration rule."""
		self._removeSomeRuleTypes("duration")
		return super().setEndEpoch(epoch)

	def _setEnd(
		self,
		endType: str,
		*values: Any,
	) -> None:
		"""Set the end by type ('date', 'epoch', or 'duration')."""
		if endType == "date":
			date, time = values
			self.setEndDateTime(date, time)
		elif endType == "epoch":
			self._setEndEpochOnly(values[0])
		elif endType == "duration":
			value, unit = values
			self.setEndDuration(value, unit)
		else:
			raise ValueError(f"invalid {endType=}")

	def getStart(self) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
		"""Return the start as (date, time) tuples."""
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
		"""Return the end as ('date', (date, time)) or ('duration', (value, unit))."""
		end = EndEventRule.getFrom(self)
		if end is not None:
			return ("date", (end.date, end.time))
		duration = DurationEventRule.getFrom(self)
		if duration is not None:
			return ("duration", (duration.value, duration.unit))
		raise ValueError("no end date neither duration specified for task")

	def getEndEpoch(self) -> int:
		"""Return the end time as an epoch, computing from duration if needed."""
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
		"""Set the end time by epoch, adjusting duration if no end rule exists."""
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
		"""Move the task to start at the given epoch, preserving duration."""
		start = StartEventRule.getFrom(self)
		if start is None:
			raise KeyError
		end = EndEventRule.getFrom(self)
		if end is not None:
			end.setEpoch(end.getEpoch() + newStartEpoch - start.getEpoch())
		start.setEpoch(newStartEpoch)

	def modifyStart(self, newStartEpoch: int) -> None:
		"""Change the start time, adjusting duration to preserve the end time."""
		start = StartEventRule.getFrom(self)
		if start is None:
			raise KeyError
		duration = DurationEventRule.getFrom(self)
		if duration is not None:
			duration.value -= (newStartEpoch - start.getEpoch()) / duration.unit
		start.setEpoch(newStartEpoch)

	def modifyEnd(self, newEndEpoch: int) -> None:
		"""Change the end time, adjusting duration if no end rule exists."""
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
		"""Copy properties from another event, adjusting time components."""
		super().copyFrom(other)
		myStart = StartEventRule.getFrom(self)
		if myStart is None:
			raise KeyError
		# --
		if isinstance(other, TaskEvent):
			endType, values = other.getEnd()
			self._setEnd(endType, *values)
		elif other.name == "dailyNote":
			myStart.time = (0, 0, 0)
			self.setEndDuration(24, 3600)
		elif other.name == "allDayTask":
			self._removeSomeRuleTypes("end", "duration")
			self._copySomeRuleTypesFrom(other, "start", "end", "duration")
		else:
			otherDayTime = DayTimeEventRule.getFrom(self)
			if otherDayTime is not None:
				myStart.time = otherDayTime.dayTime

	def setIcsData(self, data: dict[str, str]) -> bool:
		"""Import event data from an iCalendar dictionary."""
		self.setStartEpoch(ics.getEpochByIcsTime(data["DTSTART"]))
		self.setEndEpoch(ics.getEpochByIcsTime(data["DTEND"]))  # FIXME
		return True


@classes.event.register
class AllDayTaskEvent(SingleStartEndEvent):
	"""All-day task spanning one or more full days."""

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
		"""Return v4 format dictionary representation."""
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
		"""Set the start date from a Julian day."""
		start = StartEventRule.addOrGetFrom(self)
		start.setJdExact(jd)

	def setStartDate(self, date: tuple[int, int, int]) -> None:
		"""Set the start date."""
		start = StartEventRule.addOrGetFrom(self)
		start.setDate(date)

	def _setJdExact(self, jd: int) -> None:
		"""Set the start Julian Day and duration to one day."""
		self.setJd(jd)
		self.setEndDurationDays(1)

	def setDefaults(self, group: EventGroupType | None = None) -> None:
		"""Set default start to today and a duration of one day."""
		super().setDefaults(group=group)
		jd = getCurrentJd()
		self.setJd(jd)
		self.setEndDurationDays(1)
		# if group and group.name == "taskList":
		# 	value, unit = group.defaultAllDayDuration
		# 	if value > 0:
		# 		self.setEndDurationDays(value)

	def setEndDurationDays(self, value: float) -> None:
		"""Set the end as a duration in days."""
		self._removeSomeRuleTypes("end", "date")
		rule = DurationEventRule.addOrGetFrom(self)
		rule.value = value
		rule.unit = dayLen

	def _setEndEpochOnly(self, epoch: int) -> None:
		"""Set the end time by epoch, removing any duration rule."""
		self._removeSomeRuleTypes("duration")
		return super().setEndEpoch(epoch)

	def _setEnd(self, endType: str, value: tuple[int, int, int] | int | float) -> None:
		"""Set the end by type ('date', 'epoch', 'duration', or 'jd')."""
		if endType == "date":
			assert isinstance(value, tuple), f"{value=}"
			self.setEndDateTime(value, (0, 0, 0))
		elif endType == "epoch":
			assert isinstance(value, int), f"{value=}"
			self._setEndEpochOnly(value)
		elif endType == "duration":
			assert isinstance(value, float), f"{value=}"
			self.setEndDuration(value, dayLen)
		elif endType == "jd":
			assert isinstance(value, int), f"{value=}"
			self._setEndEpochOnly(self.getEpochFromJd(value))
		else:
			raise ValueError(f"invalid {endType=}")

	def getEnd(self) -> tuple[str, tuple[int, int, int] | float]:
		"""Return the end as ('date', date) or ('duration', days)."""
		end = EndEventRule.getFrom(self)
		if end is not None:
			return ("date", end.date)
		duration = DurationEventRule.getFrom(self)
		if duration is not None:
			return ("duration", duration.value)
		raise ValueError("no end date neither duration specified for task")

	def getEndJd(self) -> int:
		"""Return the end Julian Day, computing from duration if needed."""
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
		"""Return the end time as an epoch."""
		# if not isinstance(self.getEndJd(), int):
		# 	raise TypeError(f"{self}.getEndJd() returned non-int: {self.getEndJd()}")
		return self.getEpochFromJd(self.getEndJd())

	# def _setEndJd(self, jd):
	# 	EndEventRule.getFrom(self).setJdExact(jd)

	def _setEndJd(self, jd: int) -> None:
		"""Set the end Julian Day, adjusting duration if no end rule exists."""
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
		"""Return iCalendar data for this all-day task."""
		return [
			("DTSTART", ics.getIcsDateByJd(self.getJd(), prettyDateTime)),
			("DTEND", ics.getIcsDateByJd(self.getEndJd(), prettyDateTime)),
			("TRANSP", "OPAQUE"),
			("CATEGORIES", self.name),  # FIXME
		]

	def setIcsData(self, data: dict[str, str]) -> bool:
		"""Import event data from an iCalendar dictionary."""
		self.setJd(ics.getJdByIcsDate(data["DTSTART"]))
		self._setEndJd(ics.getJdByIcsDate(data["DTEND"]))  # FIXME
		return True

	def copyFrom(self, other: EventType) -> None:
		"""Copy properties from another event, preserving the end configuration."""
		super().copyFrom(other)
		if other.name == self.name:
			assert isinstance(other, AllDayTaskEvent), f"{other=}"
			kind, value = other.getEnd()
			self._setEnd(kind, value)
