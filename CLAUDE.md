# CLAUDE.md

## Project

StarCal — a multi-calendar desktop application (Python/GTK).

## Code style

- Run `ruff format` before committing
- Run `ruff check` before committing (use `ruff check --fix` for auto-fixes)

## Git

- When asked to commit a specific fix or change, only commit files related to that fix. Do not bundle unrelated changes.

## Audit / issue tracking

- Do NOT auto-remove or renumber audit issues when fixing them. Only remove/reorder issues when explicitly asked.
- When fixing an issue, strike through its heading (`#### ~~N. Title~~ FIXED`) and replace the description with a brief fix summary.
- Do NOT add changelog / "fixed since last audit" style sections (e.g. a "Fixed Issues" or "Fixed Since Last Audit" section listing resolved items) to `audit.md`. Resolved issues are tracked in place by striking through their headings; keep the audit to issues + recommendations only.
- Do NOT add "quality metrics" tables (type hints / error handling / testing / performance ratings) to the audit. Keep the audit factual: issues + recommendations only.
- Do NOT add "Architecture Overview" or "File-by-File Summary" sections to the audit — they live in `README.md`.
- When editing an audit, keep each open issue tagged with `Priority: N/5` and `Complexity: N/5` (Complexity = effort of the solution, 1 = trivial, 5 = large), and keep the issues list sorted by `Priority − Complexity` descending. Do not re-add priority sections (P1/P2/P3). Do not add a "Resolved" section — when fixing an issue, strike through its heading and replace the description with a brief fix summary, keeping it in place in the list. Only remove issues when explicitly asked.
