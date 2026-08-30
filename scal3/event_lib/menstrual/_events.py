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

log = logger.get()

from scal3 import ics
from scal3.cal_types import getSysDate
from scal3.event_lib.event_base import Event
from scal3.event_lib.menstrual._group import MenstrualCycleGroup
from scal3.event_lib.menstrual._stats import (
	_menstrualIcon,
	_percent,
	dayProbabilityRelativeToOvulation,
	defaultPeriodLength,
	observationFlowLabels,
	observationMucusLabels,
	observationOpkLabels,
	observationRecordedByLabels,
)
from scal3.event_lib.occur import JdOccurSet
from scal3.event_lib.register import classes
from scal3.event_lib.rules import DateEventRule
from scal3.locale_man import tr as _

if TYPE_CHECKING:
	from typing import Any

	from scal3.event_lib.pytypes import EventGroupType, OccurSetType


@classes.event.register
class MenstrualPeriodEvent(Event):
	"""A recorded period start (or a predicted one when ``predicted`` is True)."""

	name = "menstrualPeriod"
	desc = _("Period")
	iconName = "menstruation"
	isSingleOccur = True
	requiredRules = ["date"]
	supportedRules = ["date"]
	isAllDay = True
	_myParams = [
		"predicted",
		"anchorJd",
		"actualCycle",
		"ovulationOverride",
	]
	params = Event.params + _myParams
	paramsOrder = Event.paramsOrder + _myParams

	@classmethod
	def getDefaultIcon(cls) -> str:
		return _menstrualIcon(cls.iconName)

	def __bool__(self) -> bool:
		return True

	def getV4Dict(self) -> dict[str, Any]:
		"""Return v4 format dictionary representation."""
		data = Event.getV4Dict(self)
		data.update({"jd": self.getJd()})
		return data

	def getDate(self) -> tuple[int, int, int] | None:
		"""Return the period-start date as (year, month, day)."""
		if self.predicted:
			return None
		rule = DateEventRule.getFrom(self)
		if rule is not None:
			return rule.date
		return None

	def getJd(self) -> int:
		"""Return the period-start Julian day."""
		if self.predicted:
			return int(self.anchorJd)
		rule = DateEventRule.getFrom(self)
		if rule is not None:
			return rule.getJd()
		return int(self.anchorJd)

	def setJd(self, jd: int) -> None:
		"""Set the period-start date from a Julian day."""
		rule = DateEventRule.getFrom(self)
		if rule is not None:
			rule.setJd(jd)
		else:
			self.anchorJd = jd

	def setDefaults(self, group: EventGroupType | None = None) -> None:
		"""Set default date to today's system date."""
		super().setDefaults(group=group)
		self.predicted = False
		self.anchorJd = 0
		self.actualCycle: int | None = None
		self.ovulationOverride: int | None = None
		self.summary = ""  # auto text is generated on demand, not saved
		rule = DateEventRule.getFrom(self)
		if rule is not None:
			rule.date = getSysDate(self.calType)

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSetType:
		"""Return the period days for this occurrence."""
		jd = self.getJd()
		if self.parent is not None:
			periodLength = getattr(self.parent, "periodLength", defaultPeriodLength)
		else:
			periodLength = defaultPeriodLength
		days = {jd + i for i in range(periodLength)}
		return JdOccurSet({d for d in days if startJd <= d < endJd})

	@property
	def autoSummary(self) -> str:
		"""Return the user summary, or translated auto text computed on demand."""
		if self.summary:
			return self.summary
		if self.predicted:
			return _("Predicted Period")
		return _("Period")

	def getIcsData(self, prettyDateTime: bool = False) -> list[tuple[str, str]] | None:
		"""Return iCalendar data for this period occurrence."""
		jd = self.getJd()
		return [
			("DTSTART", ics.getIcsDateByJd(jd, prettyDateTime)),
			("DTEND", ics.getIcsDateByJd(jd + 1, prettyDateTime)),
			("TRANSP", "TRANSPARENT"),
			("CATEGORIES", self.name),  # FIXME
		]

	def setIcsData(self, data: dict[str, str]) -> bool:
		"""Import event data from an iCalendar dictionary."""
		self.setJd(ics.getJdByIcsDate(data["DTSTART"]))
		return True


@classes.event.register
class MenstrualFertileEvent(Event):
	"""A derived event marking one fertile day of a cycle."""

	name = "menstrualFertile"
	desc = _("Fertile Window")
	iconName = "fertile"
	isSingleOccur = True
	isAllDay = True
	requiredRules = []
	supportedRules = []
	_myParams = [
		"anchorJd",  # the cycle start this fertile day belongs to
		"dayJd",  # the fertile day
		"predicted",
	]
	params = Event.params + _myParams
	paramsOrder = Event.paramsOrder + _myParams

	@classmethod
	def getDefaultIcon(cls) -> str:
		return _menstrualIcon(cls.iconName)

	def __bool__(self) -> bool:
		return True

	def setDict(self, data: dict[str, Any]) -> None:
		"""Load event data, ensuring dayJd exists for legacy fertile events."""
		Event.setDict(self, data)
		if not hasattr(self, "dayJd"):
			self.dayJd = 0

	def setDefaults(self, group: EventGroupType | None = None) -> None:
		"""Initialize derived-event fields."""
		super().setDefaults(group=group)
		self.anchorJd = 0
		self.dayJd = 0
		self.predicted = True
		self.summary = ""  # auto text is generated on demand, not saved

	def dayProbability(self) -> float | None:
		"""Return this day's conception probability, or None if not available."""
		parent = self.parent
		if parent is None or not isinstance(parent, MenstrualCycleGroup):
			return None
		if parent.windowMode == "oginoKnaus":
			return None
		ovulation = parent.predictOvulationForCycle(self.anchorJd)
		if ovulation is None:
			return None
		dayJd = getattr(self, "dayJd", self.anchorJd)
		return dayProbabilityRelativeToOvulation(
			ovulation - dayJd,
			includeDayAfterProbability=0.08,
		)

	@property
	def autoSummary(self) -> str:
		"""Return the user summary, or the day-specific probability on demand."""
		if self.summary:
			return self.summary
		probability = self.dayProbability()
		if probability is None:
			return _("Fertile Window")
		return _("Fertile Window ({percent}%)").format(
			percent=_(_percent(probability)),
		)

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSetType:
		"""Return the single fertile day."""
		dayJd = getattr(self, "dayJd", self.anchorJd)
		if startJd <= dayJd < endJd:
			return JdOccurSet({dayJd})
		return JdOccurSet()


@classes.event.register
class MenstrualOvulationEvent(Event):
	"""A derived event marking the estimated ovulation day of one cycle."""

	name = "menstrualOvulation"
	desc = _("Ovulation")
	iconName = "ovulation"
	isSingleOccur = True
	isAllDay = True
	requiredRules = []
	supportedRules = []
	_myParams = [
		"anchorJd",
		"predicted",
	]
	params = Event.params + _myParams
	paramsOrder = Event.paramsOrder + _myParams

	@classmethod
	def getDefaultIcon(cls) -> str:
		return _menstrualIcon(cls.iconName)

	def __bool__(self) -> bool:
		return True

	def setDefaults(self, group: EventGroupType | None = None) -> None:
		"""Initialize derived-event fields."""
		super().setDefaults(group=group)
		self.anchorJd = 0
		self.predicted = True
		self.summary = ""  # auto text is generated on demand, not saved

	@property
	def autoSummary(self) -> str:
		"""Return the user summary, or translated auto text computed on demand."""
		if self.summary:
			return self.summary
		parent = self.parent
		if parent is None:
			return _("Ovulation")
		peak = 0.33 * getattr(parent, "viabilityFactor", 1.0)
		return _("Ovulation ({}%)").format(_(_percent(peak)))

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSetType:
		"""Return the single ovulation day for the anchored cycle."""
		parent = self.parent
		if parent is None or not isinstance(parent, MenstrualCycleGroup):
			return JdOccurSet()
		ovulation = parent.predictOvulationForCycle(self.anchorJd)
		if ovulation is None:
			return JdOccurSet()
		return JdOccurSet(
			{ovulation} if startJd <= ovulation < endJd else set(),
		)


@classes.event.register
class MenstrualObservationEvent(Event):
	"""A daily observation logged by the woman or her partner."""

	name = "menstrualObservation"
	desc = _("Cycle Observation")
	iconName = "menstrual_observation"
	isSingleOccur = True
	requiredRules = ["date"]
	supportedRules = ["date"]
	isAllDay = True
	_myParams = [
		"recordedBy",
		"flow",
		"mucus",
		"bbt",
		"opk",
		"sex",
	]
	params = Event.params + _myParams
	paramsOrder = Event.paramsOrder + _myParams

	@classmethod
	def getDefaultIcon(cls) -> str:
		return _menstrualIcon(cls.iconName)

	def getV4Dict(self) -> dict[str, Any]:
		"""Return v4 format dictionary representation."""
		data = Event.getV4Dict(self)
		data.update({"jd": self.getJd()})
		return data

	def getDate(self) -> tuple[int, int, int] | None:
		"""Return the observation date as (year, month, day)."""
		rule = DateEventRule.getFrom(self)
		if rule is not None:
			return rule.date
		return None

	def setDate(self, year: int, month: int, day: int) -> None:
		"""Set the observation date."""
		rule = DateEventRule.getFrom(self)
		if rule is None:
			raise KeyError("no date rule")
		rule.date = (year, month, day)

	def getJd(self) -> int:
		"""Return the Julian day of the observation."""
		rule = DateEventRule.getFrom(self)
		if rule is not None:
			return rule.getJd()
		return self.getStartJd()

	def setJd(self, jd: int) -> None:
		"""Set the observation date from a Julian day."""
		rule = DateEventRule.getFrom(self)
		if rule is None:
			log.error("MenstrualObservationEvent: setJd: no date rule")
			return
		rule.setJd(jd)

	def setDefaults(self, group: EventGroupType | None = None) -> None:
		"""Set default observation values and today's date."""
		super().setDefaults(group=group)
		self.recordedBy = "woman"  # "woman" | "partner"
		self.flow = "none"  # none | light | medium | heavy
		self.mucus = ""  # dry | sticky | creamy | watery | eggwhite
		self.bbt: float | None = None  # basal body temperature in °C
		self.opk = ""  # negative | positive
		self.sex = False
		self.summary = ""  # auto text is generated on demand, not saved
		rule = DateEventRule.getFrom(self)
		if rule is not None:
			rule.date = getSysDate(self.calType)

	@property
	def autoSummary(self) -> str:
		"""Return the user summary, or translated auto text computed on demand."""
		if self.summary:
			return self.summary
		return _("Cycle Observation")

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSetType:
		"""Return the single observation day."""
		jd = self.getJd()
		return JdOccurSet(
			{jd} if startJd <= jd < endJd else set(),
		)

	def _getAutoDescription(self) -> str:
		"""Auto-generated summary of the recorded observation fields."""
		lines = [
			_("Recorded by: {who}").format(
				who=observationRecordedByLabels.get(self.recordedBy, self.recordedBy),
			),
		]
		if self.flow != "none":
			lines.append(
				_("Flow: {value}").format(
					value=observationFlowLabels.get(self.flow, self.flow),
				),
			)
		if self.mucus:
			lines.append(
				_("Cervical Mucus: {value}").format(
					value=observationMucusLabels.get(self.mucus, self.mucus),
				),
			)
		if self.bbt is not None:
			lines.append(
				_("Basal Body Temperature: {value}°C").format(value=_(self.bbt)),
			)
		if self.opk:
			lines.append(
				_("Ovulation Predictor Kit: {value}").format(
					value=observationOpkLabels.get(self.opk, self.opk),
				),
			)
		if self.sex:
			lines.append(_("Intercourse occurred"))
		return "\n".join(lines)

	@property
	def autoDescription(self) -> str:
		"""Return the user description with the auto-generated summary appended."""
		auto = self._getAutoDescription()
		if not self.description:
			return auto
		return self.description + "\n" + auto

	def getIcsData(self, prettyDateTime: bool = False) -> list[tuple[str, str]] | None:
		"""Return iCalendar data for this observation."""
		jd = self.getJd()
		return [
			("DTSTART", ics.getIcsDateByJd(jd, prettyDateTime)),
			("DTEND", ics.getIcsDateByJd(jd + 1, prettyDateTime)),
			("TRANSP", "TRANSPARENT"),
			("CATEGORIES", self.name),  # FIXME
		]

	def setIcsData(self, data: dict[str, str]) -> bool:
		"""Import event data from an iCalendar dictionary."""
		self.setJd(ics.getJdByIcsDate(data["DTSTART"]))
		return True
