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
