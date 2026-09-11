# Occurrence-State Persistence

Recurring rules describe when an event is scheduled. They do not currently provide a place to
store facts about an individual occurrence, such as whether it was completed or postponed. This
document defines that shared infrastructure for event types that need per-occurrence state.

## Occurrence key

Done state is keyed by the start epoch of the final user-facing occurrence interval in
`completedAtByStartEpoch`. The key is the final effective start epoch, not an occurrence index. No index is stored: changing
the event's start date must not make an old index point at a different occurrence. If a schedule or
postponement produces different final start epochs, those final intervals are checked using those
new keys.

The presence of a final start epoch in `completedAtByStartEpoch` means the occurrence is done. A
completion value may be `null` when no completion date is recorded. A postponed occurrence is still
pending, so postponement does not add its old or new start epoch to this map.

Example:

```json
{
  "notifiers": [],
  "completedAtByStartEpoch": {
    "1760054400.0": 1760140800.0
  },
  "history": []
}
```

The occurrence state is applied after recurrence and postponement have produced the final
user-facing occurrence intervals. The start epoch of each final interval is the key used to check
and record Done. A postponed occurrence therefore remains pending until it is completed, at which
point its postponed start epoch is added to `completedAtByStartEpoch`.

## State store

`OccurrenceStateStore` owns loading, validation, mutation, and saving of this state. It must define:

- a stable location and format in the event JSON, separate from generated occurrence caches;
- `completedAtByStartEpoch` as a top-level event-JSON field, written after `notifiers` and immediately
  before `history`;
- direct JSON read/write that bypasses event objects and does not add a revision-history entry;
- atomic writes and recovery from an interrupted write;
- behavior when an event is copied, moved, deleted, restored, imported, or converted;
- backup/export/import behavior;
- modification/version metadata for synchronization and conflict handling;
- migration when the state format changes.

The state should not be confused with the recurrence rule. Updating the rule changes future
generated start epochs; it does not silently reinterpret an old start epoch as another occurrence.

## Event types requiring this infrastructure

- `FlexibleTaskEvent`: recurring all-day tasks with per-occurrence completion and postponement;
  see [flexible-task-event.md](flexible-task-event.md).
- `HabitEvent` and `MedicationReminderEvent`: recurring reminders with per-occurrence completion.
- `StudyPlanGroup` and `StudyMilestoneEvent`: generated milestones when progress tracking is
  enabled.

These types should share the state-store contract rather than each inventing a separate completion
format.

## Revision history and synchronization

Occurrence facts are operational state, not a change to the recurrence definition. They may be kept
out of the event's content revisions. `OccurrenceStateStore` must update only
`completedAtByStartEpoch` in the event JSON and preserve the surrounding `notifiers` and `history`
data. Because this bypasses event objects and revision history, synchronization must compare and
merge this field separately from event revisions.

## Minimum tests

The shared tests should cover round-tripping state, repeated completion and undo, postponement
without changing `completedAtByStartEpoch`, completion after postponement, schedule changes,
duplicate/equal start epochs, interrupted writes, and copying or deleting an event.
