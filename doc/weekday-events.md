# Weekday Recurrence Event Types

Two standalone event types that recur by *day of week* instead of by day-of-month or year. Both are
thin compositions of existing rules — no new recurrence rule is needed. Their `end` date is an
exclusive boundary: an event ending on 2030/01/08 includes occurrences through 2030/01/07.

## Weekly Weekday Event (`WeeklyWeekdayEvent`)

Repeats every week on a chosen set of days. **Class:** `WeeklyWeekdayEvent`, type name
`weeklyWeekday`, UI label *"Weekly Weekday Event"*.

**Rules:** `start` + `end` (date range), `dayTimeRange` (time of day), `weekDay` (selected days).

| Example | Days | Time | Meaning |
| --- | --- | --- | --- |
| Office hours | Mon–Fri | 09:00–17:00 | every weekday |
| Standup meeting | Mon, Wed, Fri | 09:30–09:45 | three times a week |
| Gym class | Sat | 08:00–09:00 | once a week |
| Language course | Tue, Thu | 18:00–20:00 | twice a week |

Serialized rules for "office hours" (Gregorian):

```python
{
	"start": {"date": "2030/01/01", "time": "09:00:00"},
	"end": {"date": "2031/01/01", "time": "00:00:00"},
	"dayTimeRange": ("09:00:00", "17:00:00"),
	"weekDay": [1, 2, 3, 4, 5],  # 0=Sunday .. 6=Saturday
}
```

## Monthly Weekday Event (`MonthlyWeekdayEvent`)

Repeats on the *nth* occurrence of a weekday within each month. **Class:** `MonthlyWeekdayEvent`,
type name `monthlyWeekday`, UI label *"Monthly Weekday Event"*.

**Rules:** `start` + `end` (date range), `dayTimeRange` (time of day), `weekMonth` (month, weekday
instance, weekday).

The `weekMonth` value is `{month, wmIndex, weekDay}` where `wmIndex` is 0..4 (`First, Second, Third,
Fourth, Last`) and `month` is 0 for every month or 1..12 for a single month.

| Example | weekMonth | Meaning |
| --- | --- | --- |
| Payday | `{"month": 0, "wmIndex": 1, "weekDay": 2}` | second Tuesday of every month |
| Board meeting | `{"month": 0, "wmIndex": 4, "weekDay": 5}` | last Friday of every month |
| Club membership day | `{"month": 0, "wmIndex": 0, "weekDay": 1}` | first Monday of every month |
| Tax deadline | `{"month": 11, "wmIndex": 4, "weekDay": 4}` | last Thursday of November only |

Serialized rules for "second Tuesday of every month":

```python
{
	"start": {"date": "2030/01/01", "time": "00:00:00"},
	"end": {"date": "2031/01/01", "time": "00:00:00"},
	"dayTimeRange": ("09:00:00", "17:00:00"),
	"weekMonth": {"month": 0, "wmIndex": 1, "weekDay": 2},
}
```

## How these differ from the weekly event

The existing **Weekly Event** (`weekly`, `WeeklyEvent`) is a *gap-based* recurrence: it repeats every
`N` weeks (`cycleWeeks` rule), always on the same weekday as its start date, one occurrence per
cycle. Its purpose is controlling the interval — "every 2 weeks", "every 3 weeks".

The two types in this document are *pattern-based* instead: they pick *which* days of the week
recur, not how many weeks apart.

| | `weekly` (Weekly Event) | `weeklyWeekday` | `monthlyWeekday` |
| --- | --- | --- | --- |
| Question it answers | "how often?" | "which days?" | "which weekday instance of the month?" |
| Day of occurrence | the start date's weekday, once per cycle | any chosen set of days, every week | nth / last occurrence of a chosen weekday |
| Multiple days per week | no | yes (e.g. Mon–Fri) | no |
| Every-N-weeks interval | yes (`cycleWeeks`) | no (always weekly) | no |
| Month-based (e.g. 2nd Tuesday) | no | no | yes |

The user problem each solves:

- **Weekly Event** — a recurring appointment with a fixed gap: *"dentist visit every 3 weeks"*,
  *"biweekly Friday standup"*. It is the wrong tool when the schedule is *"every weekday"* or *"the
  second Tuesday of the month"*.
- **Weekly Weekday Event** — anything that happens on fixed days every week, especially several days
  at once: *office hours 09:00–17:00 Mon–Fri*, *a course that meets Tue and Thu*, *gym every
  Saturday*. It is the wrong tool when you need to skip weeks ("every other week").
- **Monthly Weekday Event** — anything pegged to a weekday *position* in the month rather than a
  calendar date: *payday on the second Tuesday*, *board meeting on the last Friday*. The weekly event
  cannot express this at all, and a fixed calendar date (e.g. the 15th) drifts across weekdays over
  time.

A *"every 2nd week on Friday"* (biweekly payday) is a gap-based schedule and stays the job of the
weekly event or a `cycleWeeks` + `weekDay` composition — these two types always recur every week or
every month and cannot skip weeks.

## ICS / iCalendar

Both types support Gregorian iCalendar data only. They export and import a single recurring VEVENT:
`DTSTART`/`DTEND` carry the time and duration of one instance, while `UNTIL` carries the inclusive
date of the last recurrence. Starcal converts that inclusive date to its exclusive `end` boundary.

- `weeklyWeekday` → `RRULE:FREQ=WEEKLY;UNTIL=<date>;BYDAY=MO,TU,WE,TH,FR`
- `monthlyWeekday` → `RRULE:FREQ=MONTHLY;UNTIL=<date>;BYDAY=2TU` (or `-1FR` for "Last", plus
  `BYMONTH=n` when a single month is set)

Import accepts the matching `FREQ`; an `INTERVAL` other than `1` is rejected for both types (that is
the existing gap-based `weekly` event's job). The RRULE `UNTIL` value, rather than the recurring
instance's `DTEND`, determines the imported series end date.

## Implementation notes

- Both classes live in `scal3/event_lib/weekday.py`, sharing a private
  `_WeekdayEventBase` for the date-range/time-range handling, `getV4Dict`, `setDefaults`, and the
  ICS plumbing. The two pattern rules (`weekDay`, `weekMonth`) are defined and serialized per
  subclass.
- Recurrence is computed by the normal rule-intersection in `Event.calcEventOccurrenceIn` — no
  custom occurrence logic.
- Rule values are validated: weekly weekday lists must contain at least one weekday from 0 (Sunday)
  through 6 (Saturday), and monthly patterns must use month 0..12, weekday 0..6, and index 0..4.
- Widgets: `scal3/ui_gtk/event/event/weeklyWeekday.py` (day-toggle row) and
  `scal3/ui_gtk/event/event/monthlyWeekday.py` (nth/weekday/month combos), sharing
  `weekdayBase.WidgetBase` for the common start/end/time rows.
- Both types are enabled on generic groups via the default `acceptsEventTypes` list in
  `event_container.py`.
