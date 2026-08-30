from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, cast

from scal3 import event_lib
from scal3.cal_types import GREGORIAN, to_jd
from scal3.event_lib.handler import Handler
from scal3.event_lib.menstrual import (
	MenstrualCycleGroup,
	MenstrualFertileEvent,
	MenstrualObservationEvent,
	MenstrualOvulationEvent,
	MenstrualPeriodEvent,
	computeCycleStats,
	dayProbabilityRelativeToOvulation,
	fertileWindowDays,
	predictNextPeriod,
	predictOvulation,
)

if TYPE_CHECKING:
	from scal3.event_lib.occur import JdOccurSet
	from scal3.filesystem import FileSystem


def jd(year: int, month: int, day: int) -> int:
	"""Return the Gregorian Julian day for the given date."""
	return to_jd(year, month, day, GREGORIAN)


def createMenstrualGroup(fs: FileSystem) -> MenstrualCycleGroup:
	"""Create a fresh menstrual cycle group attached to the handler."""
	handler = Handler()
	handler.init(fs)
	group = cast(
		"MenstrualCycleGroup",
		handler.groups.create("menstrualCycle"),
	)
	group.fs = fs
	group.setTitle("Test Cycle")
	group.setRandomColor()
	group.endJd = jd(2026, 1, 1)  # keep the prediction horizon small
	group.save()
	handler.groups.append(group)
	group.updateOccurrence()
	return group


def addPeriod(group: MenstrualCycleGroup, startJd: int) -> None:
	"""Create, append and save a recorded period-start event."""
	event = cast("MenstrualPeriodEvent", group.create("menstrualPeriod"))
	event.setJd(startJd)
	event.setId()
	assert event.id is not None
	event.save()
	group.append(event)


# --------------------------------------- pure calculation functions


def test_compute_cycle_stats() -> None:
	assert computeCycleStats([100, 128, 156]) == (28, 28, 28)
	# lengths 30 and 27, recency-weighted average = (30*1 + 27*2) / 3 = 28
	assert computeCycleStats([100, 130, 157]) == (28, 27, 30)
	assert computeCycleStats([100]) == (None, None, None)
	assert computeCycleStats([]) == (None, None, None)


def test_predict_ovulation_and_next_period() -> None:
	assert predictOvulation(1000, 28, 14) == 1014
	assert predictOvulation(1000, 30, 14) == 1016
	assert predictOvulation(1000, 28, 12) == 1016
	assert predictNextPeriod(1000, 28) == 1028


def test_fertile_window_fixed() -> None:
	# 5 days before, 1 day after, excluding the ovulation day itself
	assert fertileWindowDays(1014) == [1009, 1010, 1011, 1012, 1013, 1015]


def test_fertile_window_ogino_knaus() -> None:
	days = fertileWindowDays(
		None,
		mode="oginoKnaus",
		periodStartJd=1000,
		minCycle=28,
		maxCycle=32,
	)
	# first = minCycle - 18 = day 10, last = maxCycle - 11 = day 21
	assert days == list(range(1010, 1022))


def test_day_probability_table() -> None:
	assert dayProbabilityRelativeToOvulation(0) == 0.33
	assert dayProbabilityRelativeToOvulation(1) == 0.31
	assert dayProbabilityRelativeToOvulation(2) == 0.27
	assert dayProbabilityRelativeToOvulation(3) == 0.14
	assert dayProbabilityRelativeToOvulation(4) == 0.16
	assert dayProbabilityRelativeToOvulation(5) == 0.10
	assert dayProbabilityRelativeToOvulation(6) == 0.0
	assert dayProbabilityRelativeToOvulation(-1) == 0.0
	assert (
		dayProbabilityRelativeToOvulation(
			-1,
			includeDayAfterProbability=0.08,
		)
		== 0.08
	)
	assert dayProbabilityRelativeToOvulation(-3) == 0.0


# --------------------------------------- group behavior


def test_group_generates_predictions(fs: FileSystem) -> None:
	group = createMenstrualGroup(fs)
	assert group.getPeriodStartJds() == []

	s1, s2, s3 = jd(2025, 6, 1), jd(2025, 6, 29), jd(2025, 7, 27)
	addPeriod(group, s1)
	addPeriod(group, s2)
	addPeriod(group, s3)

	assert group.getPeriodStartJds() == [s1, s2, s3]
	assert group.getCycleLength() == 28
	assert group.getMinMaxCycle() == (28, 28)

	# predicted (derived) events exist for each cycle
	names = Counter(event.name for event in group)
	assert names["menstrualPeriod"] >= 3
	assert names["menstrualFertile"] >= 3
	assert names["menstrualOvulation"] >= 3

	# predicted period events must not be counted as recorded starts
	recorded = group.getPeriodStartEvents()
	assert len(recorded) == 3

	ovulation = group.predictOvulationForCycle(s1)
	assert ovulation == s1 + 14

	prob, kind = group.probabilityOnDate(ovulation)
	assert prob == 0.33
	assert kind == "recorded"
	prob, _kind = group.probabilityOnDate(ovulation - 5)
	assert prob == 0.10
	prob, _kind = group.probabilityOnDate(ovulation + 1)
	assert prob == 0.08

	assert group.phaseOnDate(s1) == "period"
	assert group.phaseOnDate(ovulation) == "ovulation"
	assert group.phaseOnDate(ovulation - 2) == "fertile"
	assert group.phaseOnDate(s1 - 1) == "unknown"


def test_ovulation_override(fs: FileSystem) -> None:
	group = createMenstrualGroup(fs)
	s1 = jd(2025, 6, 1)
	addPeriod(group, s1)

	event = cast("MenstrualPeriodEvent", group.getPeriodStartEvents()[0])
	event.ovulationOverride = s1 + 16
	event.save()
	group.updateOccurrence()

	assert group.predictOvulationForCycle(s1) == s1 + 16
	assert group.phaseOnDate(s1 + 16) == "ovulation"
	prob, _kind = group.probabilityOnDate(s1 + 16)
	assert prob == 0.33


def test_ogino_knaus_window(fs: FileSystem) -> None:
	group = createMenstrualGroup(fs)
	group.windowMode = "oginoKnaus"
	group.minCycle = 27
	group.maxCycle = 31
	s1 = jd(2025, 6, 1)
	addPeriod(group, s1)
	group.updateOccurrence()

	window = group.fertileWindowForCycle(s1)
	assert window == list(range(s1 + (27 - 18), s1 + (31 - 11) + 1))
	assert group.phaseOnDate(s1 + 10) == "fertile"


def test_remove_period_resyncs(fs: FileSystem) -> None:
	group = createMenstrualGroup(fs)
	addPeriod(group, jd(2025, 6, 1))
	addPeriod(group, jd(2025, 6, 29))

	recorded = group.getPeriodStartEvents()
	assert len(recorded) == 2
	group.remove(recorded[1])

	assert group.getPeriodStartJds() == [jd(2025, 6, 1)]
	assert len(group.getPeriodStartEvents()) == 1
	# the second start is now predicted
	predictedJds = {
		e.getJd()
		for e in group
		if e.name == "menstrualPeriod" and getattr(e, "predicted", False)
	}
	assert jd(2025, 6, 29) in predictedJds


def test_group_params_roundtrip(fs: FileSystem) -> None:
	group = createMenstrualGroup(fs)
	group.cycleLength = 30
	group.cycleLengthAuto = False
	group.lutealPhase = 13
	group.periodLength = 6
	group.windowMode = "oginoKnaus"
	group.viabilityFactor = 0.37
	group.personName = "Ada"
	group.save()

	assert group.id is not None
	loaded = cast("MenstrualCycleGroup", MenstrualCycleGroup.load(group.id, fs=fs))
	assert loaded is not None
	assert loaded.cycleLength == 30
	assert loaded.cycleLengthAuto is False
	assert loaded.lutealPhase == 13
	assert loaded.periodLength == 6
	assert loaded.windowMode == "oginoKnaus"
	assert loaded.viabilityFactor == 0.37
	assert loaded.personName == "Ada"


# --------------------------------------- event behavior


def test_period_event_occurrence(fs: FileSystem) -> None:
	group = createMenstrualGroup(fs)
	group.periodLength = 5
	event = cast("MenstrualPeriodEvent", group.create("menstrualPeriod"))
	event.setJd(jd(2025, 6, 1))
	event.setId()
	event.save()
	group.append(event)

	occur = cast(
		"JdOccurSet",
		event.calcEventOccurrenceIn(jd(2025, 6, 1), jd(2025, 7, 1)),
	)
	assert len(occur) == 5
	assert occur.getStartJd() == jd(2025, 6, 1)
	assert occur.getEndJd() == jd(2025, 6, 6)

	# outside the group range the same set is returned (events do not clamp)
	assert event.getJd() == jd(2025, 6, 1)


def test_period_event_roundtrip(fs: FileSystem) -> None:
	group = createMenstrualGroup(fs)
	event = cast("MenstrualPeriodEvent", group.create("menstrualPeriod"))
	event.setDict(
		{
			"summary": "period",
			"calType": "gregorian",
			"rules": [("date", "2025/06/01")],
			"actualCycle": 27,
			"ovulationOverride": jd(2025, 6, 16),
		},
	)
	assert event.getJd() == jd(2025, 6, 1)
	assert event.actualCycle == 27
	assert event.ovulationOverride == jd(2025, 6, 16)

	ordered = event.getDictOrdered()
	reimported = MenstrualPeriodEvent(parent=group)
	reimported.setDict(ordered)
	assert reimported.autoSummary == event.autoSummary
	assert reimported.actualCycle == 27
	assert reimported.ovulationOverride == jd(2025, 6, 16)
	assert reimported.getJd() == jd(2025, 6, 1)


def test_observation_event_roundtrip(fs: FileSystem) -> None:
	group = createMenstrualGroup(fs)
	event = cast("MenstrualObservationEvent", group.create("menstrualObservation"))
	event.setDict(
		{
			"summary": "obs",
			"calType": "gregorian",
			"rules": [("date", "2025/06/05")],
			"recordedBy": "partner",
			"flow": "heavy",
			"mucus": "eggwhite",
			"bbt": 36.6,
			"opk": "positive",
			"sex": True,
		},
	)
	assert event.recordedBy == "partner"
	assert event.flow == "heavy"
	assert event.mucus == "eggwhite"
	assert event.bbt == 36.6
	assert event.opk == "positive"
	assert event.sex is True
	assert event.getJd() == jd(2025, 6, 5)

	occur = event.calcEventOccurrenceIn(jd(2025, 6, 1), jd(2025, 7, 1))
	assert occur.getStartJd() == jd(2025, 6, 5)

	ordered = event.getDictOrdered()
	reimported = MenstrualObservationEvent(parent=group)
	reimported.setDict(ordered)
	assert reimported.recordedBy == "partner"
	assert reimported.mucus == "eggwhite"
	assert reimported.bbt == 36.6
	assert reimported.sex is True


def test_observation_auto_description(fs: FileSystem) -> None:
	group = createMenstrualGroup(fs)
	event = cast("MenstrualObservationEvent", group.create("menstrualObservation"))
	event.setDict(
		{
			"summary": "obs",
			"calType": "gregorian",
			"rules": [("date", "2025/06/05")],
			"description": "cramps in the evening",
			"recordedBy": "partner",
			"flow": "heavy",
			"mucus": "eggwhite",
			"bbt": 36.6,
			"opk": "positive",
			"sex": True,
		},
	)
	auto = event.getAutoDescription()
	for field in ("Recorded by", "Flow", "Cervical Mucus", "Temperature", "Kit"):
		assert field in auto
	assert "36.6" in auto

	description = event.getDescription()
	assert description.startswith("cramps in the evening")
	assert auto in description
	# the stored description must remain the raw user input
	assert event.description == "cramps in the evening"

	text = event.getText()
	assert "cramps in the evening" in text
	assert "Recorded by" in text


def test_auto_summaries_on_demand(fs: FileSystem) -> None:
	"""Auto summaries are computed/translated on demand, not persisted."""
	group = createMenstrualGroup(fs)
	s1 = jd(2025, 6, 1)
	addPeriod(group, s1)
	group.updateOccurrence()

	derived = [
		e
		for e in group
		if e.name in ("menstrualFertile", "menstrualOvulation")
		or (e.name == "menstrualPeriod" and getattr(e, "predicted", False))
	]
	assert derived
	for event in derived:
		assert event.summary == ""  # nothing auto-generated is stored
		assert event.autoSummary != ""  # translated text on demand
		assert event.getDict()["summary"] == ""

	# a user-provided summary overrides the auto text and is persisted
	fertile = next(e for e in group if e.name == "menstrualFertile")
	fertile.summary = "my own text"
	assert fertile.autoSummary == "my own text"
	assert fertile.getDict()["summary"] == "my own text"

	# recorded periods also show translated text on demand
	period = next(
		e
		for e in group
		if e.name == "menstrualPeriod" and not getattr(e, "predicted", False)
	)
	assert period.summary == ""
	assert period.autoSummary != ""


def test_daily_note_accepted_and_ignored(fs: FileSystem) -> None:
	"""DailyNote events are accepted by the group but ignored in predictions."""
	group = createMenstrualGroup(fs)
	s1 = jd(2025, 6, 1)
	addPeriod(group, s1)

	note = group.create("dailyNote")
	note.setJd(s1 + 10)
	note.setId()
	assert note.id is not None
	note.save()
	group.append(note)

	assert group.checkEventToAdd(note)
	# the note does not affect recorded starts or predictions
	assert group.getPeriodStartJds() == [s1]
	assert group.getCycleLength() == 28
	assert group.predictOvulationForCycle(s1) == s1 + 14
	assert group.phaseOnDate(s1 + 10) != "period"

	# the note still occurs normally
	occur = note.calcEventOccurrenceIn(jd(2025, 6, 1), jd(2025, 7, 1))
	assert occur.getStartJd() == s1 + 10


def test_fertile_day_specific_summary(fs: FileSystem) -> None:
	"""Fertile events are per-day, show that day's probability, and skip ovulation."""
	group = createMenstrualGroup(fs)
	s1 = jd(2025, 6, 1)
	addPeriod(group, s1)
	group.updateOccurrence()
	ovulation = group.predictOvulationForCycle(s1)
	assert ovulation == s1 + 14

	byDay: dict[int, MenstrualFertileEvent] = {}
	for event in group:
		if isinstance(event, MenstrualFertileEvent):
			byDay[event.dayJd] = event
	# the ovulation day itself has no fertile event (it has its own event)
	assert ovulation not in byDay
	assert byDay[ovulation - 1].dayProbability() == 0.31
	assert byDay[ovulation - 2].dayProbability() == 0.27
	assert byDay[ovulation - 5].dayProbability() == 0.10
	assert byDay[ovulation + 1].dayProbability() == 0.08

	peakSummary = byDay[ovulation - 1].autoSummary
	assert peakSummary != byDay[ovulation - 2].autoSummary
	assert peakSummary != byDay[ovulation - 5].autoSummary
	assert peakSummary != ""
	# computed on demand, not stored
	assert byDay[ovulation - 1].summary == ""
	# each fertile day is its own single-day event
	occur = cast(
		"JdOccurSet",
		byDay[ovulation - 1].calcEventOccurrenceIn(s1, s1 + 40),
	)
	assert occur.getStartJd() == ovulation - 1
	assert len(occur) == 1


def test_legacy_fertile_event_without_dayjd(fs: FileSystem) -> None:
	"""Fertile events saved before dayJd existed must not crash the sync."""
	group = createMenstrualGroup(fs)
	s1 = jd(2025, 6, 1)
	addPeriod(group, s1)
	group.updateOccurrence()

	# simulate an old event file that never had the dayJd attribute
	legacy = MenstrualFertileEvent()
	assert not hasattr(legacy, "dayJd")
	legacy.setDict(
		{
			"summary": "",
			"calType": "gregorian",
			"anchorJd": s1,
			"predicted": True,
		},
	)
	legacy.setId()
	assert legacy.id is not None
	legacy.fs = fs
	legacy.save()
	group.append(legacy)

	# re-sync must not crash and must regenerate proper fertile events
	group.syncDerivedEvents()
	group.updateOccurrence()
	fertiles = [e for e in group if e.name == "menstrualFertile"]
	assert fertiles
	for event in fertiles:
		assert getattr(event, "dayJd", 0) != 0


def test_derived_events_types_registered() -> None:
	assert MenstrualPeriodEvent.name == "menstrualPeriod"
	assert MenstrualFertileEvent.name == "menstrualFertile"
	assert MenstrualOvulationEvent.name == "menstrualOvulation"
	assert MenstrualObservationEvent.name == "menstrualObservation"
	for name in (
		"menstrualPeriod",
		"menstrualFertile",
		"menstrualOvulation",
		"menstrualObservation",
	):
		assert name in event_lib.classes.event.byName
	assert "menstrualCycle" in event_lib.classes.group.byName


def test_sample_data_importable(fs: FileSystem) -> None:
	"""A menstrual sample group must round-trip through export and import."""
	group = createMenstrualGroup(fs)
	for startJd in (
		jd(2025, 6, 1),
		jd(2025, 6, 29),
		jd(2025, 7, 27),
	):
		addPeriod(group, startJd)
	group.updateOccurrence()

	exported = group.exportData()
	assert exported["type"] == "menstrualCycle"
	# derived events are regenerated on import, so exclude them here
	exported["events"] = [
		e
		for e in exported["events"]
		if e["type"] == "menstrualObservation"
		or (e["type"] == "menstrualPeriod" and not e.get("predicted"))
	]

	handler = Handler()
	handler.init(fs)
	res = handler.groups.importData(
		{
			"groups": [exported],
		},
	)
	assert res.newGroupIds
	gid = next(iter(res.newGroupIds))
	imported = cast("MenstrualCycleGroup", handler.groups[gid])
	assert imported.getPeriodStartJds() == group.getPeriodStartJds()
	names = Counter(event.name for event in imported)
	assert names["menstrualFertile"] >= 3
	assert names["menstrualOvulation"] >= 3
