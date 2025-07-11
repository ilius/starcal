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

__all__ = [
	"CLOSED_END",
	"CLOSED_START",
	"OPEN_END",
	"ab_overlaps",
	"getIntervalListByPoints",
	"humanizeIntervalList",
	"intersectionOfTwoIntervalList",
	"log",
	"simplifyNumList",
]


log = logger.get()


CLOSED_START, OPEN_START, OPEN_END, CLOSED_END = range(4)


def ab_overlaps(a0: float, b0: float, a1: float, b1: float) -> bool:
	return b0 - a0 + b1 - a1 - abs(a0 + b0 - a1 - b1) > 0.01


def simplifyNumList(
	nums: list[int],
	minCount: int = 3,
) -> list[int | tuple[int, int]]:
	"""
	Nums must be sorted
	minCount >= 2.
	"""
	ranges: list[int | tuple[int, int]] = []
	tmp: list[int] = []
	for n in nums:
		if tmp and n - tmp[-1] != 1:
			if len(tmp) > minCount:
				ranges.append((tmp[0], tmp[-1]))
			else:
				ranges += tmp
			tmp = []
		tmp.append(n)
	if tmp:
		if len(tmp) > minCount:
			ranges.append((tmp[0], tmp[-1]))
		else:
			ranges += tmp
	return ranges


def getIntervalPoints2(
	lst: list[tuple[int, int]],
	lst_index: int = 0,
) -> list[tuple[int, int, int]]:
	"""
	Lst is a list of (start, end) tuples.
	returns a list of (pos, ptype, lst_index) tuples.
	ptype is one of (CLOSED_START, OPEN_START, OPEN_END, CLOSED_END).
	"""
	points: list[tuple[int, int, int]] = []
	for row in lst:
		points += [
			(
				row[0],
				CLOSED_START,
				lst_index,
			),
			(
				row[1],
				CLOSED_END if row[0] == row[1] else OPEN_END,
				lst_index,
			),
		]
	return points


def getIntervalPoints3(
	lst: list[tuple[int, int, bool]],
	lst_index: int = 0,
) -> list[tuple[int, int, int]]:
	"""
	Lst is a list of (start, end, closedEnd) tuples.
	returns a list of (pos, ptype, lst_index) tuples
	ptype is one of (CLOSED_START, OPEN_START, OPEN_END, CLOSED_END).
	"""
	points: list[tuple[int, int, int]] = []
	for row in lst:
		points += [
			(
				row[0],
				CLOSED_START,
				lst_index,
			),
			(
				row[1],
				CLOSED_END if row[2] else OPEN_END,
				lst_index,
			),
		]
	return points


def getIntervalListByPoints(
	points: list[tuple[int, int, int]],
) -> list[tuple[int, int, bool]]:
	"""
	points: a list of (pos, ptype, lst_index) tuples
	ptype in (CLOSED_START, OPEN_START, OPEN_END, CLOSED_END).

	return a list of (start, end, closedEnd) tuples
		start (int)
		end (int)
		closedEnd (bool)
	"""
	lst = []
	startedStack: list[int] = []
	for pos, ptype, _ in points:
		if ptype in {OPEN_END, CLOSED_END}:
			if not startedStack:
				raise RuntimeError(f"{pos=}, start=None")
			start = startedStack.pop()
			# log.debug(f"pop {start}")
			if not startedStack:
				lst.append(
					(
						start,
						pos,
						ptype == CLOSED_END,
					),
				)
		else:
			# log.debug(f"push {pos}")
			startedStack.append(pos)
	return lst


def humanizeIntervalList(lst: list[tuple[int, int, bool]]) -> list[tuple[int, int]]:
	"""
	Replace Closed End intervals with 2 new intervals
	in math terms: [a, b] ==> [a, b) + [b, b].

	lst is a list of (start, end, closedEnd) tuples
		start (int)
		end (int)
		closedEnd (bool)

	returns a list of (start, end) tuples
	"""
	newList = []
	for start, end, closedEnd in lst:
		newList.append((start, end))
		if closedEnd and end > start:
			newList.append((end, end))
	return newList


def intersectionOfTwoIntervalList(
	*lists: list[tuple[int, int]],
) -> list[tuple[int, int]]:
	listsN = len(lists)
	assert listsN == 2
	points = []
	for lst_index, lst in enumerate(lists):
		points += getIntervalPoints3(
			getIntervalListByPoints(sorted(getIntervalPoints2(lst))),
			lst_index,
		)
	points.sort()

	openStartList: list[int | None] = [None for i in range(listsN)]
	result = []
	for pos, ptype, lst_index in points:
		if ptype in {OPEN_END, CLOSED_END}:
			# end == pos
			if None not in openStartList:
				start: int = max(openStartList)  # type: ignore[type-var, assignment]
				if start > pos:
					raise RuntimeError(f"{start - pos = }")
				if pos > start or ptype == CLOSED_END:
					result.append(
						(
							start,
							pos,
							ptype == CLOSED_END,
						),
					)
				# if start == pos:  # FIXME
				# 	log.info(f"start: pos={start%(24*3600)/3600.0}, {ptype=}")
			openStartList[lst_index] = None
		# it's start, and start == pos
		elif openStartList[lst_index] is None:
			openStartList[lst_index] = pos
		else:
			raise RuntimeError(
				f"{pos=}, {openStartList[lst_index]=}",
			)
	return humanizeIntervalList(result)  # right place? FIXME
