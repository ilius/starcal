# Breaking Up Python Files Over 800 LOC

## List of files over 800 LOC (11)

| LOC | File | What it holds |
|----:|------|---------------|
| 2956 | `scal3/ui_gtk/event/manager.py` | `EventManagerDialog` — one ~2750-LOC class |
| 1465 | `scal3/ui/conf.py` | flat module: 181 `Option` definitions with docstrings |
| 1226 | `scal3/ui_gtk/starcal_mainwin.py` | `MainWin` class |
| 1090 | `scal3/ui_gtk/day_cal.py` | `DayCal` class |
| 1074 | `scal3/ui_gtk/timeline.py` | `TimeLine` class + small `TimeLineWindow` |
| 940 | `scal3/ui_gtk/timeline_prefs.py` | single `TimeLinePreferencesWindow` |
| 887 | `scal3/ui_gtk/event/search_events.py` | single `EventSearchWindow` |
| 848 | `scal3/ui_gtk/option_ui_extra.py` | 6 independent `OptionUI` classes |
| 848 | `scal3/plugin_man.py` | `BasePlugin` + Holiday/YearlyText/Ics + loader |
| 835 | `scal3/event_lib/group.py` | `EventGroup` |
| 803 | `scal3/ui_gtk/mainwin_items/labelBox.py` | labels + button boxes + `CalObj` |

## Proposed plan (by technique)

### 1. Package conversions — zero consumer breakage

Module → dir + `__init__.py` re-export; all existing imports keep working

- **`plugin_man.py`** → package: `base.py`, `holiday.py`, `yearly_text.py`,
  `ics.py`, `loader.py`.
- **`labelBox.py`** → `labels.py`, `buttons.py`, `calobj.py`.

### 2. Split independent classes into sibling modules

- **`option_ui_extra.py`** → one module per `OptionUI`
  (keep the coupled treeview/toolbar classes together).

### 3. Extract cohesive chunks from single big classes via mixins/helper modules

Most invasive; the class must either inherit mixins or call moved helpers.

- **`manager.py`** (2956) — method clusters:
  - multi-select (664–1126)
  - row/group model helpers (1129–1408)
  - right-click menus (1413–1799)
  - key/treeview event handlers (1804–2011)
  - group ops (2097–2472)
  - event/trash ops (2473–2648)
  - move up/down (2649–2781)
  - group convert/bulk/export (2781–2883)
  - copy/cut/paste (2884–2956)
- **`starcal_mainwin.py`** — extract menu building + status-icon/toolbar clock
  sections.
- **`day_cal.py`** — extract drawing code (drawAll, drawEventIcons,
  drawSeasonPie, drawWithContext, render helpers).
- **`timeline.py`** — move `TimeLineWindow` to its own file; drawing methods →
  `timeline_drawing.py`.
- **`timeline_prefs.py`** — split the ~5 tab-builders (nested funcs, 54–906)
  into per-page modules.
- **`search_events.py`** — split search/export logic vs. context-menu /
  result-UI mixins.
- **`group.py`** — occurrence/cache + search + import/export data into a
  helper module.

## Notes

- Single-class files (`manager`, `timeline_prefs`, `search_events`) are the
  highest-risk; multiple-file mixins change class layout.
- The `conf` data file is mechanical but must preserve exact
  order and values.
- Verification: `ruff check`, `ruff format`, `pytest` (event_lib tests need
  an isolated `FileSystem`), plus a manual GUI smoke test for GTK files.

## Suggested order

1. Low-risk first: `plugin_man.py`, `labelBox.py`,
   `option_ui_extra.py`.
2. Medium: `starcal_mainwin.py`, `day_cal.py`, `timeline.py`, `group.py`,
   `search_events.py`, `timeline_prefs.py`.
3. Last: `manager.py` (the biggest and most invasive).

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