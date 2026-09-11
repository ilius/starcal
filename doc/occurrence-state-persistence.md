# Occurrence-State Persistence

Recurring rules describe when an event is scheduled. They do not currently provide a place to
store facts about an individual occurrence, such as whether it was completed or postponed. This
document defines the shared `Event` field and serialization contract for event types that need
per-occurrence state.

## Occurrence key

Done state is keyed by the start epoch of the final user-facing occurrence interval in
`completedAtByStartEpoch`. The key is the final effective start epoch, not an occurrence index. No index is stored: changing
the event's start date must not make an old index point at a different occurrence. If a schedule or
postponement produces different final start epochs, those final intervals are checked using those
new keys.

The presence of a final start epoch in `completedAtByStartEpoch` means the occurrence is done. Its
value is the integer completion epoch. A postponed occurrence is still pending, so postponement
does not add its old or new start epoch to this map.

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

## Event field and serialization

`Event` owns loading, validation, mutation, and saving of this state, just as it does for
`self.notifiers`. It must define:

- a stable location and format in the event JSON, separate from generated occurrence caches;
- `completedAtByStartEpoch` as a top-level event-JSON field, written after `notifiers` and immediately
  before `history`;
- event-object loading and saving for the field, without a separate state-store class;
- atomic writes and recovery from an interrupted write;
- save-wide preservation: a normal event save must not drop the field (see below);
- behavior when an event is copied, moved, deleted, restored, imported, or converted;
- backup/export/import behavior;
- modification/version metadata for synchronization and conflict handling;
- migration when the state format changes.

The state should not be confused with the recurrence rule. Updating the rule changes future
generated start epochs; it does not silently reinterpret an old start epoch as another occurrence.

### Save-wide preservation

The event basic file is not append-only. `SObjBinaryModel.save()` rebuilds the basic data from
`getDict()` plus `basicOptions` and writes only those keys alongside `history`, so any other key
already present in the file is silently dropped on the next ordinary event save. This would wipe
`completedAtByStartEpoch` the first time the user edits a completed task; it already loses
`remoteIds` and `lastMergeSha1` today. Implementing the field therefore requires fixing the
save path, not just an isolated occurrence-state write:

- `SObjBinaryModel.save()` must merge the existing basic-file data instead of overwriting it, so a
  completed occurrence survives later edits to the event and existing fields such as `remoteIds`
  and `lastMergeSha1` are preserved;
- event-object writes must go through the same merged path, so occurrence state and ordinary event
  edits can never clobber each other;
- a regression test must cover "mark an occurrence done, then edit the event, then verify the done
  state is still present".

## Event types requiring this infrastructure

- `FlexibleTaskEvent`: recurring all-day tasks with per-occurrence completion and postponement;
  see [flexible-task-event.md](flexible-task-event.md).
- `HabitEvent` and `MedicationReminderEvent`: recurring reminders with per-occurrence completion.
- `StudyPlanGroup` and `StudyMilestoneEvent`: generated milestones when progress tracking is
  enabled.

These types should share the `Event` field contract rather than each inventing a separate completion
format.

## Revision history and synchronization

Occurrence facts are operational state, not a change to the recurrence definition. They may be kept
out of the event's content revisions. `Event` must update only
`completedAtByStartEpoch` in the event JSON and preserve the surrounding `notifiers` and `history`
data. Synchronization must compare and merge this field separately from event revisions.

## Minimum tests

The shared tests should cover round-tripping state, repeated completion and undo, postponement
without changing `completedAtByStartEpoch`, completion after postponement, schedule changes,
duplicate/equal start epochs, interrupted writes, editing an event after completion (save-wide
preservation), and copying or deleting an event.
