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
	from scal3.event_lib.pytypes import EventType

__all__ = ["IntervalOccurSet", "JdOccurSet", "OccurSet", "TimeListOccurSet"]


class OccurSet(SObj):
	def __init__(self) -> None:
		self.event: EventType | None = None

	def intersection(self, other: OccurSet) -> OccurSet:
		raise NotImplementedError

	def getDaysJdList(self) -> list[int]:  # noqa: PLR6301
		return []  # make generator FIXME

	def getTimeRangeList(self) -> list[tuple[int, int]]:  # noqa: PLR6301
		return []  # make generator FIXME

	def getStartJd(self) -> int | None:
		raise NotImplementedError

	def getEndJd(self) -> int | None:
		raise NotImplementedError

	# def __iter__(self) -> Iterator:
	# 	return iter(self.getTimeRangeList())


class JdOccurSet(OccurSet):
	name = "jdSet"

	def __init__(self, jdSet: set[int] | None = None) -> None:
		OccurSet.__init__(self)
		if jdSet is None:
			jdSet = set()
		else:
			assert isinstance(jdSet, set)
		self.jdSet = jdSet

	def __repr__(self) -> str:
		return f"JdOccurSet({list(self.jdSet)})"

	def __bool__(self) -> bool:
		return bool(self.jdSet)

	def __len__(self) -> int:
		return len(self.jdSet)

	def getStartJd(self) -> int | None:
		if not self.jdSet:
			return None
		return min(self.jdSet)

	def getEndJd(self) -> int | None:
		if not self.jdSet:
			return None
		return max(self.jdSet) + 1

	def intersection(self, occur: OccurSet) -> OccurSet:
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
		return sorted(self.jdSet)

	def getTimeRangeList(self) -> list[tuple[int, int]]:
		return [
			(
				getEpochFromJd(jd),
				getEpochFromJd(jd + 1),
			)
			for jd in self.jdSet
		]

	def calcJdRanges(self) -> list[tuple[int, int]]:
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
	name = "timeRange"

	def __init__(self, rangeList: list[tuple[int, int]] | None = None) -> None:
		OccurSet.__init__(self)
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
		if not self.rangeList:
			return None
		return getJdFromEpoch(min(r[0] for r in self.rangeList))

	def getEndJd(self) -> int | None:
		if not self.rangeList:
			return None
		return getJdFromEpoch(max(r[1] for r in self.rangeList))

	def intersection(self, occur: OccurSet) -> OccurSet:
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
		return sorted(
			{
				jd
				for startEpoch, endEpoch in self.rangeList
				for jd in getJdListFromEpochRange(startEpoch, endEpoch)
			},
		)

	def getTimeRangeList(self) -> list[tuple[int, int]]:
		return self.rangeList

	@staticmethod
	def newFromStartEnd(startEpoch: int, endEpoch: int) -> OccurSet:
		if startEpoch > endEpoch:
			return IntervalOccurSet([])
		return IntervalOccurSet([(startEpoch, endEpoch)])


class TimeListOccurSet(OccurSet):
	name = "repeativeTime"

	def __init__(
		self,
		*args,  # noqa: ANN002
	) -> None:
		OccurSet.__init__(self)
		if not args:
			self.startEpoch = 0
			self.endEpoch = 0
			self.stepSeconds = -1
			self.epochList = set()
		elif len(args) == 1:
			self.epochList = set(args[0])
		elif len(args) == 3:
			self.setRange(*args)
		else:
			raise ValueError

	def __repr__(self) -> str:
		return r"TimeListOccurSet({self.epochList!r})"

	# def __bool__(self) -> bool:
	# 	return self.startEpoch == self.endEpoch

	def __bool__(self) -> bool:
		return bool(self.epochList)

	def getStartJd(self) -> int | None:
		if not self.epochList:
			return None
		return getJdFromEpoch(min(self.epochList))

	def getEndJd(self) -> int | None:
		if not self.epochList:
			return None
		return getJdFromEpoch(max(self.epochList) + 1)

	def setRange(self, startEpoch: int, endEpoch: int, stepSeconds: int) -> None:
		try:
			from numpy.core.multiarray import arange
		except ImportError:
			from scal3.utils import arange  # type: ignore[no-redef]
		# ------
		self.startEpoch = startEpoch
		self.endEpoch = endEpoch
		self.stepSeconds = stepSeconds
		self.epochList = set(arange(startEpoch, endEpoch, stepSeconds))

	def intersection(self, occur: OccurSet) -> OccurSet:
		if isinstance(occur, JdOccurSet | IntervalOccurSet):
			epochBetween = []
			for epoch in self.epochList:
				for startEpoch, endEpoch in occur.getTimeRangeList():
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
		return sorted({getJdFromEpoch(epoch) for epoch in self.epochList})

	def getTimeRangeList(self) -> list[tuple[int, int]]:
		return [(epoch, epoch) for epoch in self.epochList]  # or end=None, FIXME
