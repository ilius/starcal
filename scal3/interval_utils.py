# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from scal3.utils import s_join

CLOSED_START, OPEN_START, OPEN_END, CLOSED_END = range(4)


def ab_overlaps(a0, b0, a1, b1):
	return (
		b0 - a0
		+ b1 - a1
		- abs(a0 + b0 - a1 - b1) > 0.01
	)


def md_overlaps(m0, d0, m1, d1):
	return d0 + d1 - abs(m0 - m1) > 0.01


def simplifyNumList(nums, minCount=3):
	"""
	nums must be sorted
	minCount >= 2
	"""
	ranges = []
	tmp = []
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


def getIntervalPoints(lst, lst_index=0):
	"""
	lst is a list of (start, end, closedEnd) or (start, end) tuples
		start (int)
		end (int)
		closedEnd (bool)

	returns a list of (pos, ptype, lst_index) tuples
		ptype in (CLOSED_START, OPEN_START, OPEN_END, CLOSED_END)
	"""
	points = []
	for row in lst:
		start = row[0]
		end = row[1]
		try:
			closedEnd = row[2]
		except IndexError:
			closedEnd = (start == end)
		points += [
			(
				start,
				CLOSED_START,
				lst_index,
			),
			(
				end,
				CLOSED_END if closedEnd else OPEN_END,
				lst_index,
			),
		]
	return points


def getIntervalListByPoints(points):
	lst = []
	startedStack = []
	for pos, ptype, _ in points:
		if ptype in (OPEN_END, CLOSED_END):
			if not startedStack:
				raise RuntimeError("pos=%s, start=None" % pos)
			start = startedStack.pop()
			#print("pop %s"%start)
			if not startedStack:
				lst.append((
					start,
					pos,
					ptype == CLOSED_END,
				))
		else:
			#print("push %s"%pos)
			startedStack.append(pos)
	return lst


def normalizeIntervalList(lst):
	num = len(lst)
	points = getIntervalPoints(lst)
	points.sort()
	return getIntervalListByPoints(points)


def humanizeIntervalList(lst):
	"""
	replace Closed End intervals with 2 new intervals
	in math terms: [a, b] ==> [a, b) + [b, b]

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


def intersectionOfTwoIntervalList(*lists):
	listsN = len(lists)
	assert listsN == 2
	points = []
	for lst_index, lst in enumerate(lists):
		lst = normalizeIntervalList(lst)
		points += getIntervalPoints(lst, lst_index)
	points.sort()

	openStartList = [None for i in range(listsN)]
	result = []
	for pos, ptype, lst_index in points:
		if ptype in (OPEN_END, CLOSED_END):
			# end == pos
			if None not in openStartList:
				start = max(openStartList)
				if start > pos:
					raise RuntimeError("start - pos = %s" % (start - pos))
				if pos > start or ptype == CLOSED_END:
					result.append((
						start,
						pos,
						ptype == CLOSED_END,
					))
				#if start == pos:  # FIXME
				#	print("start = pos = %s, ptype=%s"%(start%(24*3600)/3600.0, ptype))
			openStartList[lst_index] = None
		else:  # start
			# start == pos
			if openStartList[lst_index] is None:
				openStartList[lst_index] = pos
			else:
				raise RuntimeError("pos=%s, openStartList[%s]=%s" % (
					pos,
					lst_index,
					openStartList[lst_index],
				))
	result = humanizeIntervalList(result)  # right place? FIXME
	return result
