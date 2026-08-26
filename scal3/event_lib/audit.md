# Audit Report: `scal3/event_lib/`

**Date:** 2026-08-26
**Total lines:** 9,358 across 50 Python files (39 top-level + 11 in `rules/`)
**License:** AGPL-3.0+

---

## 1. Architecture Overview

The `event_lib` package is the core event management system for StarCal. It provides:

- **Event model** — composable rule-based event definitions (date, time, cycle, duration, etc.)
- **Group model** — containers for events with occurrence tracking and search
- **Occurrence engine** — computes which events occur on a given day/range
- **Persistence** — JSON-based file storage with content-addressed binary objects and history tracking
- **Plugin registry** — class registration system for extensible event types, rules, notifiers, accounts, and groups
- **VCS integration** — git/hg commit and tag event groups
- **ICS export** — iCalendar format export

### Key Design Patterns

| Pattern | Location | Description |
|---|---|---|
| Registry | `register.py` | `@classes.event.register` decorators auto-register types at import time |
| Protocol typing | `pytypes.py` | Structural subtyping via `Protocol` for loose coupling |
| Content-addressed storage | `objects.py`, `event_base.py` | Objects stored as `{hash}.json` with full revision history |
| Rule composition | `rules/`, `rule_container.py` | Events defined by composable rules rather than fixed schemas |
| Mixin inheritance | `event_base.py` | `Event` inherits from `HistoryEventObjBinaryModel`, `RuleContainer`, `WithIcon` |

### Class Hierarchy

```
SObj (s_object)
├── EventObjTextModel
│   ├── InfoWrapper
│   ├── LastIdsWrapper
│   └── Event
│       ├── SingleStartEndEvent
│       │   ├── LifetimeEvent
│       │   ├── TaskEvent
│       │   └── AllDayTaskEvent
│       ├── CustomEvent
│       ├── LargeScaleEvent
│       ├── MonthlyEvent
│       ├── WeeklyEvent
│       ├── YearlyEvent
│       ├── DailyNoteEvent
│       ├── UniversityClassEvent
│       ├── UniversityExamEvent
│       ├── VcsEpochBaseEvent
│       │   ├── VcsCommitEvent
│       │   └── VcsTagEvent
│       └── VcsDailyStatEvent
├── HistoryEventObjBinaryModel
│   ├── Account
│   │   └── DummyAccount
│   ├── EventContainer
│   │   ├── EventGroup
│   │   │   ├── NoteBook
│   │   │   ├── TaskList
│   │   │   ├── YearlyGroup
│   │   │   ├── LargeScaleGroup
│   │   │   ├── LifetimeGroup
│   │   │   ├── UniversityTerm
│   │   │   ├── VcsBaseEventGroup
│   │   │   │   └── VcsEpochBaseEventGroup
│   │   │   │       ├── VcsCommitEventGroup
│   │   │   │       └── VcsTagEventGroup
│   │   │   └── VcsDailyStatEventGroup
│   │   └── EventTrash
│   └── EventNotifier
│       ├── AlarmNotifier
│       ├── FloatingMsgNotifier
│       ├── WindowMsgNotifier
│       └── CommandNotifier
├── OccurSet
│   ├── JdOccurSet
│   ├── IntervalOccurSet
│   └── TimeListOccurSet
└── EventRule
    ├── AllDayEventRule
    │   └── WeekDayEventRule
    ├── MultiValueAllDayEventRule
    ├── DateEventRule
    │   └── DateAndTimeEventRule
    │       ├── StartEventRule
    │       └── EndEventRule
    ├── DayTimeEventRule
    ├── DayTimeRangeEventRule
    ├── DurationEventRule
    ├── CycleDaysEventRule
    ├── CycleWeeksEventRule
    ├── CycleLenEventRule
    ├── WeekNumberModeEventRule
    ├── WeekMonthEventRule
    ├── YearEventRule
    ├── MonthEventRule
    ├── DayOfMonthEventRule
    ├── ExYearEventRule
    ├── ExMonthEventRule
    ├── ExDayOfMonthEventRule
    └── ExDatesEventRule
```

---

## 2. File-by-File Summary

| File | Purpose |
|---|---|---|
| `__init__.py` | Package init, global `ev` Handler, `init()`, `removeUnusedObjects()` |
| `event_base.py` | Core `Event` and `SingleStartEndEvent` classes |
| `group.py` | `EventGroup` — main event container with caching, search, import/export |
| `university.py` | University term scheduling (classes, exams, weekly schedule) |
| `task.py` | Task events and all-day tasks |
| `event_container.py` | Base container for events (holds event ID lists) |
| `vcs.py` | VCS commit/tag/daily-stat event groups |
| `pytypes.py` | Protocol definitions for all major types |
| `rules/rule_week.py` | Week-based rules (weekday, week-month, week number) |
| `yearly.py` | Yearly recurring events (birthdays, anniversaries) |
| `occur.py` | Occurrence set types (JD, interval, time-list) |
| `groups_holder.py` | Manages list of all event groups |
| `rule_container.py` | Mixin for objects containing rules |
| `vcs_base.py` | Base classes for VCS event groups |
| `large_scale.py` | Large-scale (millennia/centuries) events |
| `rules/rule_cycle.py` | Cycle-based recurrence rules |
| `accounts.py` | Account base class |
| `holders.py` | Generic container for ordered collections |
| `rules/rule_date.py` | Date rules and exclusion dates |
| `rules/rule_daytime.py` | Time-within-day rules |
| `rules/rule_datetime.py` | Date+time rules |
| `rules/rule_ymd.py` | Year/month/day matching rules |
| `lifetime.py` | Lifetime (birth-death) events |
| `occur_data.py` | Day/week/month occurrence data computation |
| `rules/rule_duration.py` | Duration-based rule |
| `accounts_holder.py` | Account loading/storing |
| `note.py` | Daily notes (notebook) |
| `notifiers.py` | Concrete notifier implementations |
| `rules/rule_allday.py` | All-day event matching rules |
| `monthly.py` | Monthly recurring events |
| `state.py` | Global mutable state (`allReadOnly`, `info`, `lastIds`) |
| `rules/rule_base.py` | Base `EventRule` class |
| `event_ics.py` | ICS format export |
| `typing_test.py` | Ad-hoc type checking (not a real test suite) |
| `trash.py` | Trash container for deleted events |
| `common.py` | Shared utilities (week days, JD, compression) |
| `weekly.py` | Weekly recurring events |
| `events.py` | Registers `CustomEvent` type |
| `handler.py` | Facade wrapping accounts, groups, trash |
| `register.py` | Class registry system |
| `patch.py` | Patch list creation for sync |
| `groups_import.py` | Import mode constants |
| `icon.py` | Icon path handling |
| `rules/__init__.py` | Re-exports all rule classes |
| `objects.py` | Binary model for history-tracked objects |
| `notifier_base.py` | Base notifier class |
| `object_base.py` | Read-only respecting text model |
| `errors.py` | `AccountError` exception |
| `exceptions.py` | `BadEventFile` exception |

---

## 3. Issues Found

### P1 — High Priority

#### 1. `typing_test.py` is not a proper test
**File:** `typing_test.py:101 lines`

Runs code at import level (`print(isinstance(acc, AccountType))`). Contains mostly commented-out code.

**Recommended fix:** Convert to a `pytest` test file with proper test functions, or remove entirely if type checking is handled by `mypy`/`pyright`.

#### 2. `WeekOccurData` and `MonthOccurData` are unused
**File:** `occur_data.py`

Both NamedTuple classes are defined but never imported or used anywhere in the codebase.

**Recommended fix:** Remove both classes. If needed in the future, they can be re-added.

---

### P2 — Medium Priority

#### 3. `defaultGroupTypeIndex = 0` has unresolved FIXME
**File:** `__init__.py:150`

**Recommended fix:** Determine the correct default (likely `0` for "NoteBook") and remove the `# FIXME` comment, or make it configurable.

#### 4. Large blocks of commented-out dead code
**Files:** `event_base.py` (lines ~480-540, ~680-700), `__init__.py` (lines 166-186)

Commented-out TODO classes (`HolidayEventRule`, `ShowInMCalEventRule`, `SunTimeRule`) and disabled methods (`loadFiles`, `getUrlForFile`, `getFilesUrls`).

**Recommended fix:** Remove all commented-out code. If the features are planned, track them as issues instead.

#### 5. `university.py:setDefaults` only handles Jalali calendar
**File:** `university.py:269-291`

No default generation for Gregorian or other calendar types.

**Recommended fix:** Add Gregorian defaults or raise a clear error for unsupported calendar types.

#### 6. `NotImplementedError` used as abstract method signal
**Files:** `event_base.py` (`index`), `notifier_base.py` (`notify`), `rules/rule_base.py` (`getServerString`), `vcs_base.py` (`load`)

**Recommended fix:** Make base classes inherit from `abc.ABC` and mark methods with `@abstractmethod`. This gives clearer error messages ("Can't instantiate abstract class X with abstract method Y") at instantiation time rather than at call time.

---

### P3 — Low Priority / Code Smells

#### 7. `icon.py` hardcoded magic string
**File:** `icon.py:43`
Hardcoded check for `obituary.png` -> `green_clover.svg`.

**Recommended fix:** Define a `ICON_REMAPPING: dict[str, str]` dict in `icon.py` or a config file.

#### 8. `rule_container.py:copyRulesDict` creates shallow copies
**File:** `rule_container.py:71-75`
Rules may share mutable state after copy.

**Recommended fix:** Use `copy.deepcopy` on each rule, or document that callers must not mutate copied rules.

#### 9. Missing `__repr__` on many classes
`EventNotifier`, `OccurSet`, `EventRule`, `EventContainer` — no useful `__repr__`, making debugging harder.

**Recommended fix:** Add `__repr__` returning e.g. `f"{self.__class__.__name__}(id={self.id})"`.

#### 10. `event_ics.py` manually constructs ICS format
**File:** `event_ics.py:108 lines`
String concatenation for ICS is fragile. No escaping of special characters beyond `\n` -> `\\n`.

**Recommended fix:** Use a library like `icalendar` for robust ICS generation, or at minimum escape `,`, `;`, and `\` in text fields per RFC 5545.

#### 11. `holder.py` obscures root cause
**File:** `holders.py:132-149`
`delete` catches 3 separate exceptions with `log.exception("")` — hides the actual failure.

**Recommended fix:** Use a single `except (FileNotFoundError, OSError) as e:` with a descriptive log message.

---

## 4. Recommendations (Priority Order)

1. **Add a proper test suite** (#1) — convert `typing_test.py` and add pytest-based tests
2. **Remove dead code** (#2, #4) — `WeekOccurData`, `MonthOccurData`, commented-out blocks
3. **Replace `assert` with proper exceptions** in `handler.py` and `holders.py`
4. **Add docstrings** to public classes and methods
5. **Resolve FIXME comments** or convert them to tracked issues
