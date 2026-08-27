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

#### 12. `checkForOrphans()` is not merely observational
**File:** `groups_holder.py:243-306`

Despite its name, `checkForOrphans()` deletes unlisted group files (`fs.removeFile`), persists recovered events (`newEvent.save()`), creates and saves a new group (`newGroup.save()`), appends it, and saves the holder (`self.save()`).

**Recommended fix:** Rename to reflect the mutation (e.g. `recoverOrphans`), or split the read-only detection from the deletion/persistence logic.

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

#### 13. `trash.empty()` swallows deletion failures but clears IDs anyway
**File:** `trash.py:88-98`

`empty()` catches deletion exceptions (`log.exception`) but unconditionally removes every ID from `idList` and saves, leaving untracked files behind despite the "permanently delete" promise.

**Recommended fix:** Only clear IDs whose file was successfully removed; surface or collect failures instead of swallowing them.

#### 14. `setEndDurationDays()` removes the duration rule, not the explicit end rule
**File:** `task.py:367-372`

It calls `removeSomeRuleTypes("duration")`, discarding an existing duration rule instead of removing any explicit `end`/`date` rule. As a result the documented duration may not become the effective end, and `setJdExact()`'s "one day" promise is not guaranteed.

**Recommended fix:** Remove the end/date rule (and any conflicting rules) before adding the duration rule.

#### 15. `getEnd()` labels duration as days without checking the unit
**File:** `task.py:396-404`

Returns `("duration", duration.value)` described as days, but `DurationEventRule.value` is combined with `.unit` (seconds/minutes/hours/weeks). A non-day unit is reported as if it were days.

**Recommended fix:** Convert the value to days using `duration.unit`, or return the unit alongside the value.

#### 16. `Event.create()` claims to attach the rule but only constructs it
**File:** `event_base.py:212-217`

Docstring says "Create and attach", but the method only builds and returns the rule; callers must attach it separately.

**Recommended fix:** Either attach the rule inside `create()` or reword the docstring to "create and return".

#### 17. `invalidate()` does not prevent future saves
**File:** `event_base.py:365-375`

Sets `id=None`/`file=""`, but `save()` re-runs `setId()` when `id is None`, allocating a new ID/path and writing the event again.

**Recommended fix:** Track an explicit invalidated state and have `save()` raise/skip when set.

#### 18. `copyFrom()` checks event type names, not calendar types
**File:** `event_base.py:386-394`

Docstring says dates are converted when calendar types differ, but the code checks `self.name != other.name` (event type names), not calendar type.

**Recommended fix:** Compare `calType` values (and perform the JD conversion when they differ), not event type names.

#### 19. `changeCalType()` returns True without changing anything
**File:** `rules/rule_base.py:85-87`

Documents "Return True if changed", but the base implementation does nothing and returns True, which callers interpret as success.

**Recommended fix:** Have the base return `False` (nothing to convert) or reword the contract to mean "handled successfully".

#### 20. `Group.save()` only honors the per-group read-only flag
**File:** `group.py:342-348`

Docstring promises RuntimeError whenever read-only, but it checks only `self.__readOnly`; global read-only mode (`state.allReadOnly`, used by `isReadOnly()`) silently skips saving.

**Recommended fix:** Check `state.allReadOnly` (or call `isReadOnly()`) and raise consistently.

#### 21. `Handler.init()` does not initialize all subsystems
**File:** `handler.py:30-39`

Docstring says "Initialize all subsystems", but directories, `state.info`, and `state.lastIds` must be set up by `event_lib.init()` first; `Handler.init()` only loads accounts, groups, trash, and the notifier.

**Recommended fix:** Reconcile responsibilities — either perform full init here or document the prerequisite and narrow the docstring.

#### 22. `deepConvertTo()` task conversion fails for tag groups
**File:** `vcs_base.py:192-210`

Asserts `event.epoch is not None`, but `VcsTagEventGroup.getEvent()` builds tag events from only `summary`/`icon` and never sets an epoch, so the conversion asserts for tag groups.

**Recommended fix:** Set the epoch when building tag events (and commit events) before conversion, or handle `epoch is None`.

#### 23. `MultiValueAllDayEventRule` claims to match values but always matches
**File:** `rules/rule_allday.py:62-63`

Docstring says it "matches against a list of individual values or ranges", but it inherits `AllDayEventRule.jdMatches()`, which always returns True. The docstring commit also removed the `# Should not be registered, or instantiate directly` warning.

**Recommended fix:** Override `jdMatches()` to use `hasValue()`, or reword the docstring and restore the warning.

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
