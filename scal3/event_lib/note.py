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

from typing import TYPE_CHECKING

from scal3 import ics
from scal3.cal_types import getSysDate
from scal3.locale_man import tr as _

from .event_base import Event
from .occur import JdOccurSet
from .register import classes
from .rules import DateEventRule

if TYPE_CHECKING:
	from collections.abc import Sequence
	from typing import Any

	from scal3.event_lib.pytypes import EventGroupType, EventType, OccurSetType

__all__ = ["DailyNoteEvent", "NoteBook"]


@classes.group.register
class NoteBook(EventGroup):
	name = "noteBook"
	desc = _("Note Book")
	acceptsEventTypes: Sequence[str] = ("dailyNote",)
	canConvertTo: list[str] = [
		"yearly",
		"taskList",
	]
	# actions = EventGroup.actions + []
	sortBys = EventGroup.sortBys + [("date", _("Date"), True)]
	sortByDefault = "date"

	def getSortByValue(self, event: EventType, attr: str) -> Any:
		if event.name in self.acceptsEventTypes and attr == "date":
			return event.getJd()
		return EventGroup.getSortByValue(self, event, attr)


@classes.event.register
class DailyNoteEvent(Event):
	name = "dailyNote"
	desc = _("Daily Note")
	isSingleOccur = True
	iconName = "note"
	requiredRules = ["date"]
	supportedRules = ["date"]
	isAllDay = True

	def getV4Dict(self) -> dict[str, Any]:
		data = Event.getV4Dict(self)
		data.update(
			{
				"jd": self.getJd(),
			},
		)
		return data

	def getDate(self) -> tuple[int, int, int] | None:
		rule = DateEventRule.getFrom(self)
		if rule is not None:
			return rule.date
		return None

	def setDate(self, year: int, month: int, day: int) -> None:
		rule = DateEventRule.getFrom(self)
		if rule is None:
			raise KeyError("no date rule")
		rule.date = (year, month, day)

	def getJd(self) -> int:
		rule = DateEventRule.getFrom(self)
		if rule is not None:
			return rule.getJd()
		return self.getStartJd()

	def setJd(self, jd: int) -> None:
		rule = DateEventRule.getFrom(self)
		if rule is None:
			log.error("DailyNoteEvent: setJd: no date rule")
			return
		rule.setJd(jd)

	def setDefaults(self, group: EventGroupType | None = None) -> None:
		super().setDefaults(group=group)
		self.setDate(*getSysDate(self.calType))

	# startJd and endJd can be float jd
	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSetType:
		jd = self.getJd()
		return JdOccurSet(
			{jd} if startJd <= jd < endJd else set(),
		)

	def getIcsData(self, prettyDateTime: bool = False) -> list[tuple[str, str]] | None:
		jd = self.getJd()
		return [
			("DTSTART", ics.getIcsDateByJd(jd, prettyDateTime)),
			("DTEND", ics.getIcsDateByJd(jd + 1, prettyDateTime)),
			("TRANSP", "TRANSPARENT"),
			("CATEGORIES", self.name),  # FIXME
		]

	def setIcsData(self, data: dict[str, str]) -> bool:
		self.setJd(ics.getJdByIcsDate(data["DTSTART"]))
		return True
