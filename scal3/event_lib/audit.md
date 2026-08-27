# Audit Report: `scal3/event_lib/`

**Date:** 2026-08-27
**Total lines:** 9,949 across 50 Python files (40 top-level + 10 in `rules/`)
**License:** AGPL-3.0+
**Last re-audit:** 2026-08-27 (all prior issues re-verified against current code)

See `README.md` for architecture overview and file-by-file summary.

---

## 1. Issues Found

> Issues are sorted by `Priority − Complexity` (higher first). Both are rated 1–5.
> `Priority` = impact on usability/stability, `Complexity` = effort of the solution (1 = trivial, 5 = large).

#### 1. `trash.empty()` swallows deletion failures but clears IDs anyway
**Priority:** 5/5 — **Complexity:** 2/5 (score: 3)
**File:** `trash.py:88-98`

`empty()` catches deletion exceptions (`log.exception`) but unconditionally removes every ID from `idList` and saves, leaving untracked files behind despite the "permanently delete" promise.

**Recommended fix:** Only clear IDs whose file was successfully removed; surface or collect failures instead of swallowing them.

#### 2. `invalidate()` does not prevent future saves
**Priority:** 5/5 — **Complexity:** 2/5 (score: 3)
**File:** `event_base.py:365-375`

Sets `id=None`/`file=""`, but `save()` re-runs `setId()` when `id is None`, allocating a new ID/path and writing the event again — resurrecting an event that was supposed to be deleted.

**Recommended fix:** Track an explicit invalidated state and have `save()` raise/skip when set.

#### 3. `checkForOrphans()` is not merely observational
**Priority:** 4/5 — **Complexity:** 2/5 (score: 2)
**File:** `groups_holder.py:243-306`

Despite its name, `checkForOrphans()` deletes unlisted group files (`fs.removeFile`), persists recovered events (`newEvent.save()`), creates and saves a new group (`newGroup.save()`), appends it, and saves the holder (`self.save()`).

**Recommended fix:** Rename to reflect the mutation (e.g. `recoverOrphans`), or split the read-only detection from the deletion/persistence logic.

#### 4. `setEndDurationDays()` removes the duration rule, not the explicit end rule
**Priority:** 4/5 — **Complexity:** 2/5 (score: 2)
**File:** `task.py:367-372`

It calls `removeSomeRuleTypes("duration")`, discarding an existing duration rule instead of removing any explicit `end`/`date` rule. As a result the documented duration may not become the effective end, and `setJdExact()`'s "one day" promise is not guaranteed.

**Recommended fix:** Remove the end/date rule (and any conflicting rules) before adding the duration rule.

#### 5. `MultiValueAllDayEventRule` claims to match values but always matches
**Priority:** 4/5 — **Complexity:** 2/5 (score: 2)
**File:** `rules/rule_allday.py:62-63`

Docstring says it "matches against a list of individual values or ranges", but it inherits `AllDayEventRule.jdMatches()`, which always returns True. The docstring commit also removed the `# Should not be registered, or instantiate directly` warning.

**Recommended fix:** Override `jdMatches()` to use `hasValue()`, or reword the docstring and restore the warning.

#### 6. `changeCalType()` returns True without changing anything
**Priority:** 3/5 — **Complexity:** 1/5 (score: 2)
**File:** `rules/rule_base.py:85-87`

Documents "Return True if changed", but the base implementation does nothing and returns True, which callers interpret as success.

**Recommended fix:** Have the base return `False` (nothing to convert) or reword the contract to mean "handled successfully".

#### 7. `copyFrom()` checks event type names, not calendar types
**Priority:** 4/5 — **Complexity:** 3/5 (score: 1)
**File:** `event_base.py:386-394`

Docstring says dates are converted when calendar types differ, but the code checks `self.name != other.name` (event type names), not calendar type — so cross-calendar copies may keep unconverted dates.

**Recommended fix:** Compare `calType` values (and perform the JD conversion when they differ), not event type names.

#### 8. `deepConvertTo()` task conversion fails for tag groups
**Priority:** 4/5 — **Complexity:** 3/5 (score: 1)
**File:** `vcs_base.py:192-210`

Asserts `event.epoch is not None`, but `VcsTagEventGroup.getEvent()` builds tag events from only `summary`/`icon` and never sets an epoch, so converting a tag group to a task list asserts.

**Recommended fix:** Set the epoch when building tag events (and commit events) before conversion, or handle `epoch is None`.

#### 9. `university.py:setDefaults` only handles Jalali calendar
**Priority:** 3/5 — **Complexity:** 2/5 (score: 1)
**File:** `university.py:269-291`

No default generation for Gregorian or other calendar types.

**Recommended fix:** Add Gregorian defaults or raise a clear error for unsupported calendar types.

#### 10. `NotImplementedError` / silent no-op used as abstract method signal
**Priority:** 3/5 — **Complexity:** 2/5 (score: 1)
**Files:** `event_base.py` (`index`), `notifier_base.py` (`notify` — now a silent `pass`, no longer `NotImplementedError`), `rules/rule_base.py` (`getServerString`), `vcs_base.py` (`load`)

**Recommended fix:** Make base classes inherit from `abc.ABC` and mark methods with `@abstractmethod`. This gives clearer error messages ("Can't instantiate abstract class X with abstract method Y") at instantiation time rather than at call time. The silent `pass` in `EventNotifier.notify()` is arguably worse than raising — a subclass that forgets to override it silently does nothing.

#### 11. `rule_container.py:copyRulesDict` creates shallow copies
**Priority:** 3/5 — **Complexity:** 2/5 (score: 1)
**File:** `rule_container.py:71-75`
Rules may share mutable state after copy, causing subtle cross-event bugs.

**Recommended fix:** Use `copy.deepcopy` on each rule, or document that callers must not mutate copied rules.

#### 12. `Group.save()` only honors the per-group read-only flag
**Priority:** 3/5 — **Complexity:** 2/5 (score: 1)
**File:** `group.py:342-348`

Docstring promises RuntimeError whenever read-only, but it checks only `self.__readOnly`; global read-only mode (`state.allReadOnly`, used by `isReadOnly()`) silently skips saving, so edits appear to succeed in read-only sessions.

**Recommended fix:** Check `state.allReadOnly` (or call `isReadOnly()`) and raise consistently.

#### 13. `defaultGroupTypeIndex = 0` has unresolved FIXME
**Priority:** 2/5 — **Complexity:** 1/5 (score: 1)
**File:** `__init__.py:152`

**Recommended fix:** Determine the correct default (likely `0` for "NoteBook") and remove the `# FIXME` comment, or make it configurable.

#### 14. `icon.py` hardcoded magic string
**Priority:** 2/5 — **Complexity:** 1/5 (score: 1)
**File:** `icon.py:48-49`
Hardcoded check for `obituary.png` -> `green_clover.svg`.

**Recommended fix:** Define a `ICON_REMAPPING: dict[str, str]` dict in `icon.py` or a config file.

#### 15. `holder.py` obscures root cause
**Priority:** 2/5 — **Complexity:** 1/5 (score: 1)
**File:** `holders.py:132-149`
`delete` catches 3 separate exceptions with `log.exception("")` — hides the actual failure.

**Recommended fix:** Use a single `except (FileNotFoundError, OSError) as e:` with a descriptive log message.

#### 16. `event_ics.py` manually constructs ICS format
**Priority:** 3/5 — **Complexity:** 3/5 (score: 0)
**File:** `event_ics.py:109 lines`
String concatenation for ICS is fragile. No escaping of special characters beyond `\n` -> `\\n`, so exported events can be rejected by other calendar apps.

**Recommended fix:** Use a library like `icalendar` for robust ICS generation, or at minimum escape `,`, `;`, and `\` in text fields per RFC 5545.

#### 17. `AllDayTaskEvent.getEnd()` reports duration as days without checking the unit
**Priority:** 2/5 — **Complexity:** 2/5 (score: 0)
**File:** `task.py:396-404`

**Mostly fixed:** `TaskEvent.getEnd()` now returns `("duration", (value, unit))` — the unit is included (`task.py:220`). For `AllDayTaskEvent`, `getEnd()` still returns a bare `("duration", duration.value)`, which is correct only because every internal setter (`setEndDurationDays`, `setEnd("duration", ...)`) uses `unit = dayLen`.

**Residual risk:** `AllDayTaskEvent` inherits `SingleStartEndEvent.setEndDuration(value, unit)`, so a non-day unit can still be set and would then be reported as days.

**Recommended fix:** Convert the value to days using `duration.unit` in `AllDayTaskEvent.getEnd()`, or restrict the accepted units there.

#### 18. `WeekOccurData` and `MonthOccurData` are unused
**Priority:** 1/5 — **Complexity:** 1/5 (score: 0)
**File:** `occur_data.py`

Both NamedTuple classes are defined but never imported or used anywhere in the codebase.

**Recommended fix:** Remove both classes. If needed in the future, they can be re-added.

#### 19. Missing `__repr__` on some classes
**Priority:** 1/5 — **Complexity:** 1/5 (score: 0)
**Partially fixed since last audit:** `Event` (`event_base.py:153`), `EventGroup` (`group.py:239`), `VcsCommitEvent` (`vcs.py:78`), and all `OccurSet` subclasses (`occur.py`) now have `__repr__`; `EventContainer` has `__str__` (`event_container.py:161`).

**Remaining:** `EventNotifier` and `EventRule` (and their subclasses) still fall back to the default object representation, making debug logs less readable.

**Recommended fix:** Add `__repr__` returning e.g. `f"{self.__class__.__name__}(id={self.id})"` to `EventNotifier` and `EventRule`.

#### 20. `Event.create()` claims to attach the rule but only constructs it
**Priority:** 1/5 — **Complexity:** 1/5 (score: 0)
**File:** `event_base.py:212-217`

Docstring says "Create and attach", but the method only builds and returns the rule; callers must attach it separately.

**Recommended fix:** Either attach the rule inside `create()` or reword the docstring to "create and return".

#### 21. `Handler.init()` does not initialize all subsystems
**Priority:** 1/5 — **Complexity:** 1/5 (score: 0)
**File:** `handler.py:30-39`

Docstring says "Initialize all subsystems", but directories, `state.info`, and `state.lastIds` must be set up by `event_lib.init()` first; `Handler.init()` only loads accounts, groups, trash, and the notifier.

**Recommended fix:** Reconcile responsibilities — either perform full init here or document the prerequisite and narrow the docstring.

#### 22. `typing_test.py` is not a proper test
**Priority:** 2/5 — **Complexity:** 3/5 (score: -1)
**File:** `typing_test.py:101 lines`

Runs code at import level (`print(isinstance(acc, AccountType))`). Contains mostly commented-out code.

**Recommended fix:** Convert to a `pytest` test file with proper test functions, or remove entirely if type checking is handled by `mypy`/`pyright`.

#### 23. Large blocks of commented-out dead code
**Priority:** 1/5 — **Complexity:** 2/5 (score: -1)
**Files:** `event_base.py` (lines 293-299, 300-319, 500-501, 546-567), `__init__.py` (lines 168-188), plus smaller blocks in `group.py`, `university.py`, `vcs_base.py`, `note.py`, `occur.py`

Commented-out TODO classes (`HolidayEventRule`, `ShowInMCalEventRule`, `SunTimeRule`) and disabled methods (`loadFiles`, `getUrlForFile`, `getFilesUrls`).

**Recommended fix:** Remove all commented-out code. If the features are planned, track them as issues instead.

#### ~~24. `LargeScaleEvent.setDefaults` has a wrong `TYPE_CHECKING` assert~~ FIXED
**File:** `large_scale.py:129-133`

Fixed in `a271df76` — the dead `if TYPE_CHECKING` assert is now a real `assert isinstance(group, LargeScaleGroup)`, matching the `group.name == "largeScale"` branch it guards.

#### ~~25. `ObjectsHolderTextModel.getList()` relies on `__bool__` coercion~~ FIXED
**File:** `holders.py:187`

Fixed in `f745f221` — the coupling was resolved by making the contract explicit: `EventGroup.__bool__` now documents "Disabled group must be Falsy" (`group.py:377`), and the `# FIXME` is removed. The disabled-sign logic in `getList()` is now a documented invariant rather than an accidental dependency.

---

## 2. Recommendations (Priority Order)

1. **Add a proper test suite** (#1) — convert `typing_test.py` and add pytest-based tests
2. **Remove dead code** (#2, #4) — `WeekOccurData`, `MonthOccurData`, commented-out blocks
3. **Replace `assert` with proper exceptions** in `handler.py` and `holders.py`
4. **Decouple read-only state** (#20) — make `Group.save()` honor `state.allReadOnly` consistently
5. **Resolve FIXME comments** (105 remaining) or convert them to tracked issues
