# Event Occurrence Search Tree — Design Notes

Technical background for `scal3/event_search_tree.py`, which indexes event
occurrences in time so the calendar views can answer "what happens on day X"
quickly.

## Use cases / required operations

- **Range query**: return every occurrence overlapping `[t0, t1)` (e.g. a day,
  a week, a month). This is the hot path — every cell redraw queries the tree
  via `getDayOccurrenceData`.
- **Batch delete by event**: `delete(eid)` removes *all* occurrences of one
  event (moving an event to Trash, or editing it, drops its old occurrences).
- **Per-event min/max**: `getFirstOfEvent(eid)` / `getLastOfEvent(eid)` — used
  for event sorting and for notification scheduling (`checkNotify`).
- **Last-before query**: `getLastBefore(t1)` — used by the timeline.
- The index holds **multi-occurrence events** (a weekly event over the group's
  ~15-year range produces hundreds of entries), and many events can share the
  same start time.

## Current structure

An interval-tree variant:

- A red-black-style BST keyed by interval **midpoint** `mt = (t0 + t1) / 2`.
- Each node keeps a max-heap of `(dt, eid)` where `dt = (t1 - t0) / 2`, so
  events sharing the same midpoint share one node.
- Each node also stores subtree bounds `min_t` / `max_t` so the search can
  prune whole subtrees.
- A separate index `byId: eid -> MaxHeap[(mt, dt)]` enables the per-event batch
  operations.

This is a legitimate interval tree, but keying by *midpoint* (rather than by
start) is non-standard and was the source of the bugs below.

### Bugs found and fixed

1. **Stale `min_t` / `max_t` on delete.** `_deleteStep` never recomputed the
   subtree bounds. When the last occurrence was removed from a node that had
   both children, the replacement node kept its old bounds, which no longer
   covered the subtree it inherited — so `search()` pruned whole subtrees and
   valid events became unfindable (e.g. moving one event to Trash made another
   disappear). Fix: call `updateMinMax()` on the way back up in
   `_deleteStep`, mirroring the add path.

2. **Degenerate nodes for zero-duration intervals.** A zero-duration
   occurrence (`t0 == t1`, e.g. a task whose duration is 0) produces a node
   with `min_t == max_t`. The search clamps the query range to that point and
   hits `t0 >= t1`, pruning the node, so the event is never returned — it is
   hidden in the main window from the moment it is created (including right
   after startup). Fix: widen such intervals by a tiny epsilon
   (`epsTm = 0.01 s`) on insert, so their nodes are never degenerate. The
   epsilon is kept sub-second so the display still renders the event as a
   point (just the start time).

## Is there a better data structure?

The current structure is already an interval tree, so a different *kind* of
structure is not needed. The two bugs were implementation defects in the
midpoint-keyed design, not a flaw in the interval-tree concept. But there is a
cleaner *canonical* formulation:

### Standard interval tree (keyed by start, max-end augmented)

- Node key = occurrence **start** time; the node holds a small list of
  `(end, eid)` for all occurrences starting at that time; each subtree stores
  the maximum `end` below it.
- Overlap query `[t0, t1)`: recurse left iff `left.maxEnd > t0`, test the
  node's intervals directly (`s < t1 and e > t0`), recurse right iff
  `node.s < t1`.
- Advantages over the current design:
  - **No degenerate nodes.** Two occurrences starting at the same time simply
    share a node's list, so the whole zero-duration bug class disappears
    without an epsilon hack.
  - **Half-open boundary handled with real endpoints.** Since every interval's
    actual `(s, e)` is available, `s == e` (a point) is checked explicitly.
    The current midpoint heuristic is symmetric and cannot tell "point at
    range start" (must match) from "point at range end" (must not), which is
    exactly why the naive search-side fix causes midnight events to appear on
    two days.
  - **Textbook delete.** Simple single-node removal; no `min_t`/`max_t`
    bookkeeping to go stale.
- The `byId: eid -> occurrences` index is still kept for the per-event batch
  operations (`delete(eid)`, `getFirstOfEvent`, `getLastOfEvent`).

### Per-day buckets (alternative)

Index each occurrence under every day it spans; a day query becomes O(1).
This is arguably the most natural fit for a calendar (an event spanning two
days is intentionally shown on both). Costs:

- Linear memory in the day-span of each occurrence — a 15-year lifetime event
  touches ~5500 day buckets.
- Event updates become O(occurrences × days).

Not worth it at the current scale.

### Recommendation

Keep the current tree. It is the right class of structure, both bugs are
fixed, and its asymptotics are already optimal: O(log n) insert/delete/search
and O(k) to report k occurrences. A rewrite to the start-keyed interval tree
would be cleaner to maintain and eliminate the degenerate-node class by
construction, but it is a significant change with real regression risk for
marginal practical gain at the app's scale (thousands of events, tens of
thousands of occurrences). Consider the rewrite only if the current
implementation continues to produce correctness bugs.