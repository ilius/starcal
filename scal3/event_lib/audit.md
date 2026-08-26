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

| File | Lines | Purpose |
|---|---|---|
| `__init__.py` | 188 | Package init, global `ev` Handler, `init()`, `removeUnusedObjects()` |
| `event_base.py` | 703 | Core `Event` and `SingleStartEndEvent` classes |
| `group.py` | 791 | `EventGroup` — main event container with caching, search, import/export |
| `university.py` | 582 | University term scheduling (classes, exams, weekly schedule) |
| `task.py` | 432 | Task events and all-day tasks |
| `event_container.py` | 392 | Base container for events (holds event ID lists) |
| `vcs.py` | 378 | VCS commit/tag/daily-stat event groups |
| `pytypes.py` | 340 | Protocol definitions for all major types |
| `rules/rule_week.py` | 303 | Week-based rules (weekday, week-month, week number) |
| `yearly.py` | 292 | Yearly recurring events (birthdays, anniversaries) |
| `occur.py` | 291 | Occurrence set types (JD, interval, time-list) |
| `groups_holder.py` | 295 | Manages list of all event groups |
| `rule_container.py` | 262 | Mixin for objects containing rules |
| `vcs_base.py` | 238 | Base classes for VCS event groups |
| `large_scale.py` | 238 | Large-scale (millennia/centuries) events |
| `rules/rule_cycle.py` | 228 | Cycle-based recurrence rules |
| `accounts.py` | 179 | Account base class |
| `holders.py` | 180 | Generic container for ordered collections |
| `rules/rule_date.py` | 178 | Date rules and exclusion dates |
| `rules/rule_daytime.py` | 173 | Time-within-day rules |
| `rules/rule_datetime.py` | 171 | Date+time rules |
| `rules/rule_ymd.py` | 169 | Year/month/day matching rules |
| `lifetime.py` | 148 | Lifetime (birth-death) events |
| `occur_data.py` | 142 | Day/week/month occurrence data computation |
| `rules/rule_duration.py` | 143 | Duration-based rule |
| `accounts_holder.py` | 129 | Account loading/storing |
| `note.py` | 129 | Daily notes (notebook) |
| `notifiers.py` | 122 | Concrete notifier implementations |
| `rules/rule_allday.py` | 102 | All-day event matching rules |
| `monthly.py` | 112 | Monthly recurring events |
| `state.py` | 112 | Global mutable state (`allReadOnly`, `info`, `lastIds`) |
| `rules/rule_base.py` | 117 | Base `EventRule` class |
| `event_ics.py` | 108 | ICS format export |
| `typing_test.py` | 101 | Ad-hoc type checking (not a real test suite) |
| `trash.py` | 94 | Trash container for deleted events |
| `common.py` | 92 | Shared utilities (week days, JD, compression) |
| `weekly.py` | 91 | Weekly recurring events |
| `events.py` | 58 | Registers `CustomEvent` type |
| `handler.py` | 77 | Facade wrapping accounts, groups, trash |
| `register.py` | 70 | Class registry system |
| `patch.py` | 67 | Patch list creation for sync |
| `groups_import.py` | 52 | Import mode constants |
| `icon.py` | 51 | Icon path handling |
| `rules/__init__.py` | 50 | Re-exports all rule classes |
| `objects.py` | 84 | Binary model for history-tracked objects |
| `notifier_base.py` | 56 | Base notifier class |
| `object_base.py` | 38 | Read-only respecting text model |
| `errors.py` | 5 | `AccountError` exception |
| `exceptions.py` | 5 | `BadEventFile` exception |

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
