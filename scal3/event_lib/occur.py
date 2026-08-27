#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.

from __future__ import annotations

from scal3 import logger

log = logger.get()


from typing import TYPE_CHECKING

from scal3.interval_utils import intersectionOfTwoIntervalList

# from scal3.interval_utils import
from scal3.s_object import SObj
from scal3.time_utils import (
	getEpochFromJd,
	getJdFromEpoch,
	getJdListFromEpochRange,
)

if TYPE_CHECKING:
	from collections.abc import Iterable

	from scal3.event_lib.pytypes import OccurSetType

	from .pytypes import EventType

__all__ = ["IntervalOccurSet", "JdOccurSet", "TimeListOccurSet"]


class OccurSet(SObj):
	"""Base class representing the set of times an event occurs."""

	def __init__(self) -> None:
		self.event: EventType | None = None

	def intersection(self, other: OccurSetType) -> OccurSetType:
		"""Return a new set containing only times present in both sets."""
		raise NotImplementedError

	def getDaysJdList(self) -> list[int]:  # noqa: PLR6301
		"""Return the list of Julian days covered by this occurrence set."""
		return []  # make generator FIXME

	def getTimeRangeList(self) -> list[tuple[int, int]]:  # noqa: PLR6301
		"""Return a list of (startEpoch, endEpoch) time ranges."""
		return []  # make generator FIXME

	def getStartJd(self) -> int | None:
		"""Return the first Julian day of this set, or None if empty."""
		raise NotImplementedError

	def getEndJd(self) -> int | None:
		"""Return the last Julian day of this set, or None if empty."""
		raise NotImplementedError

	# def __iter__(self) -> Iterator:
	# 	return iter(self.getTimeRangeList())


class JdOccurSet(OccurSet):
	"""Occurrence set defined by a collection of Julian day numbers."""

	name = "jdSet"

	def __init__(self, jdSet: set[int] | None = None) -> None:
		super().__init__()
		if jdSet is None:
			jdSet = set()
		else:
			assert isinstance(jdSet, set), f"{jdSet=}"
		self.jdSet = jdSet

	def __repr__(self) -> str:
		return f"JdOccurSet({list(self.jdSet)})"

	def __bool__(self) -> bool:
		return bool(self.jdSet)

	def __len__(self) -> int:
		return len(self.jdSet)

	def getStartJd(self) -> int | None:
		"""Return the earliest Julian day, or None if empty."""
		if not self.jdSet:
			return None
		return min(self.jdSet)

	def getEndJd(self) -> int | None:
		"""Return the day after the latest Julian day, or None if empty."""
		if not self.jdSet:
			return None
		return max(self.jdSet) + 1

	def intersection(self, occur: OccurSetType) -> OccurSetType:
		"""Return a new set containing only times present in both sets."""
		if isinstance(occur, JdOccurSet):
			return JdOccurSet(
				self.jdSet.intersection(occur.jdSet),
			)
		if isinstance(occur, IntervalOccurSet):
			return IntervalOccurSet(
				intersectionOfTwoIntervalList(
					self.getTimeRangeList(),
					occur.getTimeRangeList(),
				),
			)
		if isinstance(occur, TimeListOccurSet):
			return occur.intersection(self)

		raise TypeError

	def getDaysJdList(self) -> list[int]:
		"""Return the sorted list of Julian days in this set."""
		return sorted(self.jdSet)

	def getTimeRangeList(self) -> list[tuple[int, int]]:
		"""Return each JD as a full-day (startEpoch, endEpoch) interval."""
		return [
			(
				getEpochFromJd(jd),
				getEpochFromJd(jd + 1),
			)
			for jd in self.jdSet
		]

	def calcJdRanges(self) -> list[tuple[int, int]]:
		"""Collapse individual JDs into contiguous (start, end) ranges."""
		jdList = sorted(self.jdSet)  # jdList is sorted
		if not jdList:
			return []
		startJd = jdList[0]
		endJd = startJd + 1
		jdRanges = []
		for jd in jdList[1:]:
			if jd == endJd:
				endJd += 1
			else:
				jdRanges.append((startJd, endJd))
				startJd = jd
				endJd = startJd + 1
		jdRanges.append((startJd, endJd))
		return jdRanges


class IntervalOccurSet(OccurSet):
	"""Occurrence set defined by a list of (startEpoch, endEpoch) intervals."""

	name = "timeRange"

	def __init__(self, rangeList: list[tuple[int, int]] | None = None) -> None:
		super().__init__()
		if not rangeList:
			rangeList = []
		self.rangeList = rangeList

	def __repr__(self) -> str:
		return f"IntervalOccurSet({self.rangeList!r})"

	def __bool__(self) -> bool:
		return bool(self.rangeList)

	def __len__(self) -> int:
		return len(self.rangeList)

	# def __getitem__(i):
	# 	self.rangeList.__getitem__(i)  # FIXME

	def getStartJd(self) -> int | None:
		"""Return the Julian day of the earliest range start, or None if empty."""
		if not self.rangeList:
			return None
		return getJdFromEpoch(min(r[0] for r in self.rangeList))

	def getEndJd(self) -> int | None:
		"""Return the Julian day of the latest range end, or None if empty."""
		if not self.rangeList:
			return None
		return getJdFromEpoch(max(r[1] for r in self.rangeList))

	def intersection(self, occur: OccurSetType) -> OccurSetType:
		"""Return a new set containing only times present in both sets."""
		if isinstance(occur, JdOccurSet | IntervalOccurSet):
			return IntervalOccurSet(
				intersectionOfTwoIntervalList(
					self.getTimeRangeList(),
					occur.getTimeRangeList(),
				),
			)
		if isinstance(occur, TimeListOccurSet):
			return occur.intersection(self)

		raise TypeError(
			f"bad type {occur.__class__.__name__} ({occur!r})",
		)

	def getDaysJdList(self) -> list[int]:
		"""Return the sorted unique Julian days covered by all intervals."""
		return sorted(
			{
				jd
				for startEpoch, endEpoch in self.rangeList
				for jd in getJdListFromEpochRange(startEpoch, endEpoch)
			},
		)

	def getTimeRangeList(self) -> list[tuple[int, int]]:
		"""Return the list of (startEpoch, endEpoch) intervals."""
		return self.rangeList

	@staticmethod
	def newFromStartEnd(startEpoch: int, endEpoch: int) -> OccurSetType:
		"""Create a single-interval occurrence set from start and end epochs."""
		if startEpoch > endEpoch:
			return IntervalOccurSet([])
		return IntervalOccurSet([(startEpoch, endEpoch)])


class TimeListOccurSet(OccurSet):
	"""Occurrence set defined by individual epoch timestamps."""

	name = "repeativeTime"

	def __init__(
		self,
		epochList: Iterable[int] | None = None,
	) -> None:
		super().__init__()
		self.startEpoch = 0
		self.endEpoch = 0
		self.stepSeconds = -1
		self.epochList: set[int]
		if epochList is None:
			self.epochList = set()
		else:
			self.epochList = set(epochList)

	@classmethod
	def fromRange(
		cls,
		startEpoch: int,
		endEpoch: int,
		stepSeconds: int,
	) -> TimeListOccurSet:
		"""Create a TimeListOccurSet from a fixed-step range."""
		obj = cls()
		obj.setRange(startEpoch, endEpoch, stepSeconds)
		return obj

	def __repr__(self) -> str:
		return f"TimeListOccurSet({self.epochList!r})"

	# def __bool__(self) -> bool:
	# 	return self.startEpoch == self.endEpoch

	def __bool__(self) -> bool:
		return bool(self.epochList)

	def getStartJd(self) -> int | None:
		"""Return the Julian day of the earliest epoch, or None if empty."""
		if not self.epochList:
			return None
		return getJdFromEpoch(min(self.epochList))

	def getEndJd(self) -> int | None:
		"""Return the Julian day after the latest epoch, or None if empty."""
		if not self.epochList:
			return None
		return getJdFromEpoch(max(self.epochList) + 1)

	def setRange(self, startEpoch: int, endEpoch: int, stepSeconds: int) -> None:
		"""Populate the epoch list from a fixed-step range."""
		try:
			from numpy.multiarray import arange
		except ImportError:
			from scal3.utils import arange
		# ------
		self.startEpoch = startEpoch
		self.endEpoch = endEpoch
		self.stepSeconds = stepSeconds
		self.epochList = set(arange(startEpoch, endEpoch, stepSeconds))

	def intersection(self, occur: OccurSetType) -> OccurSetType:
		"""Return a new set containing only times present in both sets."""
		if isinstance(occur, JdOccurSet | IntervalOccurSet):
			otherRanges = sorted(occur.getTimeRangeList())
			if not otherRanges:
				return TimeListOccurSet()
			epochBetween = []
			for epoch in sorted(self.epochList):
				for startEpoch, endEpoch in otherRanges:
					if epoch < startEpoch:
						break
					if startEpoch <= epoch < endEpoch:
						epochBetween.append(epoch)
						break
			return TimeListOccurSet(epochBetween)

		if isinstance(occur, TimeListOccurSet):
			return TimeListOccurSet(
				self.epochList.intersection(occur.epochList),
			)

		raise TypeError

	# FIXME: improve performance
	def getDaysJdList(self) -> list[int]:
		"""Return the sorted unique Julian days of all epochs."""
		return sorted({getJdFromEpoch(epoch) for epoch in self.epochList})

	def getTimeRangeList(self) -> list[tuple[int, int]]:
		"""Return each epoch as a zero-length (epoch, epoch) interval."""
		return [(epoch, epoch) for epoch in self.epochList]  # or end=None, FIXME
