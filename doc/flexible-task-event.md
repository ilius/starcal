# Recurring Flexible Task Event Type

This event type depends on the shared [occurrence-state persistence](occurrence-state-persistence.md)
infrastructure.

## Concept

A recurring all-day task with a target date but no hard time — e.g. "water plants every 3 days" or
"review budget weekly". Each occurrence carries a per-occurrence **Done** flag (and optional
completion date); a pending occurrence can be postponed.

### Shift mode

The current occurrence moves later and all subsequent occurrences shift by the same delay, keeping
the same gap between occurrences going forward.

Examples: cleaning, maintenance, watering plants — tasks where each occurrence should stay roughly
`interval` apart.

### No-shift mode

Only the current occurrence moves; future occurrences keep their original scheduled dates, so the
lateness is absorbed and the schedule returns to the nominal interval.

Examples: taking medicine, feeding animals — tasks where getting back on schedule matters more than
the one missed day.

Both modes need the same per-occurrence **Done** state; they differ only in whether the postponed
date is an isolated override (no-shift) or cascades forward (shift).

## Occurrence state

The event does not store an occurrence index. After shift/no-shift postponements are applied and the
final user-facing occurrence intervals are extracted, their start epochs are checked for membership
in `completedAtByStartEpoch`. Postponing a pending occurrence does not update that map; marking it
done adds the start epoch of its final interval.

## Alternative: ask at postponement time (Google Calendar style)

Instead of a fixed per-event mode, prompt the user when postponing whether to shift only the current
occurrence, "this and following", or all occurrences, mirroring Google Calendar / Outlook.

**Pros**
- No up-front mode choice; the right behavior depends on context (one-off slip vs. permanent
  schedule change), which the user knows better than a setting.
- Matches muscle memory from mainstream calendar apps.
- One event type covers both behaviors.

**Cons**
- Extra dialog on every postpone action.
- "This and following" requires splitting the series or storing a per-occurrence offset — the
  hardest part of the state model.
- Ambiguous semantics (what happens to already-`done` occurrences inside the shifted tail).
- More complex help/settings copy.

## Implementation notes

- Builds on the existing `TaskEvent`/`TaskList` (`task.py`).
- Uses the `Event.completedAtByStartEpoch` field specified in
  [occurrence-state-persistence.md](occurrence-state-persistence.md).
- A "Mark done / Postpone" occurrence UI.
- A rule that recomputes the next due date.

**Class:** `FlexibleTaskEvent`. **Complexity:** High.
