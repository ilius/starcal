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

from collections import defaultdict
from typing import TYPE_CHECKING, cast

from scal3.event_lib.event_base import Event
from scal3.event_lib.group import EventGroup
from scal3.event_lib.menstrual._stats import (
	computeCycleStats,
	dayProbabilityRelativeToOvulation,
	defaultCycleLength,
	defaultLutealPhase,
	defaultPeriodLength,
	fertileWindowDays,
	predictNextPeriod,
	predictOvulation,
)
from scal3.event_lib.register import classes
from scal3.locale_man import tr as _

if TYPE_CHECKING:
	from collections.abc import Sequence

	from scal3.event_lib.menstrual._events import (
		MenstrualFertileEvent,
		MenstrualOvulationEvent,
		MenstrualPeriodEvent,
	)
	from scal3.event_lib.pytypes import EventType


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
		from scal3.event_lib.menstrual._events import (
			MenstrualFertileEvent,
			MenstrualOvulationEvent,
			MenstrualPeriodEvent,
		)

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
