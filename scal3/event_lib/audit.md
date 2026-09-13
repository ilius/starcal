# Audit Report: `scal3/event_lib/`

**Date:** 2026-08-27
**License:** AGPL-3.0+
**Last re-audit:** 2026-09-13 (all prior issues re-verified against current code; line references updated)

See `README.md` for architecture overview and file-by-file summary.

---

## 1. Issues Found

> Issues are sorted by `Priority − Complexity` (higher first). Both are rated 1–5.
> `Priority` = impact on usability/stability, `Complexity` = effort of the solution (1 = trivial, 5 = large).

#### ~~1. `rule_container.py:copyRulesDict` creates shallow copies~~ FIXED
**Priority:** 3/5 — **Complexity:** 2/5 (score: 1)
**File:** `rule_container.py:72-78`
`copyRulesDict` now deep-copies each rule via `copy.deepcopy`, and `EventRule.__deepcopy__` (in `rule_base.py`) deep-copies all instance state while keeping the same `parent`, so mutable and derived rule state (e.g. `ExDatesEventRule.jdList`) is no longer shared or dropped. Regression test added in `rules_test.py:test_copy_rules_dict_deep_copies`.

#### 2. `icon.py` hardcoded magic string
**Priority:** 2/5 — **Complexity:** 1/5 (score: 1)
**File:** `icon.py:48-49`
Hardcoded check for `obituary.png` -> `green_clover.svg`.

**Recommended fix:** Define a `ICON_REMAPPING: dict[str, str]` dict in `icon.py` or a config file.

#### ~~3. `AllDayTaskEvent.getEnd()` reports duration as days without checking the unit~~ FIXED
**Priority:** 2/5 — **Complexity:** 2/5 (score: 0)
**File:** `task.py:400-408`

**Fix:** `AllDayTaskEvent.getEnd()` now converts the duration to days using `duration.unit` (`task.py:407`): it returns `("duration", duration.value * duration.unit / dayLen)`. Non-day units set via the inherited `SingleStartEndEvent.setEndDuration(value, unit)` are now reported correctly as days. Covered by a test in `events_test.py` (`setEndDuration(48, 3600)` → `("duration", 2)`).

#### ~~4. `WeekOccurData` and `MonthOccurData` are unused~~ FIXED
**Priority:** 1/5 — **Complexity:** 1/5 (score: 0)
**File:** `occur_data.py`

Both NamedTuple classes are defined but never imported or used anywhere in the codebase.

**Recommended fix:** Remove both classes. If needed in the future, they can be re-added.

#### ~~5. Missing `__repr__` on some classes~~ FIXED
**Priority:** 1/5 — **Complexity:** 1/5 (score: 0)
**Fix:** `EventNotifier` (`notifier_base.py`) now has `__repr__` returning `EventNotifier(event=...)`, and `EventRule` (`rules/rule_base.py`) has `__repr__` returning `EventRule(parent=...)`; subclasses inherit both. Rules and notifiers have no `id` attribute, so the reprs use `event`/`parent` instead. Covered by `test_event_notifier_repr` (`events_test.py`) and `test_rule_repr` (`rules_test.py`).

#### 6. `Event.create()` claims to attach the rule but only constructs it
**Priority:** 1/5 — **Complexity:** 1/5 (score: 0)
**File:** `event_base.py:214-219`

Docstring says "Create and attach", but the method only builds and returns the rule; callers must attach it separately.

**Recommended fix:** Either attach the rule inside `create()` or reword the docstring to "create and return".

#### 7. `Handler.init()` does not initialize all subsystems
**Priority:** 1/5 — **Complexity:** 1/5 (score: 0)
**File:** `handler.py:34-46`

Docstring says "Initialize all subsystems", but directories, `state.info`, and `state.lastIds` must be set up by `event_lib.init()` first; `Handler.init()` only loads accounts, groups, trash, and the notifier.

**Recommended fix:** Reconcile responsibilities — either perform full init here or document the prerequisite and narrow the docstring.

#### 8. `typing_test.py` is not a proper test
**Priority:** 2/5 — **Complexity:** 3/5 (score: -1)
**File:** `typing_test.py:101 lines`

Runs code at import level (`print(isinstance(acc, AccountType))`). Contains mostly commented-out code.

**Recommended fix:** Convert to a `pytest` test file with proper test functions, or remove entirely if type checking is handled by `mypy`/`pyright`.

#### 9. Large blocks of commented-out dead code
**Priority:** 1/5 — **Complexity:** 2/5 (score: -1)
**Files:** `event_base.py` (lines 297-303, 304-311, 514-515, 563-582), `__init__.py` (lines 168-191), plus smaller blocks in `group.py`, `university.py`, `vcs_base.py`, `note.py`, `occur.py`

Commented-out TODO classes (`HolidayEventRule`, `ShowInMCalEventRule`, `SunTimeRule`), the no-op attachment loader (`_loadFiles`), and commented-out methods (`getUrlForFile`, `getFilesUrls`).

**Recommended fix:** Remove all commented-out code. If the features are planned, track them as issues instead.

---

## 2. Recommendations (Priority Order)

- **Add a proper test suite** (#8) — convert `typing_test.py` and add pytest-based tests
- **Remove dead code** (#4, #9) — `WeekOccurData`, `MonthOccurData`, commented-out blocks
- **Replace `assert` with proper exceptions** in `handler.py` and `holders.py`
- **Resolve FIXME comments** (109 remaining) or convert them to tracked issues
