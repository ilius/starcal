from __future__ import annotations

from scal3.event_search_tree import EventSearchTree

# Deterministic dataset that exercises the delete path where a node with both
# children is replaced by the minimum node of its right subtree. Before the
# fix, the replacement node kept its stale min_t/max_t (it never called
# updateMinMax), so search() pruned whole subtrees and valid intervals
# became unfindable.
intervals = {
	1: (844.42185152504817, 859.70196238238407),
	2: (420.57158083084499, 426.12045746155781),
	3: (511.27472136860854, 519.67093704889157),
	4: (783.79858903477259, 790.21318719331168),
	5: (476.59695415235581, 488.47290392172891),
	6: (908.11288519533514, 918.45427888377424),
	7: (281.83784439970384, 297.07602638076969),
	8: (618.36899667533157, 623.75387033189918),
	9: (909.74625596824012, 929.41057275097432),
	10: (810.21723599658958, 828.30947203016149),
	11: (310.1475693193326, 324.87928841040514),
	12: (898.83828796799344, 912.67597464034452),
	13: (472.14271545271333, 474.60638901004648),
	14: (434.17183545378367, 446.58413143593782),
	15: (913.01105323789818, 932.35987740942801),
	16: (477.00977655271703, 494.38332014426402),
	17: (260.49231039195939, 276.69035301871332),
	18: (548.69930383558926, 549.47311698878764),
	19: (719.70468640395416, 727.98174547732742),
	20: (824.84497714823306, 838.37396457225418),
}
deleted = [1, 2, 4, 8, 10, 11, 12, 14, 16, 18]


def _searchEid(tree: EventSearchTree, eid: int) -> bool:
	t0, t1 = intervals[eid]
	mid = (t0 + t1) / 2.0
	return any(item.eid == eid for item in tree.search(mid - 0.1, mid + 0.1))


def test_delete_preserves_other_intervals() -> None:
	"""Deleting an event must not make other events unfindable."""
	tree = EventSearchTree()
	for eid, (t0, t1) in intervals.items():
		tree.add(t0, t1, eid)
	for eid in deleted:
		tree.delete(eid)
	for eid in intervals:
		if eid in deleted:
			continue
		assert _searchEid(tree, eid), f"event {eid} became unfindable after delete"


def test_delete_after_interleaved_adds() -> None:
	"""Deletes interleaved with adds keep the tree consistent."""
	tree = EventSearchTree()
	for eid, (t0, t1) in intervals.items():
		tree.add(t0, t1, eid)
	for eid in deleted:
		tree.delete(eid)
	for i, (t0, t1) in enumerate(intervals.values(), start=1000):
		tree.add(t0 + 0.001, t1 + 0.001, i)
		tree.delete(i)
	for eid in intervals:
		if eid in deleted:
			continue
		assert _searchEid(tree, eid), f"event {eid} became unfindable after add/delete"
