# Breaking Up Python Files Over 800 LOC

## List of files over 800 LOC

| LOC | File | What it holds |
|----:|------|---------------|
| 1465 | `scal3/ui/conf.py` | flat module: 181 `Option` definitions with docstrings |
| 1090 | `scal3/ui_gtk/day_cal.py` | `DayCal` class |
| 1074 | `scal3/ui_gtk/timeline.py` | `TimeLine` class + small `TimeLineWindow` |
| 940 | `scal3/ui_gtk/timeline_prefs.py` | single `TimeLinePreferencesWindow` |
| 887 | `scal3/ui_gtk/event/search_events.py` | single `EventSearchWindow` |
| 848 | `scal3/ui_gtk/option_ui_extra.py` | 7 independent `OptionUI` classes |
| 803 | `scal3/ui_gtk/mainwin_items/labelBox.py` | labels + button boxes + `CalObj` |

## Proposed plan (by technique)

### 1. Package conversions — zero consumer breakage

Module → dir + `__init__.py` re-export; all existing imports keep working

- **`labelBox.py`** → `labels.py`, `buttons.py`, `calobj.py`.

### 2. Split independent classes into sibling modules

- **`option_ui_extra.py`** → one module per `OptionUI`
  (keep the coupled treeview/toolbar classes together).

### 3. Extract cohesive chunks from single big classes via helper modules

Most invasive; the class must delegate to helper objects (composition, holding
a reference to the parent) or standalone functions. Avoid multiple inheritance.

- **`day_cal.py`** — extract drawing code (drawAll, drawEventIcons,
  drawSeasonPie, drawWithContext, render helpers) into a composition helper or
  standalone functions.
- **`timeline.py`** — move `TimeLineWindow` to its own file; drawing methods →
  helper object / functions in `timeline_drawing.py`.
- **`timeline_prefs.py`** — split the ~5 tab-builders (nested funcs, 54–906)
  into per-page modules (standalone functions).
- **`search_events.py`** — split search/export logic vs. context-menu /
  result-UI helper objects.
- **`group.py`** — occurrence/cache + search into a helper module
  (import/export data already moved to `groups_import.py`, `listToDict` to
  `event_lib/utils.py`; now 780 LOC).

## Notes

- Single-class files (`timeline_prefs`, `search_events`) are the
  highest-risk; extracting into helper objects rewires the class.
- Follow the refactoring rules in `CLAUDE.md`: avoid multiple inheritance —
  use composition (helper objects holding a reference to the parent) or
  standalone functions; helpers must access the parent only through its
  methods, adding new parent methods if needed.
- The `conf` data file is mechanical but must preserve exact
  order and values.
- Verification: `ruff check`, `ruff format`, `pytest` (event_lib tests need
  an isolated `FileSystem`), plus a manual GUI smoke test for GTK files.

## Suggested order

1. Low-risk first: `labelBox.py`, `option_ui_extra.py`.
1. Medium: `day_cal.py`, `timeline.py`, `group.py`,
   `search_events.py`, `timeline_prefs.py`.

## Future: conf.py namespace classes

Turn the variable-name prefixes into namespace classes attached to `conf`: the
prefix becomes a class holding the prefix-stripped `Option` attributes, so
`conf.dcalDayParams` becomes `conf.dayCal.dayParams`.

Prefix → class mapping:

- `dcal` → `dayCal` (e.g. `dayCal.dayParams`, `dayCal.winDayParams`)
- `wcal` → `weekCal` (e.g. `weekCal.grid`, `weekCal.items`)
- `mcal` → `monthCal` (e.g. `monthCal.typeParams`, `monthCal.grid`)
- `win` / `mainWin` → `mainWin`
- `statusIcon` → `statusIcon` (own namespace)
- `statusBar` → `statusBar` (own namespace)
- `labelBox` → `labelBox`
- no prefix → `misc`

Each class is defined in its own private module (e.g. `class dayCal` in
`_daycal.py`), imported in `__init__.py`, and listed in its `__all__` so that
`conf.dayCal` resolves to the class. The `confOptions*` dicts and
`needRestartList` stay in `__init__.py`. Because the attribute paths change,
every `conf.<name>` reference across the codebase must be updated to
`conf.<namespace>.<attr>`.
