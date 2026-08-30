# Config Parameter Changes

Notes on renaming/fixing config parameters whose values are persisted in user
config files (`~/.starcal3` JSON) and compared against literal strings in code.
Such values must NOT be changed with a plain find-and-replace: existing user
configs store the old spelling, so code must keep accepting it (alias /
normalization on read) until the value is migrated.

## `"buttom"` → `"bottom"` (`yalign`)

Misspelled `"buttom"` (should be `"bottom"`) is used as a `yalign` config value.
It is stored in user configs and compared in code.

### Where the value is produced (defaults / UI)

- `scal3/ui/conf.py` — default config dicts, `"yalign": "buttom"`:
  lines 863, 882, 986, 1022, 1038, 1209, 1230, 1238
- `scal3/ui/options.py` — `"yalign": "buttom"`: lines 1262, 1290, 1490, 1529,
  1549, 1886, 1912, 1920
- `scal3/ui_gtk/timeline.py` — `yalign="buttom"`: lines 184, 195, 206, 217,
  229, 249, 261, 272
- `scal3/ui_gtk/year_wheel.py` — lines 124, 134
- `scal3/ui_gtk/mainwin_items/monthCal.py` — lines 426, 429
- `scal3/ui_gtk/cal_type_options.py` — `YAlignComboBox`:
  - line 94: `get()` returns `"buttom"`
  - line 103: `set()` compares against `"buttom"`
- `scal3/ui/pytypes.py:61-111` — `yalign: str` fields in config dict types

### Where the value is read / compared / validated

- `scal3/drawing.py:31-32` — `oppositeAlign()` returns/compares `"buttom"`
- `scal3/drawing.py:54` — `getAbsPos()` compares `yalign == "buttom"`
- `scal3/ui_gtk/button_drawing.py:61` — validation set
  `{"top", "buttom", "center"}` (invalid values raise `ValueError`)
- `scal3/ui_gtk/day_cal.py:736` — `elif yalign == "buttom":`; line 740 logs
  `invalid {yalign=}` otherwise
- `scal3/ui_gtk/day_cal.py:236, 297` — reads `yalign` from config and passes it
  to `getAbsPos()`

### Migration plan

1. Rename the defaults in `conf.py`, `options.py`, `timeline.py`,
   `year_wheel.py`, `monthCal.py`, and `day_cal.py` from `"buttom"` to
   `"bottom"`.
2. Update the comparison/validation points in `drawing.py` (`oppositeAlign`,
   `getAbsPos`), `button_drawing.py:61`, `day_cal.py:736`, and
   `cal_type_options.py` (`YAlignComboBox.get`/`set`).
3. Accept the legacy value on read: wherever a `yalign` string is loaded or
   compared, treat both `"bottom"` and `"buttom"` as bottom (e.g. normalize
   `"buttom"` → `"bottom"` at the config-load boundary, or widen the
   comparison/validation sets to include the legacy spelling).
4. Optionally migrate saved configs (rewrite `"buttom"` → `"bottom"` on save)
   once the code no longer reads the old value.

### Notes

- Tests must not read/write the real `confDir`; verify any migration logic
  against an isolated temporary `FileSystem` (see `CLAUDE.md`).