# Audit Report: `scal3/event_lib/`

**Date:** 2026-08-27
**License:** AGPL-3.0+
**Last re-audit:** 2026-08-27 (all prior issues re-verified against current code)

See `README.md` for architecture overview and file-by-file summary.

---

## 1. Issues Found

> Issues are sorted by `Priority − Complexity` (higher first). Both are rated 1–5.
> `Priority` = impact on usability/stability, `Complexity` = effort of the solution (1 = trivial, 5 = large).

#### 1. `MultiValueAllDayEventRule` claims to match values but always matches
**Priority:** 4/5 — **Complexity:** 2/5 (score: 2)
**File:** `rules/rule_allday.py:62-63`

Docstring says it "matches against a list of individual values or ranges", but it inherits `AllDayEventRule.jdMatches()`, which always returns True. The docstring commit also removed the `# Should not be registered, or instantiate directly` warning.

**Recommended fix:** Override `jdMatches()` to use `hasValue()`, or reword the docstring and restore the warning.

#### 2. `changeCalType()` returns True without changing anything
**Priority:** 3/5 — **Complexity:** 1/5 (score: 2)
**File:** `rules/rule_base.py:85-87`

Documents "Return True if changed", but the base implementation does nothing and returns True, which callers interpret as success.

**Recommended fix:** Have the base return `False` (nothing to convert) or reword the contract to mean "handled successfully".

#### 3. `copyFrom()` checks event type names, not calendar types
**Priority:** 4/5 — **Complexity:** 3/5 (score: 1)
**File:** `event_base.py:386-394`

Docstring says dates are converted when calendar types differ, but the code checks `self.name != other.name` (event type names), not calendar type — so cross-calendar copies may keep unconverted dates.

**Recommended fix:** Compare `calType` values (and perform the JD conversion when they differ), not event type names.

#### 4. `deepConvertTo()` task conversion fails for tag groups
**Priority:** 4/5 — **Complexity:** 3/5 (score: 1)
**File:** `vcs_base.py:192-210`

Asserts `event.epoch is not None`, but `VcsTagEventGroup.getEvent()` builds tag events from only `summary`/`icon` and never sets an epoch, so converting a tag group to a task list asserts.

**Recommended fix:** Set the epoch when building tag events (and commit events) before conversion, or handle `epoch is None`.

#### 5. `university.py:setDefaults` only handles Jalali calendar
**Priority:** 3/5 — **Complexity:** 2/5 (score: 1)
**File:** `university.py:269-291`

No default generation for Gregorian or other calendar types.

**Recommended fix:** Add Gregorian defaults or raise a clear error for unsupported calendar types.

#### 6. `NotImplementedError` / silent no-op used as abstract method signal
**Priority:** 3/5 — **Complexity:** 2/5 (score: 1)
**Files:** `event_base.py` (`index`), `notifier_base.py` (`notify` — now a silent `pass`, no longer `NotImplementedError`), `rules/rule_base.py` (`getServerString`), `vcs_base.py` (`load`)

**Recommended fix:** Make base classes inherit from `abc.ABC` and mark methods with `@abstractmethod`. This gives clearer error messages ("Can't instantiate abstract class X with abstract method Y") at instantiation time rather than at call time. The silent `pass` in `EventNotifier.notify()` is arguably worse than raising — a subclass that forgets to override it silently does nothing.

#### 7. `rule_container.py:copyRulesDict` creates shallow copies
**Priority:** 3/5 — **Complexity:** 2/5 (score: 1)
**File:** `rule_container.py:71-75`
Rules may share mutable state after copy, causing subtle cross-event bugs.

**Recommended fix:** Use `copy.deepcopy` on each rule, or document that callers must not mutate copied rules.

#### ~~8. `Group.save()` only honors the per-group read-only flag~~ FIXED
`Group.save()` now checks `isReadOnly()` (which includes `state.allReadOnly`), so it raises RuntimeError consistently in global read-only mode.

#### 9. `defaultGroupTypeIndex = 0` has unresolved FIXME
**Priority:** 2/5 — **Complexity:** 1/5 (score: 1)
**File:** `__init__.py:152`

**Recommended fix:** Determine the correct default (likely `0` for "NoteBook") and remove the `# FIXME` comment, or make it configurable.

#### 10. `icon.py` hardcoded magic string
**Priority:** 2/5 — **Complexity:** 1/5 (score: 1)
**File:** `icon.py:48-49`
Hardcoded check for `obituary.png` -> `green_clover.svg`.

**Recommended fix:** Define a `ICON_REMAPPING: dict[str, str]` dict in `icon.py` or a config file.

#### 11. `holder.py` obscures root cause
**Priority:** 2/5 — **Complexity:** 1/5 (score: 1)
**File:** `holders.py:132-149`
`delete` catches 3 separate exceptions with `log.exception("")` — hides the actual failure.

**Recommended fix:** Use a single `except (FileNotFoundError, OSError) as e:` with a descriptive log message.

#### 12. `event_ics.py` manually constructs ICS format
**Priority:** 3/5 — **Complexity:** 3/5 (score: 0)
**File:** `event_ics.py:109 lines`
String concatenation for ICS is fragile. No escaping of special characters beyond `\n` -> `\\n`, so exported events can be rejected by other calendar apps.

**Recommended fix:** Use a library like `icalendar` for robust ICS generation, or at minimum escape `,`, `;`, and `\` in text fields per RFC 5545.

#### 13. `AllDayTaskEvent.getEnd()` reports duration as days without checking the unit
**Priority:** 2/5 — **Complexity:** 2/5 (score: 0)
**File:** `task.py:396-404`

**Mostly fixed:** `TaskEvent.getEnd()` now returns `("duration", (value, unit))` — the unit is included (`task.py:220`). For `AllDayTaskEvent`, `getEnd()` still returns a bare `("duration", duration.value)`, which is correct only because every internal setter (`setEndDurationDays`, `_setEnd("duration", ...)`) uses `unit = dayLen`.

**Residual risk:** `AllDayTaskEvent` inherits `SingleStartEndEvent.setEndDuration(value, unit)`, so a non-day unit can still be set and would then be reported as days.

**Recommended fix:** Convert the value to days using `duration.unit` in `AllDayTaskEvent.getEnd()`, or restrict the accepted units there.

#### 14. `WeekOccurData` and `MonthOccurData` are unused
**Priority:** 1/5 — **Complexity:** 1/5 (score: 0)
**File:** `occur_data.py`

Both NamedTuple classes are defined but never imported or used anywhere in the codebase.

**Recommended fix:** Remove both classes. If needed in the future, they can be re-added.

#### 15. Missing `__repr__` on some classes
**Priority:** 1/5 — **Complexity:** 1/5 (score: 0)
**Partially fixed since last audit:** `Event` (`event_base.py:153`), `EventGroup` (`group.py:239`), `VcsCommitEvent` (`vcs.py:78`), and all `OccurSet` subclasses (`occur.py`) now have `__repr__`; `EventContainer` has `__str__` (`event_container.py:161`).

**Remaining:** `EventNotifier` and `EventRule` (and their subclasses) still fall back to the default object representation, making debug logs less readable.

**Recommended fix:** Add `__repr__` returning e.g. `f"{self.__class__.__name__}(id={self.id})"` to `EventNotifier` and `EventRule`.

#### 16. `Event.create()` claims to attach the rule but only constructs it
**Priority:** 1/5 — **Complexity:** 1/5 (score: 0)
**File:** `event_base.py:212-217`

Docstring says "Create and attach", but the method only builds and returns the rule; callers must attach it separately.

**Recommended fix:** Either attach the rule inside `create()` or reword the docstring to "create and return".

#### 17. `Handler.init()` does not initialize all subsystems
**Priority:** 1/5 — **Complexity:** 1/5 (score: 0)
**File:** `handler.py:30-39`

Docstring says "Initialize all subsystems", but directories, `state.info`, and `state.lastIds` must be set up by `event_lib.init()` first; `Handler.init()` only loads accounts, groups, trash, and the notifier.

**Recommended fix:** Reconcile responsibilities — either perform full init here or document the prerequisite and narrow the docstring.

#### 18. `typing_test.py` is not a proper test
**Priority:** 2/5 — **Complexity:** 3/5 (score: -1)
**File:** `typing_test.py:101 lines`

Runs code at import level (`print(isinstance(acc, AccountType))`). Contains mostly commented-out code.

**Recommended fix:** Convert to a `pytest` test file with proper test functions, or remove entirely if type checking is handled by `mypy`/`pyright`.

#### 19. Large blocks of commented-out dead code
**Priority:** 1/5 — **Complexity:** 2/5 (score: -1)
**Files:** `event_base.py` (lines 293-299, 300-319, 500-501, 546-567), `__init__.py` (lines 168-188), plus smaller blocks in `group.py`, `university.py`, `vcs_base.py`, `note.py`, `occur.py`

Commented-out TODO classes (`HolidayEventRule`, `ShowInMCalEventRule`, `SunTimeRule`) and disabled methods (`loadFiles`, `getUrlForFile`, `getFilesUrls`).

**Recommended fix:** Remove all commented-out code. If the features are planned, track them as issues instead.

---

## 2. Recommendations (Priority Order)

- **Add a proper test suite** (#18) — convert `typing_test.py` and add pytest-based tests
- **Remove dead code** (#14, #19) — `WeekOccurData`, `MonthOccurData`, commented-out blocks
- **Replace `assert` with proper exceptions** in `handler.py` and `holders.py`
- **Resolve FIXME comments** (105 remaining) or convert them to tracked issues

---

## 3. Public-Method Review: Internal-Only Candidates

Public methods (defined without a leading `_`) in `event_lib` that are **not referenced anywhere outside** `scal3/event_lib` (searched `scal3/`, `plugins/`, and `tools/` for `.<name>` call sites). Each is a candidate for making private (`_`-prefixed). A method may be made private safely even when called by other classes inside `event_lib`; a single underscore does not trigger name mangling.

> Notes:
> - Test functions in `occur_test.py` (`test_*`) are excluded — they are entry points, not internals.
> - `pytypes.py` `Protocol` members (e.g. `EventType.getV4Dict`, `RuleContainerType.getRule`) are excluded here — they are structural typing stubs. When any method below is renamed, its mirror member in `pytypes.py` must be renamed to match.
> - Renaming a method defined in a base class (e.g. `EventRule.calcOccurrence`, `OccurSet.getDaysJdList`) requires renaming every override in subclasses and every call site inside `event_lib`.


### Methods with unrepeated names

- [ ] `event_base.py:303` — `Event.loadFiles`
- [ ] `event_base.py:470` — `Event.getNotifiersData`
- [ ] `event_container.py:261` — `EventContainer.preAdd`
- [ ] `event_container.py:347` — `EventContainer.getEventNoCache`
- [ ] `group.py:317` — `EventGroup.clearCache`
- [ ] `group.py:331` — `EventGroup.clearRemoteAttrs`
- [ ] `group.py:361` — `EventGroup.getSyncDurationSec`
- [ ] `group.py:408` — `EventGroup.setColor`
- [ ] `group.py:470` — `EventGroup.setToCache`
- [ ] `group.py:563` — `EventGroup.copyAs`
- [ ] `group.py:597` — `EventGroup.calcGroupOccurrences`
- [ ] `group.py:639` — `EventGroup.initOccurrence`
- [ ] `group.py:663` — `EventGroup.updateOccurrenceLog`
- [ ] `group.py:728` — `EventGroup.loadEventIdByUuid`
- [ ] `group.py:740` — `EventGroup.appendByData`
- [ ] `groups_holder.py:76` — `EventGroupsHolder.setTrash`
- [ ] `holders.py:194` — `ObjectsHolderTextModel.getList`
- [ ] `icon.py:30` — `WithIcon.iconRelativeToAbsInObj`
- [ ] `objects.py:46` — `HistoryEventObjBinaryModel.set_uuid`
- [ ] `occur.py:227` — `IntervalOccurSet.newFromStartEnd`
- [ ] `register.py:60` — `ClassGroup.setMain`
- [ ] `rule_container.py:73` — `RuleContainer.copyRulesDict`
- [ ] `rule_container.py:96` — `RuleContainer.setRule`
- [ ] `rule_container.py:100` — `RuleContainer.iterRulesData`
- [ ] `rule_container.py:105` — `RuleContainer.getRulesData`
- [ ] `rule_container.py:120` — `RuleContainer.getRuleNames`
- [ ] `rule_container.py:128` — `RuleContainer.addNewRule`
- [ ] `rule_container.py:143` — `RuleContainer.removeRule`
- [ ] `rule_container.py:159` — `RuleContainer.setRulesData`
- [ ] `rule_container.py:167` — `RuleContainer.addRequirements`
- [ ] `rule_container.py:180` — `RuleContainer.removeSomeRuleTypes`
- [ ] `rule_container.py:235` — `RuleContainer.copyRulesFrom`
- [ ] `rule_container.py:242` — `RuleContainer.copySomeRuleTypesFrom`
- [ ] `rule_container.py:280` — `RuleContainer.getJdFromEpoch`
- [ ] `rules/rule_allday.py:87` — `MultiValueAllDayEventRule.hasValue`
- [ ] `rules/rule_datetime.py:73` — `DateAndTimeEventRule.setEpoch`
- [ ] `rules/rule_daytime.py:145` — `DayTimeRangeEventRule.getHourRange`
- [ ] `rules/rule_daytime.py:152` — `DayTimeRangeEventRule.getSecondsRange`
- [ ] `rules/rule_duration.py:77` — `DurationEventRule.getUnitDesc`
- [ ] `rules/rule_duration.py:91` — `DurationEventRule.getUnitSymbol`
- [ ] `rules/rule_duration.py:106` — `DurationEventRule.getSeconds`
- [ ] `rules/rule_duration.py:110` — `DurationEventRule.setSeconds`
- [ ] ~~`rules/rule_ymd.py:65` — `YearEventRule.newCalTypeValues`~~ (renamed `_newCalTypeValues`)
- [ ] `state.py:100` — `LastIdsWrapper.scanDir`
- [ ] `state.py:115` — `LastIdsWrapper.scan`
- [ ] `task.py:434` — `AllDayTaskEvent.setEndJd`
- [ ] `university.py:418` — `UniversityClassEvent.getWeekDayName`
- [ ] ~~`vcs_base.py:122` — `VcsBaseEventGroup.getVcsModule`~~ (renamed `_getVcsModule`)
- [ ] ~~`vcs_base.py:136` — `VcsBaseEventGroup.updateVcsModuleObj`~~ (renamed `_updateVcsModuleObj`)


### `getSortByValue` (6)
- [ ] `event_container.py:378` — `EventContainer.getSortByValue`
- [ ] `large_scale.py:194` — `LargeScaleGroup.getSortByValue`
- [ ] `lifetime.py:63` — `LifetimeGroup.getSortByValue`
- [ ] `note.py:59` — `NoteBook.getSortByValue`
- [ ] `task.py:78` — `TaskList.getSortByValue`
- [ ] `university.py:118` — `UniversityTerm.getSortByValue`

### ~~`setJdExact` (1)~~ RENAMED for events
- [ ] ~~`event_base.py:647` — `Event.setJdExact`~~ (renamed `_setJdExact`)
- [ ] ~~`event_base.py:715` — `SingleStartEndEvent.setJdExact`~~ (renamed `_setJdExact`)
- [ ] `rules/rule_datetime.py:79` — `DateAndTimeEventRule.setJdExact`
- [ ] ~~`task.py:161` — `TaskEvent.setJdExact`~~ (renamed `_setJdExact`)
- [ ] ~~`task.py:355` — `AllDayTaskEvent.setJdExact`~~ (renamed `_setJdExact`)

### `getDaysJdList` (4)
- [ ] `occur.py:56` — `OccurSet.getDaysJdList`
- [ ] `occur.py:128` — `JdOccurSet.getDaysJdList`
- [ ] `occur.py:212` — `IntervalOccurSet.getDaysJdList`
- [ ] `occur.py:322` — `TimeListOccurSet.getDaysJdList`

### `getRulesHash` (4)
- [ ] `large_scale.py:106` — `LargeScaleEvent.getRulesHash`
- [ ] `rule_container.py:109` — `RuleContainer.getRulesHash`
- [ ] `vcs_base.py:99` — `VcsBaseEventGroup.getRulesHash`
- [ ] `vcs_base.py:181` — `VcsEpochBaseEventGroup.getRulesHash`

### `setDefaults` (15)
- [ ] `event_base.py:266` — `Event.setDefaults`
- [ ] `group.py:382` — `EventGroup.setDefaults`
- [ ] `large_scale.py:126` — `LargeScaleEvent.setDefaults`
- [ ] `large_scale.py:208` — `LargeScaleGroup.setDefaults`
- [ ] `lifetime.py:85` — `LifetimeGroup.setDefaults`
- [ ] `monthly.py:83` — `MonthlyEvent.setDefaults`
- [ ] `note.py:117` — `DailyNoteEvent.setDefaults`
- [ ] `task.py:151` — `TaskEvent.setDefaults`
- [ ] `task.py:360` — `AllDayTaskEvent.setDefaults`
- [ ] `university.py:267` — `UniversityTerm.setDefaults`
- [ ] `university.py:389` — `UniversityClassEvent.setDefaults`
- [ ] `university.py:532` — `UniversityExamEvent.setDefaults`
- [ ] `vcs_base.py:94` — `VcsBaseEventGroup.setDefaults`
- [ ] `weekly.py:84` — `WeeklyEvent.setDefaults`
- [ ] `yearly.py:142` — `YearlyEvent.setDefaults`

### `iterFiles` (4)
- [ ] `accounts.py:120` — `Account.iterFiles`
- [ ] `event_base.py:115` — `Event.iterFiles`
- [ ] `group.py:201` — `EventGroup.iterFiles`
- [ ] `trash.py:55` — `EventTrash.iterFiles`

### `getMainClass` (3)
- [ ] `accounts_holder.py:64` — `EventAccountsHolder.getMainClass`
- [ ] `groups_holder.py:61` — `EventGroupsHolder.getMainClass`
- [ ] `holders.py:174` — `ObjectsHolderTextModel.getMainClass`

### ~~`addOccur` (2)~~ FIXED — renamed to `_addOccur`

### ~~`getCourseName` (2)~~ FIXED — renamed to `_getCourseName`

### ~~`getCourseNameById` (2)~~ DO NOT RENAME

### `getTimeZoneObj` (2)
- [ ] `event_container.py:191` — `EventContainer.getTimeZoneObj`
- [ ] ~~`rule_container.py:262` — `RuleContainer.getTimeZoneObj`~~

### `getTimeZoneStr` (2)
- [ ] ~~`event_container.py:155` — `EventContainer.getTimeZoneStr`~~
- [ ] `rule_container.py:272` — `RuleContainer.getTimeZoneStr`

### `postAdd` (2)
- [ ] `event_container.py:270` — `EventContainer.postAdd`
- [ ] `group.py:538` — `EventGroup.postAdd`

### `setEndEpochOnly` (2)
- [ ] `task.py:180` — `TaskEvent.setEndEpochOnly`
- [ ] `task.py:378` — `AllDayTaskEvent.setEndEpochOnly`

### `setList` (2)
- [ ] `groups_holder.py:92` — `EventGroupsHolder.setList`
- [ ] `holders.py:178` — `ObjectsHolderTextModel.setList`

### ~~`updateEventDesc` (2)~~ FIXED — renamed to `_updateEventDesc`

### `updateOccurrenceEvent` (2)
- [ ] ~~`event_container.py:357` — `EventContainer.updateOccurrenceEvent`~~
- [ ] `group.py:616` — `EventGroup.updateOccurrenceEvent`


### ~~`jdMatches` (8) [rules/] ~~ DO NOT RENAME

### ~~`getServerString` (16)~~ DO NOT REANME

### ~~`calcOccurrence` (14)~~ DO NOT REANME

### ~~`getV4Dict` (12)~~ DO NOT REANME

### ~~`getTimeRangeList` (4)~~ DO NOT REANME

### ~~`intersection` (4)~~ DO NOT REANME

### ~~`updateOccurrence` (4)~~ DO NOT REANME

### ~~`getEpoch` (3)~~ DO NOT REANME

### ~~`deepConvertTo` (2)~~ DO NOT REANME

### ~~`fromRange` (1) [occur.py] ~~ DO NOT REANME

### ~~`calcEventOccurrence` (1)~~ DO NOT REANME

### ~~`copyFromExact` (1)~~ DO NOT REANME

### ~~`createPatchByHash` (1)~~ DO NOT REANME

### ~~`exportToIcsFp` (1)~~ DO NOT REANME

### ~~`getAddRule` (1)~~ DO NOT REANME

### ~~`getDescription` (1)~~ DO NOT REANME

### ~~`getEpochFromJhms` (1)~~ DO NOT REANME

### ~~`getJhmsFromEpoch` (1)~~ DO NOT REANME

### ~~`getNotifyBeforeSec` (1)~~ DO NOT REANME

### ~~`getRule` (1)~~ DO NOT REANME

### ~~`icsUID` (1)~~ DO NOT REANME

### ~~`removeAll` (1)~~ DO NOT REANME

### ~~`setDictOverride` (1)~~ DO NOT REANME

### ~~`setTitle` (1)~~ DO NOT REANME

### ~~`getTextParts` (1)~~ DO NOT REANME