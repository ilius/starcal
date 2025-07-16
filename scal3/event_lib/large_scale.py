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

from contextlib import suppress

from scal3 import logger

log = logger.get()

from typing import TYPE_CHECKING

from scal3.cal_types import (
	jd_to,
	to_jd,
)
from scal3.event_lib.group import EventGroup
from scal3.locale_man import tr as _
from scal3.utils import iceil, ifloor

from .event_base import Event
from .occur import IntervalOccurSet
from .register import classes

if TYPE_CHECKING:
	from collections.abc import Sequence
	from typing import Any

	from scal3.event_lib.pytypes import (
		EventContainerType,
		EventGroupType,
		EventType,
		OccurSetType,
	)

__all__ = ["LargeScaleEvent", "LargeScaleGroup"]


@classes.event.register
class LargeScaleEvent(Event):  # or MegaEvent? FIXME
	name = "largeScale"
	desc = _("Large Scale Event")
	isSingleOccur = True
	_myOptions = [
		"scale",
		"start",
		"end",
		"endRel",
	]
	params = Event.params + _myOptions
	paramsOrder = Event.paramsOrder + _myOptions

	def __bool__(self) -> bool:
		return True

	isAllDay = True

	def getV4Dict(self) -> dict[str, Any]:
		data = Event.getV4Dict(self)
		data.update(
			{
				"scale": self.scale,
				"start": self.start,
				"end": self.end,
				"durationEnable": self.endRel,
			},
		)
		return data

	def __init__(
		self,
		ident: int | None = None,
		parent: EventContainerType | None = None,
	) -> None:
		self.scale = 1  # 1, 1000, 1000**2, 1000**3
		self.start = 0
		self.end = 1
		self.endRel = True
		super().__init__(ident, parent)

	def setDict(self, data: dict[str, Any]) -> None:
		super().setDict(data)
		if "duration" in data:
			data["end"] = data["duration"]
			data["endRel"] = True

	def getRulesHash(self) -> int:
		return hash(
			str(
				(
					self.getTimeZoneStr(),
					"largeScale",
					self.scale,
					self.start,
					self.end,
					self.endRel,
				),
			),
		)
		# hash(str(tupleObj)) is probably safer than hash(tupleObj)

	def getEnd(self) -> int:
		return self.start + self.end if self.endRel else self.end

	def setDefaults(self, group: EventGroupType | None = None) -> None:
		super().setDefaults(group=group)
		if group and group.name == "largeScale":
			if TYPE_CHECKING:
				assert isinstance(group, LargeScaleEvent), f"{group=}"
			self.scale = group.scale
			self.start = group.getStartValue()

	def getJd(self) -> int:
		return to_jd(
			self.start * self.scale,
			1,
			1,
			self.calType,
		)

	def setJd(self, jd: int) -> None:
		self.start = jd_to(jd, self.calType)[0] // self.scale

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSetType:
		myStartJd = iceil(
			to_jd(
				int(self.scale * self.start),
				1,
				1,
				self.calType,
			),
		)
		myEndJd = ifloor(
			to_jd(
				int(self.scale * self.getEnd()),
				1,
				1,
				self.calType,
			),
		)
		return IntervalOccurSet.newFromStartEnd(
			max(
				self.getEpochFromJd(myStartJd),
				self.getEpochFromJd(startJd),
			),
			min(
				self.getEpochFromJd(myEndJd),
				self.getEpochFromJd(endJd),
			),
		)

	# def getIcsData(self, prettyDateTime=False):
	# 	pass


@classes.group.register
class LargeScaleGroup(EventGroup):
	name = "largeScale"
	desc = _("Large Scale Events Group")
	acceptsEventTypes: Sequence[str] = ("largeScale",)
	params = EventGroup.params + ["scale"]
	sortBys = EventGroup.sortBys + [
		("start", _("Start"), True),
		("end", _("End"), True),
	]
	sortByDefault = "start"

	def getSortByValue(self, event: EventType, attr: str) -> Any:
		if event.name == "largeScale":
			assert isinstance(event, LargeScaleEvent), f"{event=}"
			if attr == "start":
				return event.start * event.scale
			if attr == "end":
				return event.getEnd() * event.scale
		return EventGroup.getSortByValue(self, event, attr)

	def __init__(self, ident: int | None = None) -> None:
		self.scale = 1  # 1, 1000, 1000**2, 1000**3
		super().__init__(ident)

	def setDefaults(self) -> None:
		self.startJd = 0
		self.endJd = self.startJd + self.scale * 9999
		# only show in time line
		self.showInDCal = False
		self.showInWCal = False
		self.showInMCal = False
		self.showInStatusIcon = False

	def getDict(self) -> dict[str, Any]:
		data = EventGroup.getDict(self)
		data["scale"] = self.scale
		return data

	def setDict(self, data: dict[str, Any]) -> None:
		super().setDict(data)
		with suppress(KeyError):
			self.scale = data["scale"]

	def getStartValue(self) -> int:
		return int(jd_to(self.startJd, self.calType)[0] // self.scale)

	def getEndValue(self) -> int:
		return int(jd_to(self.endJd, self.calType)[0] // self.scale)

	def setStartValue(self, start: float) -> None:
		self.startJd = int(
			to_jd(
				int(start * self.scale),
				1,
				1,
				self.calType,
			),
		)

	def setEndValue(self, end: float) -> None:
		self.endJd = int(
			to_jd(
				int(end * self.scale),
				1,
				1,
				self.calType,
			),
		)
