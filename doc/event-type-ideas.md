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

## Ideas (ranked by usefulness for general desktop users)

Complexity is an end-to-end estimate: **Low** means mostly existing rule composition and a small
widget; **Medium** means a new model or calculation plus normal serialization/UI work; **High**
means changes to occurrence calculation, persistence, time-zone semantics, or generated data.
Codebase fit varies; items that lean on Persian-calendar concepts are noted as such.

1. **Countdown / deadline events** — autoSummary like "N days left" (computed from current JD)
   with color/notifier when below threshold. Universally useful for deadlines, expirations, and
   due dates; small, high-visibility win. **Class:** `CountdownEvent`. **Complexity:** Low–Medium.

2. **Weekday-pattern events** — "second Tuesday of the month", "every weekday 9–17".
   Standing meetings, classes, recurring appointments, payday. `WeekMonthEventRule` +
   `WeekDayEventRule` + `DayTimeRangeEventRule` already exist. `WeekDayEventRule` is exercised by
   `UniversityClassEvent`/`UniversityExamEvent` (`university.py`), and `WeekMonthEventRule` is
   reachable via `CustomEvent`'s free-form rule editor (`events.py` inherits `supportedRules = None`,
   i.e. all rules). Neither has a dedicated event type — a thin composed type would package them.
   **Class:** `WeekdayPatternEvent`. **Complexity:** Low.

3. **Travel / time-zone transition event** — departure and arrival with separate local times and
   zones, optionally including a date-line crossing. Useful for business and leisure travelers,
   itineraries, and remote-work planning. The existing start/end and duration model is close, but
   the event would expose the distinction between *instant* and *display time*. It would be a
   valuable test case for ICS import/export, calendar conversion, and all-day rendering.
   **Class:** `TravelEvent`. **Complexity:** High.

4. **Anniversary / age milestone event** — birthdays, hire dates, sobriety anniversaries, and
   similar dates whose summary includes the number of completed years. Universally useful; simpler
   than a general countdown: a yearly rule plus a stable anchor date and calendar-aware age
   calculation. Fits naturally beside `LifetimeEvent` and exercises localized summaries without
   adding a new recurrence rule. **Class:** `AnniversaryEvent`. **Complexity:** Low–Medium.

5. **Event template / generated series** — a reusable event definition that creates ordinary
   events for a selected date range, instead of making every use a recurrence rule. Useful for
   shifts, conference agendas, travel itineraries, and multi-step projects. Also gives users a safe
   way to edit one generated occurrence without introducing the full persistent occurrence-state
   machinery described in [occurrence-state-persistence.md](occurrence-state-persistence.md).
   **Classes:** `EventTemplate`, `GeneratedSeriesGroup`.
   **Complexity:** High.

6. **Recurring multi-day spans** — e.g. a 3-day festival repeating monthly. Broadly useful for
   holidays, conventions, and off-site events. Current recurrence engine produces day-level
   `JdOccurSet`s; multi-day recurrence needs a new occur-set variant — an `IntervalOccurSet`-per-
   occurrence (`IntervalOccurSet` itself already exists in `occur.py` and is used by
   `SingleStartEndEvent`/`LargeScaleEvent`) returned from `Event.calcEventOccurrenceIn`. Another
   real gap. **Classes:** `RecurringSpanEvent`, `RecurringIntervalOccurSet`. **Complexity:** High.

7. **Availability / office-hours event** — a recurring interval that describes when a person,
   room, or service is available rather than an appointment. Supports multiple intervals per day,
   exclusions, and a label such as "available" or "busy". A good composition of weekday, time-range,
   cycle, and exception rules, and could later power conflict checks without requiring a separate
   scheduling model. **Class:** `AvailabilityEvent`. **Complexity:** Medium.

8. **Relative annual events** — "N days before/after Nowruz", "N days after Eid", Easter via
    computus, Thanksgiving/Labor Day-style movable holidays. Movable holidays exist in every
    calendar culture, so this is broadly useful even though the anchor computation is per-culture.
    An offset-based rule around an anchor date. **Classes:** `RelativeAnnualEvent`,
    `RelativeAnnualEventRule`. **Complexity:** Medium.

9. **Health measurement / symptom event** — a timestamped observation with a value, unit, and
    optional tags (temperature, blood pressure, pain level, medication dose). The menstrual event
    types already demonstrate domain-specific events; a generic observation model could reuse their
    group pattern while keeping sensitive values out of summaries and default notifications.
    Useful for health-aware users. **Classes:** `HealthObservationEvent`,
    `HealthObservationGroup`. **Complexity:** Medium.

10. **Celestial events** — new moon / full moon / equinox / solstice. `moon.py` and `season.py`
    already exist (`getSpringJdAfter`, `getMoonPhase`). Broadly appealing to astronomy enthusiasts
    and gardeners; the equinox/solstice tie-in to Nowruz is a Persian-calendar bonus. A
    `CelestialEvent`/`CelestialEventRule` computing occurrences and auto-summary from phase would
    mirror the commented-out `SunTimeRule`/`HolidayEventRule` in `event_base.py`. **Classes:**
    `CelestialEvent`, `CelestialEventRule`. **Complexity:** Medium.

11. **Sun-time event** — sunrise, sunset, solar noon, or a configurable offset from one of them.
    Niche but well-defined: photographers, farmers, and outdoor workers. The commented-out
    `SunTimeRule` in `event_base.py` is an explicit extension point. A practical implementation
    should define location ownership, polar-day/polar-night behavior, caching, and whether a
    location change is historical event data or a current preference. **Classes:** `SunTimeEvent`,
    `SunTimeRule`. **Complexity:** Medium–High.

12. **Biweekly payday / "every 2nd week on Friday"** — trivial composition of `CycleWeeksEventRule`
    + `WeekDayEventRule`. Mostly a special case of weekday-pattern events (#2); listed for
    completeness. **Class:** `BiweeklyEvent`. **Complexity:** Low.

## Key takeaway

The rule-composition model (`provide`/`need`/`conflict` + intersection in
`Event.calcEventOccurrenceIn`) is the real extension point — most new types need zero new rules.
The two genuinely hard problems are **per-occurrence state** (see
[occurrence-state-persistence.md](occurrence-state-persistence.md)) and **multi-day recurrence**
(#6); anything else is mostly a new file + a UI widget.
