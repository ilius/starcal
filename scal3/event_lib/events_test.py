from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from scal3 import event_lib
from scal3.cal_types import GREGORIAN, to_jd
from scal3.event_lib.common import eventTextSep
from scal3.event_lib.event_base import Event
from scal3.event_lib.events import CustomEvent
from scal3.event_lib.handler import Handler
from scal3.event_lib.large_scale import LargeScaleEvent
from scal3.event_lib.lifetime import LifetimeEvent
from scal3.event_lib.monthly import MonthlyEvent
from scal3.event_lib.note import DailyNoteEvent
from scal3.event_lib.objects import iterObjectFiles
from scal3.event_lib.task import AllDayTaskEvent, TaskEvent
from scal3.event_lib.university import UniversityClassEvent, UniversityExamEvent
from scal3.event_lib.weekly import WeeklyEvent
from scal3.event_lib.yearly import YearlyEvent

if TYPE_CHECKING:
	from scal3.event_lib.pytypes import EventGroupType, EventType
	from scal3.filesystem import FileSystem


def jd(year: int, month: int, day: int) -> int:
	"""Return the Gregorian Julian day for the given date."""
	return to_jd(year, month, day, GREGORIAN)


def createEvent(fs: FileSystem, eventType: str) -> Event:
	"""Create a fresh event of the given type attached to the default group."""
	handler = Handler()
	handler.init(fs)
	return cast("Event", handler.groups.byIndex(0).create(eventType))


def createSavedEvent(
	fs: FileSystem,
	eventType: str,
	**data: object,
) -> tuple[Event, EventGroupType]:
	"""Create, configure, append and save an event, returning (event, group)."""
	handler = Handler()
	handler.init(fs)
	group = handler.groups.byIndex(2)
	event = cast("Event", group.create(eventType))
	event.setDict(data)
	event.setId()
	assert event.id is not None
	group.append(event)
	event.save()
	group.save()
	return event, group


def assertDictAttributes(
	event: EventType,
	summary: str = "team lunch",
	description: str = "at noon",
) -> None:
	"""Check the attributes populated by setDict."""
	assert event.summary == summary
	assert event.description == description
	assert event.calType == GREGORIAN
	assert summary in event.getSummary()
	assert description in event.getDescription()
	assert summary in event.getText()


def assertExportRoundtrip(event: EventType) -> None:
	"""Export via getDictOrdered and reimport into a fresh event."""
	ordered = event.getDictOrdered()
	assert ordered["summary"] == event.summary
	assert ordered["description"] == event.description
	assert ordered["calType"] == "gregorian"

	reimported = event.__class__(parent=event.parent)
	reimported.setDict(ordered)
	assert reimported.summary == event.summary
	assert reimported.description == event.description


def test_legacy_event_set_defaults_override(fs: FileSystem) -> None:
	"""Existing event subclasses can still override the public defaults hook."""

	class LegacyEvent(Event):
		params = Event.params + ["legacyDefault"]

		def setDefaults(self, group: EventGroupType | None = None) -> None:
			"""Initialize a persisted plugin field through the legacy hook."""
			super().setDefaults(group=group)
			self.legacyDefault = "initialized"

	handler = Handler()
	handler.init(fs)
	group = handler.groups.byIndex(0)
	event = LegacyEvent(parent=group)
	assert event.legacyDefault == "initialized"
	assert event.getDict()["legacyDefault"] == "initialized"


def test_custom_event(fs: FileSystem) -> None:
	"""CustomEvent: setDict, occurrence, export and ICS import refusal."""
	event = createEvent(fs, "custom")
	assert isinstance(event, CustomEvent)
	event.setDict(
		{
			"summary": "team lunch",
			"description": "at noon",
			"calType": "gregorian",
			"rules": [("date", "2030/05/15")],
		},
	)
	assertDictAttributes(event)
	assert event.isAllDay is False
	assert event.getRule("date") is not None

	v4 = event.getV4Dict()
	assert v4["summary"] == "team lunch"
	assert v4["calType"] == "gregorian"
	assertExportRoundtrip(event)

	occur = event.calcEventOccurrenceIn(jd(2030, 5, 1), jd(2030, 6, 1))
	assert occur.getStartJd() == jd(2030, 5, 15)

	assert event.setIcsData({}) is False


def test_task_event(fs: FileSystem) -> None:
	"""TaskEvent: start/end rules, occurrence and ICS import."""
	event = createEvent(fs, "task")
	assert isinstance(event, TaskEvent)
	event.setDict(
		{
			"summary": "team lunch",
			"description": "at noon",
			"calType": "gregorian",
			"rules": [
				("start", {"date": "2030/05/15", "time": "09:00:00"}),
				("end", {"date": "2030/05/15", "time": "10:00:00"}),
			],
		},
	)
	assertDictAttributes(event)
	assert event.isAllDay is False
	assert event.getStart() == ((2030, 5, 15), (9, 0, 0))
	assert event.getEnd() == ("date", ((2030, 5, 15), (10, 0, 0)))
	assertExportRoundtrip(event)

	occur = event.calcEventOccurrenceIn(jd(2030, 5, 15), jd(2030, 5, 16))
	assert occur.getStartJd() == jd(2030, 5, 15)

	assert (
		event.setIcsData(
			{
				"DTSTART": "20300516T090000",
				"DTEND": "20300516T100000",
			},
		)
		is True
	)
	assert event.getStart() == ((2030, 5, 16), (9, 0, 0))


def test_allday_task_event(fs: FileSystem) -> None:
	"""AllDayTaskEvent: all-day duration end, occurrence and ICS import."""
	event = createEvent(fs, "allDayTask")
	assert isinstance(event, AllDayTaskEvent)
	event.setDict(
		{
			"summary": "team lunch",
			"description": "at noon",
			"calType": "gregorian",
			"rules": [
				("start", {"date": "2030/05/15", "time": "00:00:00"}),
				("duration", "1 day"),
			],
		},
	)
	assertDictAttributes(event)
	assert event.isAllDay is True
	assert event.getEnd() == ("duration", 1)
	assert event.getStartJd() == jd(2030, 5, 15)
	assert event.getEndJd() == jd(2030, 5, 16)
	assertExportRoundtrip(event)

	occur = event.calcEventOccurrenceIn(jd(2030, 5, 15), jd(2030, 5, 18))
	assert occur.getStartJd() == jd(2030, 5, 15)

	icsData = event.getIcsData()
	assert icsData is not None
	assert icsData[0] == ("DTSTART", "20300515")
	assert event.setIcsData({"DTSTART": "20300516", "DTEND": "20300518"}) is True
	assert event.getStartJd() == jd(2030, 5, 16)
	assert event.getEndJd() == jd(2030, 5, 18)


def test_daily_note_event(fs: FileSystem) -> None:
	"""DailyNoteEvent: single-day note, occurrence and ICS import."""
	event = createEvent(fs, "dailyNote")
	assert isinstance(event, DailyNoteEvent)
	event.setDict(
		{
			"summary": "team lunch",
			"description": "at noon",
			"calType": "gregorian",
			"rules": [("date", "2030/05/15")],
		},
	)
	assertDictAttributes(event)
	assert event.isAllDay is True
	assert event.getDate() == (2030, 5, 15)
	assert event.getJd() == jd(2030, 5, 15)
	assertExportRoundtrip(event)

	occur = event.calcEventOccurrenceIn(jd(2030, 5, 1), jd(2030, 6, 1))
	assert occur.getStartJd() == jd(2030, 5, 15)

	assert event.setIcsData({"DTSTART": "20300516"}) is True
	assert event.getJd() == jd(2030, 5, 16)


def test_monthly_event(fs: FileSystem) -> None:
	"""MonthlyEvent: repeats on a day of month with a daily time range."""
	event = createEvent(fs, "monthly")
	assert isinstance(event, MonthlyEvent)
	event.setDict(
		{
			"summary": "team lunch",
			"description": "at noon",
			"calType": "gregorian",
			"rules": [
				("start", {"date": "2030/01/01", "time": "00:00:00"}),
				("end", {"date": "2030/12/31", "time": "00:00:00"}),
				("day", [5]),
				("dayTimeRange", ("09:00:00", "10:00:00")),
			],
		},
	)
	assertDictAttributes(event)
	assert event.isAllDay is False
	assert event.getDay() == 5
	assertExportRoundtrip(event)

	occur = event.calcEventOccurrenceIn(jd(2030, 1, 1), jd(2030, 4, 1))
	assert len(occur.getTimeRangeList()) == 3  # Jan, Feb, Mar

	assert event.setIcsData({}) is False


def test_weekly_event(fs: FileSystem) -> None:
	"""WeeklyEvent: repeats weekly within a cycle with a time range."""
	event = createEvent(fs, "weekly")
	assert isinstance(event, WeeklyEvent)
	event.setDict(
		{
			"summary": "team lunch",
			"description": "at noon",
			"calType": "gregorian",
			"rules": [
				("start", {"date": "2030/01/01", "time": "09:00:00"}),
				("end", {"date": "2030/02/28", "time": "09:00:00"}),
				("cycleWeeks", 1),
				("dayTimeRange", ("09:00:00", "10:00:00")),
			],
		},
	)
	assertDictAttributes(event)
	assert event.isAllDay is False
	assert event.getRule("cycleWeeks") is not None
	assertExportRoundtrip(event)

	occur = event.calcEventOccurrenceIn(jd(2030, 1, 1), jd(2030, 2, 28))
	assert len(occur.getTimeRangeList()) == 9  # weekly through the 8-week cycle

	assert event.setIcsData({}) is False


def test_yearly_event(fs: FileSystem) -> None:
	"""YearlyEvent: repeats on a month/day with an ICS recurrence rule."""
	event = createEvent(fs, "yearly")
	assert isinstance(event, YearlyEvent)
	event.setDict(
		{
			"summary": "birthday",
			"description": "fun day",
			"calType": "gregorian",
			"rules": [("month", [5]), ("day", [15])],
		},
	)
	assertDictAttributes(event, summary="birthday", description="fun day")
	assert event.isAllDay is True
	assert event.getMonth() == 5
	assert event.getDay() == 15
	assertExportRoundtrip(event)

	occur = event.calcEventOccurrenceIn(jd(2030, 1, 1), jd(2031, 1, 1))
	assert occur.getStartJd() == jd(2030, 5, 15)

	assert (
		event.setIcsData(
			{"RRULE": "FREQ=YEARLY;BYMONTH=6;BYMONTHDAY=9"},
		)
		is True
	)
	assert event.getMonth() == 6
	assert event.getDay() == 9


def test_lifetime_event(fs: FileSystem) -> None:
	"""LifetimeEvent: all-day interval from start to end rule."""
	event = createEvent(fs, "lifetime")
	assert isinstance(event, LifetimeEvent)
	event.setDict(
		{
			"summary": "job",
			"description": "long gig",
			"calType": "gregorian",
			"rules": [
				("start", {"date": "2030/01/01", "time": "00:00:00"}),
				("end", {"date": "2030/12/31", "time": "00:00:00"}),
			],
		},
	)
	assertDictAttributes(event, summary="job", description="long gig")
	assert event.isAllDay is True
	assert event.getStartJd() == jd(2030, 1, 1)
	assert event.getEndJd() == jd(2030, 12, 31)
	assertExportRoundtrip(event)

	occur = event.calcEventOccurrenceIn(jd(2030, 1, 1), jd(2031, 1, 1))
	assert occur.getStartJd() == jd(2030, 1, 1)
	assert occur.getEndJd() == jd(2030, 12, 31)

	assert event.setIcsData({}) is False


def test_large_scale_event(fs: FileSystem) -> None:
	"""LargeScaleEvent: spans years with scale params and an interval occurrence."""
	event = createEvent(fs, "largeScale")
	assert isinstance(event, LargeScaleEvent)
	event.setDict(
		{
			"summary": "era",
			"description": "long time",
			"calType": "gregorian",
			"scale": 1,
			"start": 2030,
			"end": 5,
			"endRel": True,
		},
	)
	assertDictAttributes(event, summary="era", description="long time")
	assert event.isAllDay is True
	assert event.scale == 1
	assert event.start == 2030
	assert event.getEnd() == 2035
	assert event.getJd() == jd(2030, 1, 1)
	assertExportRoundtrip(event)

	occur = event.calcEventOccurrenceIn(jd(2029, 1, 1), jd(2036, 1, 1))
	assert len(occur.getTimeRangeList()) == 1
	assert occur.getStartJd() == jd(2030, 1, 1)

	assert event.setIcsData({}) is False


def test_university_class_event(fs: FileSystem) -> None:
	"""UniversityClassEvent: weekly weekday meetings in a time range."""
	event = createEvent(fs, "universityClass")
	assert isinstance(event, UniversityClassEvent)
	event.setDict(
		{
			"summary": "math",
			"description": "advanced",
			"calType": "gregorian",
			"courseId": 1,
			"rules": [
				("weekNumMode", "any"),
				("weekDay", [1]),
				("dayTimeRange", ("09:00:00", "10:00:00")),
			],
		},
	)
	assertDictAttributes(event, summary="math", description="advanced")
	assert event.isAllDay is False
	assert event.courseId == 1
	for ruleName in ("weekNumMode", "weekDay", "dayTimeRange"):
		assert event.getRule(ruleName) is not None
	assertExportRoundtrip(event)

	occur = event.calcEventOccurrenceIn(jd(2030, 1, 1), jd(2030, 2, 1))
	assert len(occur.getTimeRangeList()) >= 4  # Mondays in January

	assert event.setIcsData({}) is False


def test_university_exam_event(fs: FileSystem) -> None:
	"""UniversityExamEvent: dated exam within a daily time range."""
	event = createEvent(fs, "universityExam")
	assert isinstance(event, UniversityExamEvent)
	event.setDict(
		{
			"summary": "final",
			"description": "written",
			"calType": "gregorian",
			"courseId": 1,
			"rules": [
				("date", "2030/05/15"),
				("dayTimeRange", ("09:00:00", "11:00:00")),
			],
		},
	)
	assertDictAttributes(event, summary="final", description="written")
	assert event.isAllDay is False
	assert event.courseId == 1
	assert event.getJd() == jd(2030, 5, 15)
	assertExportRoundtrip(event)

	occur = event.calcEventOccurrenceIn(jd(2030, 5, 1), jd(2030, 6, 1))
	assert occur.getStartJd() == jd(2030, 5, 15)

	assert event.setIcsData({"DTSTART": "20300520"}) is True
	assert event.getJd() == jd(2030, 5, 20)


def test_event_save_records_history(fs: FileSystem) -> None:
	"""Changing an event between saves adds history entries."""
	handler = Handler()
	handler.init(fs)
	group = handler.groups.byIndex(0)

	event = group.create("custom")
	event.summary = "v1"
	event.setId()
	group.append(event)
	event.save()

	event.summary = "v2"
	event.save()

	history = event.loadHistory()
	assert len(history) == 2
	assert history[0][1] != history[1][1]


def test_remove_unused_objects_keeps_referenced(fs: FileSystem) -> None:
	"""RemoveUnusedObjects keeps object blobs referenced by saved events."""
	handler = Handler()
	handler.init(fs)
	group = handler.groups.byIndex(0)

	event = group.create("custom")
	event.summary = "keep me"
	event.setId()
	group.append(event)
	event.save()
	group.save()

	before = {hash_ for hash_, _fpath in iterObjectFiles(fs)}
	assert before

	event_lib.removeUnusedObjects(fs)

	after = {hash_ for hash_, _fpath in iterObjectFiles(fs)}
	assert before == after


# ---------------------------------------------------------------------------
# generic event behavior (cross-type)


def test_event_get_dict_roundtrip(fs: FileSystem) -> None:
	"""GetDict output reimports into a fresh event."""
	event, _group = createSavedEvent(
		fs,
		"custom",
		summary="orig",
		description="desc",
		calType="gregorian",
		rules=[("date", "2030/05/15")],
	)
	data = event.getDict()
	assert data["type"] == "custom"
	assert data["calType"] == "gregorian"
	assert data["rules"] == [("date", "2030/05/15")]

	fresh = event.__class__(parent=event.parent)
	fresh.setDict(data)
	assert fresh.summary == "orig"
	assert fresh.getRule("date") is not None


def test_event_copy_from(fs: FileSystem) -> None:
	"""CopyFrom copies summary and rules between events."""
	event, _group = createSavedEvent(
		fs,
		"custom",
		summary="orig",
		calType="gregorian",
		rules=[("date", "2030/05/15")],
	)
	target = event.__class__(parent=event.parent)
	target.copyFrom(event)
	assert target.summary == "orig"
	assert target.getRule("date") is not None
	assert target.getJd() == jd(2030, 5, 15)


def test_event_copy_from_exact(fs: FileSystem) -> None:
	"""CopyFromExact copies rules using exact JD conversion."""
	event, _group = createSavedEvent(
		fs,
		"custom",
		summary="orig",
		calType="gregorian",
		rules=[("date", "2030/05/15")],
	)
	target = event.__class__(parent=event.parent)
	target.copyFromExact(event)
	assert target.summary == "orig"
	assert target.getJd() == jd(2030, 5, 15)


def test_event_get_rules_hash(fs: FileSystem) -> None:
	"""GetRulesHash is stable for identical events and changes with rules."""
	event, _group = createSavedEvent(
		fs,
		"custom",
		summary="orig",
		calType="gregorian",
		rules=[("date", "2030/05/15")],
	)
	hash1 = event.getRulesHash()
	hash2 = event.getRulesHash()
	assert hash1 == hash2
	event.setRulesData([("date", "2030/06/01")])
	assert event.getRulesHash() != hash1


def test_event_get_info(fs: FileSystem) -> None:
	"""GetInfo returns a non-empty human-readable description."""
	event, _group = createSavedEvent(
		fs,
		"custom",
		summary="orig",
		calType="gregorian",
		rules=[("date", "2030/05/15")],
	)
	info = event.getInfo()
	assert isinstance(info, str)
	assert "orig" in info


def test_event_change_cal_type(fs: FileSystem) -> None:
	"""ChangeCalType converts the event between calendar types."""
	event, _group = createSavedEvent(
		fs,
		"custom",
		summary="orig",
		calType="gregorian",
		rules=[("date", "2030/05/15")],
	)
	assert event.calType == GREGORIAN
	assert event.changeCalType(1) is True
	assert event.calType == 1
	assert event.changeCalType(GREGORIAN) is True
	assert event.calType == GREGORIAN


def test_event_notify_before_seconds_minutes(fs: FileSystem) -> None:
	"""getNotifyBeforeSec/Min convert the notify-before tuple."""
	event = createEvent(fs, "custom")
	event.notifyBefore = (30, 60)  # 30 minutes
	assert event.getNotifyBeforeSec() == 1800
	assert event.getNotifyBeforeMin() == 30


def test_event_ics_uid(fs: FileSystem) -> None:
	"""IcsUID returns a stable unique identifier."""
	event, _group = createSavedEvent(
		fs,
		"custom",
		summary="orig",
		calType="gregorian",
		rules=[("date", "2030/05/15")],
	)
	assert event.uuid is not None
	assert event.icsUID() == event.uuid + "@starcal"


def test_event_get_revision_and_patch(fs: FileSystem) -> None:
	"""GetRevision loads an old revision and createPatchByHash diffs it."""
	event, group = createSavedEvent(
		fs,
		"custom",
		summary="v1",
		calType="gregorian",
		rules=[("date", "2030/05/15")],
	)
	assert event.id is not None
	reloaded = group.getEvent(event.id)
	assert reloaded.lastHash is not None
	oldHash = reloaded.lastHash

	revision = reloaded.getRevision(oldHash)
	assert revision.summary == "v1"

	reloaded.summary = "v2"
	reloaded.save()
	patch = reloaded.createPatchByHash(oldHash)
	assert patch["action"] == "modify"
	assert patch["eventId"] == event.id
	assert patch["items"][0]["fieldName"] == "summary"
	assert patch["items"][0]["oldValue"] == "v1"
	assert patch["items"][0]["newValue"] == "v2"


def test_event_invalidate_prevents_save(fs: FileSystem) -> None:
	"""Invalidate makes further saves raise RuntimeError."""
	event, _group = createSavedEvent(
		fs,
		"custom",
		summary="orig",
		calType="gregorian",
	)
	event.invalidate()
	assert event.id is None
	with pytest.raises(RuntimeError):
		event.save()


def test_event_rule_dependency_checks(fs: FileSystem) -> None:
	"""Dependency checks reject conflicting rules and allow valid ones."""
	event = createEvent(fs, "custom")

	dateRule = event.addNewRule("date")
	ok, msg = event.checkRulesDependencies(newRule=dateRule)
	assert ok is True

	startRule = event_lib.classes.rule.byName["start"](event)
	ok, msg = event.checkRulesDependencies(newRule=startRule)
	assert ok is False
	assert msg

	ok, msg = event.checkAndAddRule(startRule)
	assert ok is False
	assert startRule not in event.rulesDict.values()

	ok, msg = event.checkAndRemoveRule(dateRule)
	assert ok is True
	assert dateRule not in event.rulesDict.values()


def test_event_set_dict_override(fs: FileSystem) -> None:
	"""SetDictOverride replaces rules and attributes."""
	event = createEvent(fs, "custom")
	event.setDictOverride(
		{
			"summary": "override",
			"calType": "gregorian",
			"rules": [("date", "2031/01/01")],
		},
	)
	assert event.summary == "override"
	assert event.getRule("date") is not None


def test_event_after_modify_basic(fs: FileSystem) -> None:
	"""AfterModifyBasic assigns an ID if needed."""
	event = createEvent(fs, "custom")
	assert event.id is None
	event.afterModifyBasic()
	assert event.id is not None


def test_event_get_start_end_epoch(fs: FileSystem) -> None:
	"""getStartEpoch/getEndEpoch reflect the start/end rules."""
	event, _group = createSavedEvent(
		fs,
		"task",
		summary="t",
		calType="gregorian",
		rules=[
			("start", {"date": "2030/05/15", "time": "09:00:00"}),
			("end", {"date": "2030/05/15", "time": "10:00:00"}),
		],
	)
	assert event.getStartJd() == jd(2030, 5, 15)
	assert event.getEndJd() == jd(2030, 5, 15)
	assert event.getEndEpoch() - event.getStartEpoch() == 3600


def test_event_calc_event_occurrence_in_parent_range(fs: FileSystem) -> None:
	"""CalcEventOccurrence uses the parent group date range."""
	event, _group = createSavedEvent(
		fs,
		"dailyNote",
		summary="n",
		calType="gregorian",
		rules=[("date", "2030/05/15")],
	)
	occur = event.calcEventOccurrence()
	assert len(occur.getTimeRangeList()) == 1


def test_event_get_default_icon() -> None:
	"""GetDefaultIcon returns a path for types that ship an icon."""
	assert DailyNoteEvent.getDefaultIcon().endswith("note.png")
	assert CustomEvent.getDefaultIcon() == ""


def test_event_text_and_icon_helpers(fs: FileSystem) -> None:
	"""getTextParts, getShownDescription and icon helpers work."""
	event, _group = createSavedEvent(
		fs,
		"custom",
		summary="sum",
		description="desc",
		calType="gregorian",
		rules=[("date", "2030/05/15")],
	)
	assert event.getTextParts(showDesc=False) == ["sum"]
	assert event.getTextParts(showDesc=True) == ["sum", eventTextSep, "desc"]
	assert event.getText() == "sum" + eventTextSep + "desc"
	assert event.getShownDescription() == "desc"
	assert event.getIcon() is None or isinstance(event.getIcon(), str)
