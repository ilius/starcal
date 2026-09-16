# CLAUDE.md

## Project

StarCal — a multi-calendar desktop application (Python/GTK).

## Code style and type checking

Before committing or finishing any change:

- Run `ruff format`
- Run `ruff check` and use `ruff check --fix` for auto-fixes
- Run `mypy . --strict --disallow-any-generics` and fix all errors

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