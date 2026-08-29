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

"""
Menstrual cycle calendar: period, fertile window and ovulation tracking.

Domain model (see ``doc/ovulation-cal/proposal.md``):

- Ovulation is estimated to happen ``cycleLength - lutealPhase`` days after the
  first day of the period (the luteal phase is the stable ~14-day part).
- The fertile window is the 6-day span ending on the estimated ovulation day
  (5 days before + ovulation day), following Wilcox 1995.
- The day-specific probability of conception relative to ovulation is taken
  from the Wilcox 1995 study (10% at -5 days up to 33% on ovulation day).

The group maintains recorded period-start events and automatically generates
derived events for the fertile window, the ovulation day, and predicted
future periods, so that each phase shows its own icon in the calendar cells
without changing the cell background color.
"""

from __future__ import annotations

from scal3 import logger

log = logger.get()

from collections import defaultdict
from itertools import pairwise
from typing import TYPE_CHECKING, cast

from scal3 import ics
from scal3.cal_types import getSysDate
from scal3.locale_man import tr as _

from .event_base import Event
from .group import EventGroup
from .occur import JdOccurSet
from .register import classes
from .rules import DateEventRule

if TYPE_CHECKING:
	from collections.abc import Sequence
	from typing import Any

	from scal3.event_lib.pytypes import (
		EventGroupType,
		EventType,
		OccurSetType,
	)

__all__ = [
	"MenstrualCycleGroup",
	"MenstrualFertileEvent",
	"MenstrualObservationEvent",
	"MenstrualOvulationEvent",
	"MenstrualPeriodEvent",
	"computeCycleStats",
	"dayProbabilityRelativeToOvulation",
	"fertileWindowDays",
	"predictNextPeriod",
	"predictOvulation",
]

#: day-specific probability of conception given intercourse on that day,
#: keyed by days before ovulation (Wilcox et al., NEJM 1995;333:1517-21)
WILCOX_DAY_PROBABILITY: dict[int, float] = {
	5: 0.10,
	4: 0.16,
	3: 0.14,
	2: 0.27,
	1: 0.31,
	0: 0.33,
}

#: fertile window begins this many days before the estimated ovulation day
FERTILE_WINDOW_DAYS_BEFORE = 5

#: fertile window extends this many days after the estimated ovulation day
FERTILE_WINDOW_DAYS_AFTER = 1

defaultPeriodLength = 5
defaultLutealPhase = 14
defaultCycleLength = 28

#: translated labels for observation field values
observationRecordedByLabels: dict[str, str] = {
	"woman": _("Woman"),
	"partner": _("Partner"),
}
observationFlowLabels: dict[str, str] = {
	"none": _("None"),
	"light": _("Light"),
	"medium": _("Medium"),
	"heavy": _("Heavy"),
}
observationMucusLabels: dict[str, str] = {
	"": _("Not observed"),
	"dry": _("Dry"),
	"sticky": _("Sticky"),
	"creamy": _("Creamy"),
	"watery": _("Watery"),
	"eggwhite": _("Egg White"),
}
observationOpkLabels: dict[str, str] = {
	"": _("Not tested"),
	"negative": _("Negative"),
	"positive": _("Positive"),
}


def _menstrualIcon(name: str) -> str:
	"""Return the relative SVG icon path for an event type."""
	return f"event/{name}.svg"


def computeCycleStats(
	periodStartJds: Sequence[int],
) -> tuple[int | None, int | None, int | None]:
	"""
	Return (avgCycle, minCycle, maxCycle) in days for sorted period start JDs.

	The average is a recency-weighted mean of the measured cycle lengths.
	Returns (None, None, None) when fewer than two starts are given.
	"""
	if len(periodStartJds) < 2:
		return None, None, None
	lengths = [b - a for a, b in pairwise(periodStartJds)]
	minCycle = min(lengths)
	maxCycle = max(lengths)
	weights = list(range(1, len(lengths) + 1))
	totalWeight = sum(weights)
	avgCycle = round(
		sum(length * weight for length, weight in zip(lengths, weights, strict=True))
		/ totalWeight,
	)
	return avgCycle, minCycle, maxCycle


def predictOvulation(
	periodStartJd: int,
	cycleLength: int,
	lutealPhase: int,
) -> int:
	"""Estimate the ovulation Julian day for a cycle starting at periodStartJd."""
	return periodStartJd + (cycleLength - lutealPhase)


def predictNextPeriod(
	periodStartJd: int,
	cycleLength: int,
) -> int:
	"""Estimate the next period-start Julian day for a given cycle."""
	return periodStartJd + cycleLength


def fertileWindowDays(
	ovulationJd: int | None,
	*,
	mode: str = "fixed",
	periodStartJd: int | None = None,
	minCycle: int | None = None,
	maxCycle: int | None = None,
) -> list[int]:
	"""
	Return the fertile-window Julian days for a cycle.

	fixed mode: the days around the estimated ovulation day (5 days before and
	1 day after), excluding the ovulation day itself which is shown by the
	ovulation event.

	oginoKnaus mode: the classic Knaus-Ogino range derived from the shortest
	and longest recorded cycle lengths (first fertile day = minCycle - 18,
	last fertile day = maxCycle - 11, counted from ``periodStartJd``).
	"""
	if mode == "oginoKnaus":
		assert minCycle is not None
		assert maxCycle is not None
		assert periodStartJd is not None
		first = periodStartJd + (minCycle - 18)
		last = periodStartJd + (maxCycle - 11)
		return list(range(first, last + 1))
	assert ovulationJd is not None
	days = list(
		range(
			ovulationJd - FERTILE_WINDOW_DAYS_BEFORE,
			ovulationJd + FERTILE_WINDOW_DAYS_AFTER + 1,
		),
	)
	# exclude the ovulation day, it is marked by the ovulation event
	days.remove(ovulationJd)
	return days


def dayProbabilityRelativeToOvulation(
	daysBeforeOvulation: int,
	includeDayAfterProbability: float = 0.0,
) -> float:
	"""
	Return the estimated probability of conception given intercourse on a day
	``daysBeforeOvulation`` days before the estimated ovulation day (positive
	values are before ovulation, 0 is ovulation day, negative values are after).
	"""
	if daysBeforeOvulation in WILCOX_DAY_PROBABILITY:
		return WILCOX_DAY_PROBABILITY[daysBeforeOvulation]
	if daysBeforeOvulation == -1:
		return includeDayAfterProbability
	return 0.0


def _percent(value: float) -> int:
	"""Return a whole percent (0-100) for a probability fraction."""
	return round(value * 100)


@classes.group.register
class MenstrualCycleGroup(EventGroup):
	"""Group that tracks one person's menstrual cycle and generates predictions."""

	name = "menstrualCycle"
	desc = _("Menstrual Cycle")
	acceptsEventTypes: Sequence[str] = (
		"menstrualPeriod",
		"menstrualFertile",
		"menstrualOvulation",
		"menstrualObservation",
		"dailyNote",
	)
	canConvertTo: list[str] = []
	_myParams = [
		"personName",
		"cycleLength",
		"cycleLengthAuto",
		"lutealPhase",
		"periodLength",
		"windowMode",
		"minCycle",
		"maxCycle",
		"showPeriodPredict",
		"showFertile",
		"showOvulation",
		"viabilityFactor",
	]
	params = EventGroup.params + _myParams
	paramsOrder = EventGroup.paramsOrder + _myParams

	def __init__(self, ident: int | None = None) -> None:
		super().__init__(ident)
		self.personName = ""
		self.cycleLength = defaultCycleLength
		self.cycleLengthAuto = True
		self.lutealPhase = defaultLutealPhase
		self.periodLength = defaultPeriodLength
		self.windowMode = "fixed"  # "fixed" | "oginoKnaus"
		self.minCycle = 21
		self.maxCycle = 35
		self.showPeriodPredict = True
		self.showFertile = True
		self.showOvulation = True
		self.viabilityFactor = 1.0
		self._syncingDerived = False

	# --------------------------------------- recorded period starts

	def getPeriodStartEvents(self) -> list[EventType]:
		"""Return the recorded (non-predicted) period events."""
		return [
			event
			for event in self
			if event.name == "menstrualPeriod"
			and not getattr(event, "predicted", False)
		]

	def getPeriodStartJds(self) -> list[int]:
		"""Return the sorted Julian days of all recorded period starts."""
		return sorted(event.getJd() for event in self.getPeriodStartEvents())

	def getCycleLength(self) -> int:
		"""Return the cycle length used for predictions."""
		if self.cycleLengthAuto:
			avg, _minCycle, _maxCycle = computeCycleStats(self.getPeriodStartJds())
			if avg is not None:
				return avg
		return self.cycleLength

	def getMinMaxCycle(self) -> tuple[int, int]:
		"""Return (minCycle, maxCycle) from recorded data or the group defaults."""
		_minCycle, minC, maxC = computeCycleStats(self.getPeriodStartJds())
		if minC is None or maxC is None:
			return self.minCycle, self.maxCycle
		return minC, maxC

	def getCurrentCycleStartJd(self, jd: int) -> int | None:
		"""Return the most recent recorded period start on or before jd, if any."""
		for start in reversed(self.getPeriodStartJds()):
			if start <= jd:
				return start
		return None

	def predictOvulationForCycle(self, periodStartJd: int) -> int | None:
		"""Return the ovulation JD for a cycle, honoring a per-cycle override."""
		for event in self.getPeriodStartEvents():
			override = getattr(event, "ovulationOverride", None)
			if event.getJd() == periodStartJd and override is not None:
				return int(override)
		return predictOvulation(
			periodStartJd,
			self.getCycleLength(),
			self.lutealPhase,
		)

	def fertileWindowForCycle(self, periodStartJd: int) -> list[int]:
		"""Return the fertile-window JDs for the cycle starting at periodStartJd."""
		if self.windowMode == "oginoKnaus":
			minCycle, maxCycle = self.getMinMaxCycle()
			return fertileWindowDays(
				None,
				mode="oginoKnaus",
				periodStartJd=periodStartJd,
				minCycle=minCycle,
				maxCycle=maxCycle,
			)
		ovulation = self.predictOvulationForCycle(periodStartJd)
		if ovulation is None:
			return []
		return fertileWindowDays(ovulation)

	def phaseOnDate(self, jd: int) -> str:
		"""
		Return the cycle phase for a day:
		"period", "ovulation", "fertile", "safe" or "unknown".
		"""
		for start in reversed(self.getPeriodStartJds()):
			if start <= jd < start + self.periodLength:
				return "period"
		anchor = self.getCurrentCycleStartJd(jd)
		if anchor is None:
			return "unknown"
		ovulation = self.predictOvulationForCycle(anchor)
		if ovulation is None:
			return "unknown"
		if self.showOvulation and jd == ovulation:
			return "ovulation"
		if self.showFertile and jd in self.fertileWindowForCycle(anchor):
			return "fertile"
		return "safe"

	def probabilityOnDate(
		self,
		jd: int,
	) -> tuple[float | None, str]:
		"""
		Return (probability, kind) for intercourse on the given day.

		The probability is the estimated chance of conception given intercourse
		on that day. ``kind`` is "recorded" when the day belongs to a recorded
		cycle, "predicted" when it belongs to a predicted cycle, or "unknown"
		when no cycle data covers the day.
		"""
		recordedStarts = self.getPeriodStartJds()
		anchor = self.getCycleStartForJd(jd)
		if anchor is None:
			return None, "unknown"
		ovulation = self.predictOvulationForCycle(anchor)
		if ovulation is None:
			return None, "unknown"
		probability = dayProbabilityRelativeToOvulation(
			ovulation - jd,
			includeDayAfterProbability=0.08,
		)
		kind = "recorded" if anchor in recordedStarts else "predicted"
		return probability, kind

	# --------------------------------------- derived (predicted) events

	def getCycleStartForJd(self, jd: int) -> int | None:
		"""Return the most recent cycle anchor (recorded or predicted) for a day."""
		for anchor in reversed(self._anchorCycles()):
			if anchor <= jd:
				return anchor
		return None

	def _anchorCycles(self) -> list[int]:
		"""Return the period-start JDs for which predictions are generated."""
		recordedStarts = self.getPeriodStartJds()
		if not recordedStarts:
			return []
		cycleLength = self.getCycleLength()
		anchors = list(recordedStarts)
		nextStart = predictNextPeriod(recordedStarts[-1], cycleLength)
		while nextStart < self.endJd:
			anchors.append(nextStart)
			nextStart = predictNextPeriod(nextStart, cycleLength)
		return anchors

	def syncDerivedEvents(self) -> None:
		"""Create, update and remove derived events to match recorded periods."""
		if self._syncingDerived:
			return
		self._syncingDerived = True
		try:
			self._syncDerivedEvents()
		finally:
			self._syncingDerived = False

	def _syncDerivedEvents(self) -> None:
		recordedStarts = self.getPeriodStartJds()
		recordedSet = set(recordedStarts)
		# auto-fill the measured cycle length on recorded period events
		changed = False
		prevStart: int | None = None
		for event in self.getPeriodStartEvents():
			if not isinstance(event, MenstrualPeriodEvent):
				continue
			jd = event.getJd()
			if prevStart is not None and event.actualCycle != jd - prevStart:
				event.actualCycle = jd - prevStart
				event.save()
				changed = True
			prevStart = jd

		desired: dict[tuple[str, int], int] = {}  # key -> cycle anchor Jd
		for anchor in self._anchorCycles():
			if anchor not in recordedSet:
				desired[("menstrualPeriod", anchor)] = anchor
			for day in self.fertileWindowForCycle(anchor):
				desired[("menstrualFertile", day)] = anchor
			desired[("menstrualOvulation", anchor)] = anchor

		existing: dict[tuple[str, int], list[int]] = defaultdict(list)
		for event in list(self):
			if isinstance(event, MenstrualFertileEvent):
				key = (event.name, event.dayJd)
			elif isinstance(event, MenstrualOvulationEvent) or (
				isinstance(event, MenstrualPeriodEvent) and event.predicted
			):
				key = (event.name, event.anchorJd)
			else:
				continue
			eid = event.id
			if eid is None:
				continue
			existing[key].append(eid)

		# remove duplicate derived events (e.g. from re-import of an export)
		for key, eids in existing.items():
			if len(eids) > 1:
				for eid in eids[1:]:
					self._removeDerivedEvent(eid)
					changed = True
			existing[key] = eids[:1]

		for key, cycleAnchor in desired.items():
			if not existing.get(key):
				self._createDerivedEvent(key, cycleAnchor)
				changed = True
		for key, eids in list(existing.items()):
			if key not in desired and eids:
				self._removeDerivedEvent(eids[0])
				changed = True

		if changed:
			self.save()

	def _createDerivedEvent(
		self,
		key: tuple[str, int],
		cycleAnchor: int,
	) -> EventType:
		eventType, jd = key
		event = self.create(eventType)
		event.fs = self.fs
		if eventType == "menstrualFertile":
			fertile = cast("MenstrualFertileEvent", event)
			fertile.anchorJd = cycleAnchor
			fertile.dayJd = jd
		elif eventType == "menstrualPeriod":
			period = cast("MenstrualPeriodEvent", event)
			period.anchorJd = jd
			period.predicted = True
			if "date" in period.rulesDict:
				del period.rulesDict["date"]
		else:
			ovulation = cast("MenstrualOvulationEvent", event)
			ovulation.anchorJd = jd
		event.setId()
		event.save()
		assert event.id is not None
		self.idList.append(event.id)
		event.parent = self
		self._setToCache(event)
		return event

	def _removeDerivedEvent(self, eid: int) -> None:
		self.idList.remove(eid)
		self.removeFromCache(eid)
		eventFile = Event.getFile(eid)
		if self.fs.isfile(eventFile):
			self.fs.removeFile(eventFile)

	def updateOccurrence(self) -> None:
		"""Rebuild occurrences, first keeping derived events in sync."""
		self.syncDerivedEvents()
		EventGroup.updateOccurrence(self)

	def updateOccurrenceEvent(self, event: EventType) -> None:
		"""Re-sync derived events whenever a recorded period changes."""
		if event.name == "menstrualPeriod" and not getattr(
			event,
			"predicted",
			False,
		):
			self.syncDerivedEvents()
			if self.enable:
				self.updateOccurrence()
			return
		EventGroup.updateOccurrenceEvent(self, event)

	def postAdd(self, event: EventType) -> None:
		"""Deduplicate derived events when one is added (e.g. during import)."""
		EventGroup.postAdd(self, event)
		if event.name in ("menstrualFertile", "menstrualOvulation") or (
			event.name == "menstrualPeriod" and getattr(event, "predicted", False)
		):
			self.syncDerivedEvents()
			if self.enable:
				self.updateOccurrence()

	def remove(self, event: EventType) -> int:
		"""Remove an event, re-syncing derived events for period starts."""
		result = EventGroup.remove(self, event)
		if event.name == "menstrualPeriod" and not getattr(
			event,
			"predicted",
			False,
		):
			self.syncDerivedEvents()
			if self.enable:
				self.updateOccurrence()
		return result


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

	def getSummary(self) -> str:
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

	def getSummary(self) -> str:
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

	def getSummary(self) -> str:
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

	def getSummary(self) -> str:
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

	def getAutoDescription(self) -> str:
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

	def getDescription(self) -> str:
		"""Return the user description with the auto-generated summary appended."""
		auto = self.getAutoDescription()
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
