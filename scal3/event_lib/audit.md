# Audit Report: `scal3/event_lib/`

**Date:** 2026-08-27
**License:** AGPL-3.0+
**Last re-audit:** 2026-09-13 (all prior issues re-verified against current code; line references updated)

See `README.md` for architecture overview and file-by-file summary.

---

## 1. Issues Found

> Issues are sorted by `Priority − Complexity` (higher first). Both are rated 1–5.
> `Priority` = impact on usability/stability, `Complexity` = effort of the solution (1 = trivial, 5 = large).

#### ~~1. `MultiValueAllDayEventRule` claims to match values but always matches~~ FIXED
**File:** `rules/rule_allday.py:62-70`

`MultiValueAllDayEventRule` is now explicitly an abstract base: the `# Should not be registered, or instantiate directly` warning is restored, the docstring clarifies that subclasses define which calendar component the values represent, and its `jdMatches()` raises `NotImplementedError` instead of silently inheriting the always-True `AllDayEventRule.jdMatches()`.

#### ~~2. `changeCalType()` returns True without changing anything~~ FIXED
**File:** `rules/rule_base.py:87-89`

The docstring now states the contract correctly: `changeCalType()` returns `True` if the conversion was successful, not whether anything changed. All overrides (`rule_date.py`, `rule_ymd.py`, `rule_allday.py`) and the caller in `event_base.py:585` document the same semantics.

#### ~~3. `copyFrom()` checks event type names, not calendar types~~ FIXED
**Priority:** 4/5 — **Complexity:** 3/5 (score: 1)
**File:** `event_base.py:399-407`

`copyFrom()` and `copyFromExact()` now also check `self.calType != other.calType` (in addition to the existing event-type-name check), so dates are converted (via JD) when the source and target calendar types differ, while the name check still re-derives dates when event types use different rule representations (e.g. `dailyNote` → `task`). `Event.setJd()` (base) now delegates to the `date`/`start` rule so the conversion also works for generic rule-based events (e.g. `CustomEvent`); events with their own `setJd` override are unchanged.

#### ~~4. `deepConvertTo()` task conversion fails for tag groups~~ FIXED
**File:** `vcs_base.py:195-213`

`VcsEpochBaseEventGroup` now records each VCS id's epoch in `_addOccur()` and exposes it via `getEventEpoch()`. `VcsCommitEventGroup.getEvent()` and `VcsTagEventGroup.getEvent()` set `event.epoch` from it, and `deepConvertTo()` skips (with a warning) any event still lacking an epoch instead of asserting.

#### ~~5. `UniversityTerm.setDefaults()` only handles Jalali calendar~~ COMMENTED, NOT NEEEDED
**Priority:** 3/5 — **Complexity:** 2/5 (score: 1)
**File:** `university.py:267-290`

No default generation for Gregorian or other calendar types.

**Recommended fix:** Add Gregorian defaults or raise a clear error for unsupported calendar types.

#### ~~6. `NotImplementedError` / silent no-op used as abstract method signal~~ FIXED
**Priority:** 3/5 — **Complexity:** 2/5 (score: 1)

`EventNotifier` and `EventRule` now inherit from `abc.ABC`, and `notify()` / `getServerString()` are `@abstractmethod` — a subclass that forgets to override them fails at instantiation instead of silently no-op'ing. The dead `Event.index()` stub was removed (the real `index()` lives on `EventContainer`, `event_container.py:310`), and the dead `VcsEpochBaseEvent.load()` stub was removed (VCS events are virtual and never loaded; `Event` itself defines no `load`). `AllDayEventRule.getServerString()` returns `""` (matches every day, no values) so its unregistered abstract bases remain instantiable.

#### 7. `rule_container.py:copyRulesDict` creates shallow copies
**Priority:** 3/5 — **Complexity:** 2/5 (score: 1)
**File:** `rule_container.py:72-78`
Rules may share mutable state after copy, causing subtle cross-event bugs.

**Recommended fix:** Use `copy.deepcopy` on each rule, or document that callers must not mutate copied rules.

#### ~~8. `Group.save()` only honors the per-group read-only flag~~ FIXED
`Group.save()` now checks `isReadOnly()` (which includes `state.allReadOnly`), so it raises RuntimeError consistently in global read-only mode.

#### 9. `defaultGroupTypeIndex = 0` has unresolved FIXME
**Priority:** 2/5 — **Complexity:** 1/5 (score: 1)
**File:** `__init__.py:156`

**Recommended fix:** Determine the correct default (likely `0` for "NoteBook") and remove the `# FIXME` comment, or make it configurable.

#### 10. `icon.py` hardcoded magic string
**Priority:** 2/5 — **Complexity:** 1/5 (score: 1)
**File:** `icon.py:48-49`
Hardcoded check for `obituary.png` -> `green_clover.svg`.

**Recommended fix:** Define a `ICON_REMAPPING: dict[str, str]` dict in `icon.py` or a config file.

#### 11. `holder.py` obscures root cause
**Priority:** 2/5 — **Complexity:** 1/5 (score: 1)
**File:** `holders.py:141-159`
`delete` catches 3 separate exceptions with `log.exception("")` — hides the actual failure.

**Recommended fix:** Use a single `except (FileNotFoundError, OSError) as e:` with a descriptive log message.

#### 12. `event_ics.py` manually constructs ICS format
**Priority:** 3/5 — **Complexity:** 3/5 (score: 0)
**File:** `event_ics.py:109 lines`
String concatenation for ICS is fragile. No escaping of special characters beyond `\n` -> `\\n`, so exported events can be rejected by other calendar apps.

**Recommended fix:** Use a library like `icalendar` for robust ICS generation, or at minimum escape `,`, `;`, and `\` in text fields per RFC 5545.

#### 13. `AllDayTaskEvent.getEnd()` reports duration as days without checking the unit
**Priority:** 2/5 — **Complexity:** 2/5 (score: 0)
**File:** `task.py:400-408`

**Mostly fixed:** `TaskEvent.getEnd()` now returns `("duration", (value, unit))` — the unit is included (`task.py:209-222`). For `AllDayTaskEvent`, `getEnd()` still returns a bare `("duration", duration.value)`, which is correct only because every internal setter (`setEndDurationDays`, `_setEnd("duration", ...)` at `task.py:391-393`) uses `unit = dayLen`.

**Residual risk:** `AllDayTaskEvent` inherits `SingleStartEndEvent.setEndDuration(value, unit)`, so a non-day unit can still be set and would then be reported as days.

**Recommended fix:** Convert the value to days using `duration.unit` in `AllDayTaskEvent.getEnd()`, or restrict the accepted units there.

#### 14. `WeekOccurData` and `MonthOccurData` are unused
**Priority:** 1/5 — **Complexity:** 1/5 (score: 0)
**File:** `occur_data.py`

Both NamedTuple classes are defined but never imported or used anywhere in the codebase.

**Recommended fix:** Remove both classes. If needed in the future, they can be re-added.

#### 15. Missing `__repr__` on some classes
**Priority:** 1/5 — **Complexity:** 1/5 (score: 0)
**Partially fixed since last audit:** `Event` (`event_base.py:153`), `EventGroup` (`group.py:247`), `VcsCommitEvent` (`vcs.py:78`), and all `OccurSet` subclasses (`occur.py`) now have `__repr__`; `EventContainer` has `__str__` (`event_container.py:167`).

**Remaining:** `EventNotifier` and `EventRule` (and their subclasses) still fall back to the default object representation, making debug logs less readable.

**Recommended fix:** Add `__repr__` returning e.g. `f"{self.__class__.__name__}(id={self.id})"` to `EventNotifier` and `EventRule`.

#### 16. `Event.create()` claims to attach the rule but only constructs it
**Priority:** 1/5 — **Complexity:** 1/5 (score: 0)
**File:** `event_base.py:214-219`

Docstring says "Create and attach", but the method only builds and returns the rule; callers must attach it separately.

**Recommended fix:** Either attach the rule inside `create()` or reword the docstring to "create and return".

#### 17. `Handler.init()` does not initialize all subsystems
**Priority:** 1/5 — **Complexity:** 1/5 (score: 0)
**File:** `handler.py:34-46`

Docstring says "Initialize all subsystems", but directories, `state.info`, and `state.lastIds` must be set up by `event_lib.init()` first; `Handler.init()` only loads accounts, groups, trash, and the notifier.

**Recommended fix:** Reconcile responsibilities — either perform full init here or document the prerequisite and narrow the docstring.

#### 18. `typing_test.py` is not a proper test
**Priority:** 2/5 — **Complexity:** 3/5 (score: -1)
**File:** `typing_test.py:101 lines`

Runs code at import level (`print(isinstance(acc, AccountType))`). Contains mostly commented-out code.

**Recommended fix:** Convert to a `pytest` test file with proper test functions, or remove entirely if type checking is handled by `mypy`/`pyright`.

#### 19. Large blocks of commented-out dead code
**Priority:** 1/5 — **Complexity:** 2/5 (score: -1)
**Files:** `event_base.py` (lines 297-303, 304-311, 514-515, 563-582), `__init__.py` (lines 168-191), plus smaller blocks in `group.py`, `university.py`, `vcs_base.py`, `note.py`, `occur.py`

Commented-out TODO classes (`HolidayEventRule`, `ShowInMCalEventRule`, `SunTimeRule`), the no-op attachment loader (`_loadFiles`), and commented-out methods (`getUrlForFile`, `getFilesUrls`).

**Recommended fix:** Remove all commented-out code. If the features are planned, track them as issues instead.

---

## 2. Recommendations (Priority Order)

- **Add a proper test suite** (#18) — convert `typing_test.py` and add pytest-based tests
- **Remove dead code** (#14, #19) — `WeekOccurData`, `MonthOccurData`, commented-out blocks
- **Replace `assert` with proper exceptions** in `handler.py` and `holders.py`
- **Resolve FIXME comments** (109 remaining) or convert them to tracked issues
