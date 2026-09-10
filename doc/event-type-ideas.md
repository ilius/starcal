# Ideas for Implementing New Event Types

## How a new type plugs in

1. **Model** — subclass `Event` or `SingleStartEndEvent` in `scal3/event_lib/`, set
   `name`/`desc`/`isAllDay`/`iconName`/`requiredRules`/`supportedRules`, register with
   `@classes.event.register`. Override `setDefaults`, `getV4Dict`, `calcEventOccurrenceIn`,
   and `getIcsData`/`setIcsData` (like `yearly.py`, `weekly.py`).
2. **Rules** — subclass `EventRule` if you need new recurrence logic (e.g.
   `@classes.rule.register` with `provide`/`need`/`conflict`). Most types are just
   *compositions of existing rules* (start, end, dayTimeRange, cycle*, weekDay, day, month).
3. **Group** — `@classes.group.register` with `acceptsEventTypes` if the type needs a
   dedicated container (e.g. `YearlyGroup`).
4. **UI** — a `WidgetClass` in `scal3/ui_gtk/event/event/<name>.py` (extends
   `common.WidgetClass`), wired into `widgetClassLoaderByName` in `ui_gtk/event/__init__.py`
   and `import_all.py`. Plugins can do all this via `api.get("event_lib", "classes")`.
5. **i18n** — every `_("...")` string must be added to `locale.d/*.po`.

## Ideas (ranked by fit for this codebase)

Complexity is an end-to-end estimate: **Low** means mostly existing rule composition and a small
widget; **Medium** means a new model or calculation plus normal serialization/UI work; **High**
means changes to occurrence calculation, persistence, time-zone semantics, or generated data.

1. **Celestial events** — new moon / full moon / equinox / solstice. `moon.py` and
   `season.py` already exist (`getSpringJdAfter`, `getMoonPhase`). A `CelestialEvent`/
   `CelestialEventRule` computing occurrences and auto-summary from phase would be a natural
   fit and valuable for the Persian audience (Nowruz = spring equinox). This mirrors the
   commented-out `SunTimeRule`/`HolidayEventRule` in `event_base.py`. **Classes:**
   `CelestialEvent`, `CelestialEventRule`. **Complexity:** Medium.

2. **Relative annual events** — "N days before/after Nowruz", "N days after Eid", Easter via
   computus. An offset-based rule around an anchor date; strong fit for the multi-calendar core.
   **Classes:** `RelativeAnnualEvent`, `RelativeAnnualEventRule`. **Complexity:** Medium.

3. **Weekday-pattern events** — "second Tuesday of the month", "every weekday 9–17".
   `WeekMonthEventRule` + `WeekDayEventRule` + `DayTimeRangeEventRule` already exist. `WeekDayEventRule`
   is exercised by `UniversityClassEvent`/`UniversityExamEvent` (`university.py`), and
   `WeekMonthEventRule` is reachable via `CustomEvent`'s free-form rule editor (`events.py` inherits
   `supportedRules = None`, i.e. all rules). Neither has a dedicated event type — a thin composed
   type would package them. **Class:** `WeekdayPatternEvent`. **Complexity:** Low.

4. **Countdown / deadline events** — autoSummary like "N days left" (computed from current JD)
   with color/notifier when below threshold. Small, high-visibility win. **Class:**
   `CountdownEvent`. **Complexity:** Low–Medium.

5. **Habit / medication reminders** — recurring event with per-occurrence "done" marking.
   **Requires occurrence-state persistence**, which doesn't exist today — the biggest structural
   gap. Worth designing before jumping in. **Classes:** `HabitEvent`, optionally
   `MedicationReminderEvent` as a domain-specific subclass. **Complexity:** High.

6. **Recurring multi-day spans** — e.g. a 3-day festival repeating monthly. Current recurrence
   engine produces day-level `JdOccurSet`s; multi-day recurrence needs a new occur-set variant —
   an `IntervalOccurSet`-per-occurrence (`IntervalOccurSet` itself already exists in `occur.py`
   and is used by `SingleStartEndEvent`/`LargeScaleEvent`) returned from `Event.calcEventOccurrenceIn`.
   Another real gap. **Classes:** `RecurringSpanEvent`, `RecurringIntervalOccurSet`.
   **Complexity:** High.

7. **Biweekly payday / "every 2nd week on Friday"** — trivial composition of
   `CycleWeeksEventRule` + `WeekDayEventRule`. **Class:** `BiweeklyEvent`. **Complexity:** Low.

8. **Recurring flexible task (postponable, no strict time)** — the concrete motivation for
   per-occurrence state. E.g. "water plants every 3 days" or "review budget weekly": a recurring
   all-day task with a target date but no hard time; each occurrence can be postponed (marked
   done late / moved later), in one of two modes:
   - **Shift schedule** — postponing an occurrence delays all subsequent occurrences by the same
     amount (fixed phase preserved; a weekly task stays on its weekday).
   - **Rolling interval** — the next occurrence is recomputed from the actual completion date plus
     the interval, preserving the average interval while letting the phase drift.
   Builds on the existing `TaskEvent`/`TaskList` (`task.py`); needs per-occurrence state storage
   (a `{eventId}.occ.json` sidecar or a reschedule map in the event dict, kept out of the revision
   history), a "Mark done / Postpone" occurrence UI, and a rule that recomputes the next due date.
   **Classes:** `FlexibleTaskEvent`, `OccurrenceStateStore`. **Complexity:** High.

9. **Availability / office-hours event** — a recurring interval that describes when a person,
   room, or service is available rather than an appointment. It could support multiple intervals
   per day, exclusions, and a label such as "available" or "busy". This is a good composition of
   weekday, time-range, cycle, and exception rules, and could later power conflict checks without
   requiring a separate scheduling model. **Class:** `AvailabilityEvent`. **Complexity:**
   Medium.

10. **Travel / time-zone transition event** — departure and arrival with separate local times and
    zones, optionally including a date-line crossing. The existing start/end and duration model is
    close, but the event would expose the distinction between *instant* and *display time*. It would
    be a valuable test case for ICS import/export, calendar conversion, and all-day rendering.
    **Class:** `TravelEvent`. **Complexity:** High.

11. **Study-plan / course milestone event** — a group or event type for semesters, lessons,
    assignments, and exams, with a generated sequence of due dates from a start date and cadence.
    `UniversityTerm`, `UniversityClassEvent`, and `UniversityExamEvent` provide useful existing
    concepts to consolidate. The first version could remain a thin group-level convenience feature;
    progress tracking would be a later occurrence-state extension. **Classes:**
    `StudyPlanGroup`, `StudyMilestoneEvent`. **Complexity:** Medium–High.

12. **Anniversary / age milestone event** — birthdays, hire dates, sobriety anniversaries, and
    similar dates whose summary includes the number of completed years. This is simpler than a
    general countdown: a yearly rule plus a stable anchor date and calendar-aware age calculation.
    It would fit naturally beside `LifetimeEvent` and exercise localized summaries without adding a
    new recurrence rule. **Class:** `AnniversaryEvent`. **Complexity:** Low–Medium.

13. **Sun-time event** — sunrise, sunset, solar noon, or a configurable offset from one of them.
    The commented-out `SunTimeRule` in `event_base.py` is an explicit extension point. A practical
    implementation should define location ownership, polar-day/polar-night behavior, caching, and
    whether a location change is historical event data or a current preference. **Classes:**
    `SunTimeEvent`, `SunTimeRule`. **Complexity:** Medium–High.

14. **Health measurement / symptom event** — a timestamped observation with a value, unit, and
    optional tags (for example temperature, blood pressure, pain level, or medication dose). The
    menstrual event types already demonstrate domain-specific events; a generic observation model
    could reuse their group pattern while keeping sensitive values out of summaries and default
    notifications. **Classes:** `HealthObservationEvent`, `HealthObservationGroup`. **Complexity:**
    Medium.

15. **Event template / generated series** — a reusable event definition that creates ordinary
    events for a selected date range, instead of making every use a recurrence rule. This would be
    useful for shifts, conference agendas, travel itineraries, and multi-step projects. It also
    gives users a safe way to edit one generated occurrence without introducing the full persistent
    occurrence-state machinery described above. **Classes:** `EventTemplate`,
    `GeneratedSeriesGroup`. **Complexity:** High.

## Key takeaway

The rule-composition model (`provide`/`need`/`conflict` + intersection in
`Event.calcEventOccurrenceIn`) is the real extension point — most new types need zero new rules.
The two genuinely hard problems are **(5, 8) per-occurrence state** and **(6) multi-day recurrence**;
anything else is mostly a new file + a UI widget. Items 5, 6, and 8 all converge on the same missing
infrastructure — a place to persist per-occurrence facts (done/postponed dates, overrides) separate
from the event's revision history.
