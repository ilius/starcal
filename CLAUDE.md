# CLAUDE.md

## Project

StarCal — a multi-calendar desktop application (Python/GTK).

## Code style and type checking

Before committing or finishing any change:

- Run `ruff format`
- Run `ruff check` and use `ruff check --fix` for auto-fixes
- Run `mypy . --strict --disallow-any-generics` and fix all errors

## Refactoring

- Avoid multiple inheritance: do not add new parent classes to existing classes, and do not create new classes with many parents. Prefer composition (helper objects holding a reference to the parent, e.g. `MainWin.menu`, `MainWin.statusIcon`) or standalone functions instead.
- In composition helpers, avoid directly accessing or setting attributes on the parent reference (e.g. `self.mainWin.win`, `self.mainWin.sicon`); keep the parent's state and fields private and access them through the parent's methods instead. Add new methods to the parent if needed.
- In package `__init__.py` files, do not re-export symbols that are not imported from anywhere outside the package; import them directly from their submodule instead.

## Module interface (`__all__`)

`__all__` is a static contract that lists a module's externally-used (public) symbols. It has no runtime effect in this codebase because `import *` is never used; it exists to keep each module's public surface well-defined so internal symbols can be privatized.

- Keep `__all__` accurate: it must contain exactly the symbols that are actually imported or attribute-accessed from outside the module.
- Run the analyzer before committing: `python3 ~/import-analyzer/import-analyzer.py .` from the repo root (it locates the root by finding `pyproject.toml`).
- How it works: it scans the tree, records every `from module import name` and `module.attr` usage, then compares the externally-used names of each imported module against its `__all__`. Configuration lives in `pyproject.toml` under `[tool.import-analyzer]`:
  - `exclude`: path prefixes (regex, anchored at the start) to skip during the scan.
  - `exclude_toplevel_module`: top-level module names to treat as external and never resolve or check.

Interpreting its output:

- `unused symbol X in __all__` — X is listed in `__all__` but never used from outside; remove X from `__all__` to privatize it. If X was imported only to re-export it, remove that import too; if the import exists only for a side effect (e.g. `@registerPlugin` on import), keep it with `# noqa: F401`.
- `ADD to __all__: [...]` — the listed symbols are used from outside the module but missing from `__all__`; add them.
- `Unknown module X: ...` — X is an internal module the analyzer cannot resolve (e.g. imported via `sys.path` insertion, like `xfce_panel`); add X to `exclude_toplevel_module`. Do not "fix" this by changing the import.
- In package `__init__.py` files, do not list submodule names in `__all__` (the analyzer never suggests them for `from pkg import sub` where `sub.py`/`sub/` exists); list only symbols meant for external import.

## UI strings and translations

When adding or modifying UI strings:

- Update `locale.d/*.po` with the new `msgid`/`msgstr`
- Run `./locale.d/compile`

## Git

- When asked to commit a specific fix or change, only commit files related to that fix; do not bundle unrelated changes

## Testing

- Automated tests must never read from or write to the real user configuration directory (`confDir`; `~/.starcal3` on Linux)
- When testing `scal3/event_lib/`, use an isolated temporary `FileSystem` for every object that may load or save persistent data. In tests under `scal3/event_lib/`, request the `fs: FileSystem` pytest fixture and pass or assign it to every event, group, account, or related object that may persist data, directly or indirectly
- Do NOT call `scal3.event_lib.init()` in automated tests: it accesses `confDir/event/lock.json` even when passed the test filesystem. The `fs` fixture initializes event-library state; initialize a `Handler` with `handler.init(fs)` when a loaded handler is needed

## Audit / issue tracking

- Do NOT auto-remove or renumber audit issues when fixing them; only remove or reorder them when explicitly asked
- When fixing an issue, strike through its heading (`#### ~~N. Title~~ FIXED`) and replace the description with a brief fix summary
- Do NOT add changelog / "fixed since last audit" style sections (e.g. "Fixed Issues" or "Fixed Since Last Audit") to `audit.md`; resolved issues are tracked in place by striking through their headings, keeping the audit to issues + recommendations only
- Do NOT add "quality metrics" tables (type hints / error handling / testing / performance ratings) to the audit; keep it factual — issues + recommendations only
- Do NOT add "Architecture Overview" or "File-by-File Summary" sections to the audit; they live in `README.md`
- When editing an audit, tag each open issue with `Priority: N/5` and `Complexity: N/5` (Complexity = effort of the solution, 1 = trivial, 5 = large) and keep the issues list sorted by `Priority − Complexity` descending
- Do NOT re-add priority sections (P1/P2/P3) or a "Resolved" section; resolved issues stay in place with struck-through headings until explicitly asked to remove them