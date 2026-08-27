from __future__ import annotations

import unittest
from typing import cast

from scal3.event_lib.occur import (
	IntervalOccurSet,
	JdOccurSet,
	TimeListOccurSet,
)


class TestTimeListOccurSetIntersection(unittest.TestCase):
	"""Tests for TimeListOccurSet.intersection against other occurrence sets."""

	def test_empty_self(self) -> None:
		"""Intersecting an empty TimeListOccurSet yields an empty set."""
		a = TimeListOccurSet()
		a = TimeListOccurSet()
		b = JdOccurSet({1, 2, 3})
		result = cast("TimeListOccurSet", a.intersection(b))
		self.assertIsInstance(result, TimeListOccurSet)
		self.assertEqual(result.epochList, set())

	def test_empty_other(self) -> None:
		"""Intersecting with an empty JdOccurSet yields an empty set."""
		a = TimeListOccurSet({100, 200, 300})
		b = JdOccurSet()
		result = cast("TimeListOccurSet", a.intersection(b))
		self.assertIsInstance(result, TimeListOccurSet)
		self.assertEqual(result.epochList, set())

	def test_no_overlap_jd(self) -> None:
		"""Intersecting with a JdOccurSet covering no epochs is empty."""
		a = TimeListOccurSet({100, 200, 300})
		b = JdOccurSet({1, 2, 3})
		result = cast("TimeListOccurSet", a.intersection(b))
		self.assertEqual(result.epochList, set())

	def test_partial_overlap_jd(self) -> None:
		"""Only epochs inside the selected JD ranges are kept."""
		# JdOccurSet day ranges: jd=1 -> [epoch_1, epoch_1+86400)
		from scal3.time_utils import getEpochFromJd

		jd1, jd2, jd3 = 100, 200, 300
		e1 = getEpochFromJd(jd1)
		e2 = getEpochFromJd(jd2)
		e3 = getEpochFromJd(jd3)
		a = TimeListOccurSet({e1, e2, e3})
		b = JdOccurSet({jd1, jd3})
		result = cast("TimeListOccurSet", a.intersection(b))
		self.assertEqual(result.epochList, {e1, e3})

	def test_all_overlap_jd(self) -> None:
		"""All epochs are kept when every JD is selected."""
		from scal3.time_utils import getEpochFromJd

		jd1, jd2 = 100, 200
		e1 = getEpochFromJd(jd1)
		e2 = getEpochFromJd(jd2)
		a = TimeListOccurSet({e1, e2})
		b = JdOccurSet({jd1, jd2})
		result = cast("TimeListOccurSet", a.intersection(b))
		self.assertEqual(result.epochList, {e1, e2})

	def test_boundary_exclusive_jd(self) -> None:
		"""An epoch exactly at the end of a JD range is excluded."""
		# Epoch exactly at end of a JD range should NOT be included
		from scal3.time_utils import getEpochFromJd

		jd1 = 100
		e1 = getEpochFromJd(jd1)
		e_end = getEpochFromJd(jd1 + 1)  # first epoch of next day
		a = TimeListOccurSet({e1, e_end})
		b = JdOccurSet({jd1})
		result = cast("TimeListOccurSet", a.intersection(b))
		self.assertEqual(result.epochList, {e1})
		self.assertNotIn(e_end, result.epochList)

	def test_no_overlap_interval(self) -> None:
		"""Intersecting with a disjoint interval yields an empty set."""
		a = TimeListOccurSet({100, 200, 300})
		b = IntervalOccurSet([(0, 50)])
		result = cast("TimeListOccurSet", a.intersection(b))
		self.assertEqual(result.epochList, set())

	def test_partial_overlap_interval(self) -> None:
		"""Only epochs inside the interval are kept."""
		a = TimeListOccurSet({10, 20, 30, 40, 50})
		b = IntervalOccurSet([(15, 35)])
		result = cast("TimeListOccurSet", a.intersection(b))
		self.assertEqual(result.epochList, {20, 30})

	def test_full_overlap_interval(self) -> None:
		"""All epochs are kept when the interval covers everything."""
		a = TimeListOccurSet({10, 20, 30})
		b = IntervalOccurSet([(0, 100)])
		result = cast("TimeListOccurSet", a.intersection(b))
		self.assertEqual(result.epochList, {10, 20, 30})

	def test_multiple_intervals(self) -> None:
		"""Epochs are kept if they fall in any of several intervals."""
		a = TimeListOccurSet({10, 20, 30, 40, 50, 60, 70, 80})
		b = IntervalOccurSet([(5, 25), (55, 75)])
		result = cast("TimeListOccurSet", a.intersection(b))
		self.assertEqual(result.epochList, {10, 20, 60, 70})

	def test_boundary_interval(self) -> None:
		"""Interval starts are inclusive but ends are exclusive."""
		# Epoch at start (inclusive) vs end (exclusive)
		a = TimeListOccurSet({10, 20, 30})
		b = IntervalOccurSet([(10, 20)])
		result = cast("TimeListOccurSet", a.intersection(b))
		self.assertEqual(result.epochList, {10})
		self.assertNotIn(20, result.epochList)

	def test_empty_interval(self) -> None:
		"""Intersecting with an empty interval yields an empty set."""
		a = TimeListOccurSet({10, 20})
		b = IntervalOccurSet([])
		result = cast("TimeListOccurSet", a.intersection(b))
		self.assertEqual(result.epochList, set())

	def test_time_list_intersection(self) -> None:
		"""Intersecting two TimeListOccurSets keeps common epochs."""
		a = TimeListOccurSet({10, 20, 30, 40})
		b = TimeListOccurSet({20, 40, 60})
		result = cast("TimeListOccurSet", a.intersection(b))
		self.assertIsInstance(result, TimeListOccurSet)
		self.assertEqual(result.epochList, {20, 40})

	def test_unsorted_epochs(self) -> None:
		"""Unsorted input epochs do not break the intersection."""
		# Ensure unsorted input doesn't break the algorithm
		a = TimeListOccurSet({500, 100, 300, 200, 400})
		b = IntervalOccurSet([(150, 350)])
		result = cast("TimeListOccurSet", a.intersection(b))
		self.assertEqual(result.epochList, {200, 300})

	def test_large_epoch_list(self) -> None:
		"""Large epoch and interval lists still produce correct results."""
		# Performance sanity check: 10k epochs, 100 intervals
		epochs = set(range(0, 1_000_000, 100))
		a = TimeListOccurSet(epochs)
		intervals = [(i * 1000, i * 1000 + 500) for i in range(1000)]
		b = IntervalOccurSet(intervals)
		result = cast("TimeListOccurSet", a.intersection(b))
		# Each interval [i*1000, i*1000+500) contains epochs i*1000, i*1000+100,
		# i*1000+200, i*1000+300, i*1000+400
		expected = set()
		for i in range(1000):
			for j in range(5):
				epoch = i * 1000 + j * 100
				if epoch in epochs:
					expected.add(epoch)
		self.assertEqual(result.epochList, expected)


if __name__ == "__main__":
	unittest.main()
