# Occurrence-State Persistence

Recurring rules describe when an event is scheduled. They do not currently provide a place to
store facts about an individual occurrence, such as whether it was completed or postponed. This
document defines that shared infrastructure for event types that need per-occurrence state.

## Occurrence key

Done state is keyed by the start epoch of the final user-facing occurrence interval:

```python
doneEpochs: set[float]
```

The key is the final effective start epoch, not an occurrence index. No index is stored: changing
the event's start date must not make an old index point at a different occurrence. If a schedule or
postponement produces different final start epochs, those final intervals are checked using those
new keys.

The in-memory representation may use a set, while the JSON representation must use a sorted list
of numbers because JSON has no set type. `doneEpochs` is updated only when the user marks a
user-facing occurrence as done. A postponed occurrence is still pending, so postponement does not
add its old or new start epoch to `doneEpochs`.

Example:

```json
{
  "version": 1,
  "doneEpochs": [1760054400.0],
  "completedAtByStartEpoch": {
    "1760054400.0": 1760140800.0
  }
}
```

The occurrence state is applied after recurrence and postponement have produced the final
user-facing occurrence intervals. The start epoch of each final interval is the key used to check
and record Done. A postponed occurrence therefore remains pending until it is completed, at which
point its postponed start epoch is added to `doneEpochs`.

## State store

`OccurrenceStateStore` owns loading, validation, mutation, and saving of this state. It must define:

- a stable location and format, separate from generated occurrence caches;
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
out of the event's content revisions, but they still need their own persistence and synchronization
contract. A sidecar that is merely written beside the event file is insufficient unless backups,
remote sync, conflict resolution, and event deletion all include it.

## Minimum tests

The shared tests should cover round-tripping state, repeated completion and undo, postponement
without changing `doneEpochs`, completion after postponement, schedule changes, duplicate/equal
start epochs, interrupted writes, and copying or deleting an event.
