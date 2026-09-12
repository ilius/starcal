# Occurrence-State Persistence

Recurring rules describe when an event is scheduled. They do not currently provide a place to
store facts about an individual occurrence, such as whether it was completed or postponed. This
document defines the shared `Event` field and serialization contract for event types that need
per-occurrence state.

## Occurrence key

Done state is stored in `completedAtByStartJd`, a single map keyed by the start of the final
user-facing occurrence interval: Julian day → { seconds since midnight → completion epoch }.

The key is the final effective start, not an occurrence index. No index is stored: changing the
event's start date must not make an old index point at a different occurrence. If a schedule or
postponement produces different final starts, those final intervals are checked using those new
keys.

For a final occurrence whose start epoch is `startEpoch`, the key is derived in the event's
timezone as:

- `jd = getJdFromEpoch(startEpoch)`;
- `secondsSinceMidnight = startEpoch - getEpochFromJd(jd)` — the time of day within that day.

All-day occurrences start at midnight, so their `secondsSinceMidnight` is `0`. Because rules are
expressed as (date, time-of-day) pairs (`getEpochFromJhms(jd, h, m, s) =
getEpochFromJd(jd) + h*3600 + m*60 + s`, time_utils.py:241), this key equals the rule's stored
date and time and is independent of the timezone.

The presence of a key means the occurrence is done; its value is the integer completion epoch. A
postponed occurrence is still pending, so postponement does not add its old or new start to the
map.

Example:

```json
{
  "notifiers": [],
  "completedAtByStartJd": {
    "2460959": {
      "0": 1760140800
    },
    "2460960": {
      "36000": 1760144400
    }
  },
  "history": []
}
```

The occurrence state is applied after recurrence and postponement have produced the final
user-facing occurrence intervals. The start of each final interval is the key used to check and
record Done. A postponed occurrence therefore remains pending until it is completed, at which point
its postponed start is added to the map.

## Event field and serialization

`Event` owns loading, validation, mutation, and saving of this state, just as it does for
`self.notifiers`. It must define:

- a stable location and format in the event JSON, separate from generated occurrence caches;
- `completedAtByStartJd` as a top-level event-JSON field, written after `notifiers` and immediately
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
`completedAtByStartJd` the first time the user edits a completed
task; it already loses `remoteIds` and `lastMergeSha1` today. Implementing the field therefore
requires fixing the save path, not just an isolated occurrence-state write:

- `SObjBinaryModel.save()` must merge the existing basic-file data instead of overwriting it, so a
  completed occurrence survives later edits to the event and existing fields such as `remoteIds`
  and `lastMergeSha1` are preserved;
- event-object writes must go through the same merged path, so occurrence state and ordinary event
  edits can never clobber each other;
- a regression test must cover "mark an occurrence done, then edit the event, then verify the done
  state is still present".

### Timezone changes

Occurrence keys are (Julian day, seconds since midnight), which are timezone-independent: the rule
stores each occurrence as a (date, time-of-day) pair, and the epoch is derived from it via the
timezone's UTC offset (including DST). A timezone change — or a new DST rule — shifts only the
derived epochs, never the keys, so done markers never land on the wrong day or time. No re-keying
is needed.

`changeCalType` is unaffected: it converts rule dates to the new calendar's representation while
preserving the same Julian day, so keys are preserved.

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
`completedAtByStartJd` in the event JSON and preserve the surrounding
`notifiers` and `history` data. Synchronization must compare and merge this field separately from
event revisions.

## Minimum tests

The shared tests should cover round-tripping state, repeated completion and undo, postponement
without changing `completedAtByStartJd`, completion after postponement, schedule changes,
duplicate/equal keys and two occurrences on the same day at different times, a timezone change
keeping done markers on the same day and time, interrupted writes, editing an event after
completion (save-wide preservation), and copying or deleting an event.
