from __future__ import annotations

from typing import TYPE_CHECKING, cast

from scal3.cal_types import GREGORIAN, to_jd
from scal3.event_lib.handler import Handler

if TYPE_CHECKING:
	from scal3.event_lib.event_base import Event
	from scal3.filesystem import FileSystem


def jd(year: int, month: int, day: int) -> int:
	"""Return the Gregorian Julian day for the given date."""
	return to_jd(year, month, day, GREGORIAN)


def createEvent(
	fs: FileSystem,
	rules: list[tuple[str, object]],
) -> Event:
	"""Create a custom event with the given rules via setRulesData."""
	handler = Handler()
	handler.init(fs)
	event = cast("Event", handler.groups.byIndex(0).create("custom"))
	event.setRulesData(rules)
	return event


def assertRule(
	event: Event,
	ruleType: str,
	value: object,
	startJd: int,
	endJd: int,
	minRanges: int,
) -> None:
	"""Check a rule's value roundtrip, description methods and occurrence."""
	rule = event.getRule(ruleType)
	assert rule is not None
	assert rule.name == ruleType
	assert rule.getRuleValue() == value
	assert isinstance(rule.getServerString(), str)
	assert isinstance(rule.getInfo(), str)

	occur = rule.calcOccurrence(startJd, endJd, event)
	assert len(occur.getTimeRangeList()) >= minRanges


def startRule(date: str) -> tuple[str, dict[str, str]]:
	"""Return a start rule tuple for the given date at 09:00."""
	return ("start", {"date": date, "time": "09:00:00"})


def test_rule_cycle_days(fs: FileSystem) -> None:
	"""CycleDaysEventRule repeats every N days from the event start."""
	event = createEvent(fs, [startRule("2030/05/15"), ("cycleDays", 3)])
	assertRule(
		event,
		"cycleDays",
		3,
		jd(2030, 5, 15),
		jd(2030, 6, 1),
		minRanges=6,
	)


def test_rule_cycle_weeks(fs: FileSystem) -> None:
	"""CycleWeeksEventRule repeats every N weeks from the event start."""
	event = createEvent(fs, [startRule("2030/05/15"), ("cycleWeeks", 2)])
	assertRule(
		event,
		"cycleWeeks",
		2,
		jd(2030, 5, 15),
		jd(2030, 6, 1),
		minRanges=2,
	)


def test_rule_cycle_len(fs: FileSystem) -> None:
	"""CycleLenEventRule repeats every N days plus an extra time."""
	event = createEvent(
		fs,
		[startRule("2030/05/15"), ("cycleLen", {"days": 3, "extraTime": "02:00:00"})],
	)
	assertRule(
		event,
		"cycleLen",
		{"days": 3, "extraTime": "02:00:00"},
		jd(2030, 5, 15),
		jd(2030, 6, 1),
		minRanges=6,
	)


def test_rule_date(fs: FileSystem) -> None:
	"""DateEventRule matches a single date."""
	event = createEvent(fs, [("date", "2030/05/15")])
	assertRule(
		event,
		"date",
		"2030/05/15",
		jd(2030, 5, 1),
		jd(2030, 6, 1),
		minRanges=1,
	)
	assert event.getRule("date") is not None
	dateRule = event.getRule("date")
	assert dateRule is not None
	assert dateRule.getJd() == jd(2030, 5, 15)


def test_rule_ex_dates(fs: FileSystem) -> None:
	"""ExDatesEventRule excludes specific dates from the range."""
	event = createEvent(fs, [("ex_dates", ["2030/05/16"])])
	assertRule(
		event,
		"ex_dates",
		["2030/05/16"],
		jd(2030, 5, 15),
		jd(2030, 5, 18),
		minRanges=2,
	)
	exDatesRule = event.getRule("ex_dates")
	assert exDatesRule is not None
	occur = exDatesRule.calcOccurrence(
		jd(2030, 5, 15),
		jd(2030, 5, 18),
		event,
	)
	assert len(occur.getTimeRangeList()) == 2  # 3 days minus 1 excluded


def test_rule_start(fs: FileSystem) -> None:
	"""StartEventRule defines the interval from the event start."""
	event = createEvent(fs, [startRule("2030/05/15")])
	assertRule(
		event,
		"start",
		{"date": "2030/05/15", "time": "09:00:00"},
		jd(2030, 5, 15),
		jd(2030, 5, 16),
		minRanges=1,
	)


def test_rule_end(fs: FileSystem) -> None:
	"""EndEventRule defines the interval through the event end."""
	event = createEvent(fs, [("end", {"date": "2030/05/15", "time": "10:00:00"})])
	assertRule(
		event,
		"end",
		{"date": "2030/05/15", "time": "10:00:00"},
		jd(2030, 5, 15),
		jd(2030, 5, 16),
		minRanges=1,
	)


def test_rule_day_time(fs: FileSystem) -> None:
	"""DayTimeEventRule matches one moment per day."""
	event = createEvent(fs, [("dayTime", "09:00:00")])
	assertRule(
		event,
		"dayTime",
		"09:00:00",
		jd(2030, 5, 15),
		jd(2030, 5, 18),
		minRanges=3,
	)


def test_rule_day_time_range(fs: FileSystem) -> None:
	"""DayTimeRangeEventRule matches a time interval each day."""
	event = createEvent(fs, [("dayTimeRange", ("09:00:00", "10:00:00"))])
	assertRule(
		event,
		"dayTimeRange",
		("09:00:00", "10:00:00"),
		jd(2030, 5, 15),
		jd(2030, 5, 18),
		minRanges=3,
	)


def test_rule_duration(fs: FileSystem) -> None:
	"""DurationEventRule spans a length of time after the start rule."""
	event = createEvent(fs, [startRule("2030/05/15"), ("duration", "2 hour")])
	assertRule(
		event,
		"duration",
		"2 hour",
		jd(2030, 5, 15),
		jd(2030, 5, 16),
		minRanges=1,
	)


def test_rule_week_num_mode(fs: FileSystem) -> None:
	"""WeekNumberModeEventRule restricts occurrences to odd/even weeks."""
	event = createEvent(fs, [startRule("2030/01/01"), ("weekNumMode", "odd")])
	assertRule(
		event,
		"weekNumMode",
		"odd",
		jd(2030, 1, 1),
		jd(2030, 2, 1),
		minRanges=14,
	)


def test_rule_week_day(fs: FileSystem) -> None:
	"""WeekDayEventRule matches specific days of the week."""
	event = createEvent(fs, [("weekDay", [1, 3])])
	assertRule(
		event,
		"weekDay",
		[1, 3],
		jd(2030, 5, 1),
		jd(2030, 5, 15),
		minRanges=4,
	)


def test_rule_week_month(fs: FileSystem) -> None:
	"""WeekMonthEventRule matches a weekday instance within a month."""
	event = createEvent(
		fs,
		[("weekMonth", {"month": 1, "wmIndex": 1, "weekDay": 1})],
	)
	assertRule(
		event,
		"weekMonth",
		{"month": 1, "wmIndex": 1, "weekDay": 1},
		jd(2030, 1, 1),
		jd(2031, 1, 1),
		minRanges=1,
	)


def test_rule_year(fs: FileSystem) -> None:
	"""YearEventRule matches specific years."""
	event = createEvent(fs, [("year", [2030])])
	assertRule(
		event,
		"year",
		[2030],
		jd(2030, 1, 1),
		jd(2030, 12, 31),
		minRanges=364,
	)


def test_rule_month(fs: FileSystem) -> None:
	"""MonthEventRule matches specific months."""
	event = createEvent(fs, [("month", [5])])
	assertRule(
		event,
		"month",
		[5],
		jd(2030, 1, 1),
		jd(2030, 12, 31),
		minRanges=31,
	)


def test_rule_day(fs: FileSystem) -> None:
	"""DayOfMonthEventRule matches specific days of the month."""
	event = createEvent(fs, [("day", [15])])
	assertRule(
		event,
		"day",
		[15],
		jd(2030, 1, 1),
		jd(2030, 12, 31),
		minRanges=12,
	)


def test_rule_ex_year(fs: FileSystem) -> None:
	"""ExYearEventRule excludes specific years."""
	event = createEvent(fs, [("ex_year", [2031])])
	assertRule(
		event,
		"ex_year",
		[2031],
		jd(2030, 1, 1),
		jd(2030, 12, 31),
		minRanges=364,
	)


def test_rule_ex_month(fs: FileSystem) -> None:
	"""ExMonthEventRule excludes specific months."""
	event = createEvent(fs, [("ex_month", [6])])
	assertRule(
		event,
		"ex_month",
		[6],
		jd(2030, 1, 1),
		jd(2030, 12, 31),
		minRanges=334,
	)


def test_rule_ex_day(fs: FileSystem) -> None:
	"""ExDayOfMonthEventRule excludes specific days of the month."""
	event = createEvent(fs, [("ex_day", [16])])
	assertRule(
		event,
		"ex_day",
		[16],
		jd(2030, 1, 1),
		jd(2030, 12, 31),
		minRanges=352,
	)
