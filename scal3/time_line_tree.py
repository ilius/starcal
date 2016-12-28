# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/lgpl.txt>.
# Also avalable in /usr/share/common-licenses/LGPL on Debian systems
# or /usr/share/licenses/common/LGPL/license.txt on ArchLinux

import sys
from math import log

from scal3.interval_utils import ab_overlaps
from scal3.time_utils import *

#maxLevel = 1
#minLevel = 1


class Node:
	def __init__(self, base, level, offset, rightOri):
		#global maxLevel, minLevel
		self.base = base ## 8 or 16 is better
		self.level = level
		# base ** level is the mathematical scope of the node
		# (with its children)
		#if level > maxLevel:
		#	maxLevel = level
		#	print('maxLevel =', level)
		#if level < minLevel:
		#	minLevel = level
		#	print('minLevel =', level)
		self.offset = offset ## in days
		self.rightOri = rightOri ## FIXME
		###
		width = base ** level
		if rightOri:
			self.s0, self.s1 = offset, offset + width
		else:
			self.s0, self.s1 = offset - width, offset
		###
		self.clear()

	def clear(self):
		self.children = {}
		# possible keys of `self.children` are 0 to `base-1` for right node,
		# and `-(base-1)` to 0 for left node
		self.events = [] ## list of tuples (rel_start, rel_end, event_id)

	def sOverlaps(self, t0, t1):
		return ab_overlaps(t0, t1, self.s0, self.s1)

	def search(self, t0, t1):  # t0 < t1
		"""
		returns a generator to iterate over (ev_t0, ev_t1, eid, ev_dt) s
		"""
		# t0 and t1 are absolute. not relative to the self.offset
		if not self.sOverlaps(t0, t1):
			raise StopIteration
		for ev_rt0, ev_rt1, eid in self.events:
			ev_t0 = ev_rt0 + self.offset
			ev_t1 = ev_rt1 + self.offset
			if ab_overlaps(t0, t1, ev_t0, ev_t1):
				yield (
					max(t0, ev_t0),
					min(t1, ev_t1),
					eid,
					ev_rt1 - ev_rt0,
				)
		for child in self.children.values():
			for item in child.search(t0, t1):
				yield item

	def getChild(self, tm):
		if not self.s0 <= tm <= self.s1:
			raise RuntimeError(
				'Node.getChild: Out of scope' +
				'level=%s, offset=%s, rightOri=%s' % (
					self.level,
					self.offset,
					self.rightOri,
				)
			)
		dt = self.base ** (self.level - 1)
		index = int((tm - self.offset) // dt)
		try:
			return self.children[index]
		except KeyError:
			child = self.children[index] = self.__class__(
				self.base,
				self.level - 1,
				self.offset + index * dt,
				self.rightOri,
			)
			return child

	def newParent(self):
		parent = self.__class__(
			self.base,
			self.level + 1,
			self.offset,
			self.rightOri,
		)
		parent.children[0] = self
		return parent

	def getDepth(self):
		if not self.children:
			return 0
		return 1 + max(
			c.getDepth()
			for c in self.children.values()
		)


class TimeLineTree:
	def __init__(self, offset=0, base=4):
		# base 4 and 8 are the best (about speed of both add and search)
		self.base = base
		self.offset = offset
		self.clear()

	def clear(self):
		self.right = Node(self.base, 1, self.offset, True)
		self.left = Node(self.base, 1, self.offset, False)
		self.byEvent = {}

	def search(self, t0, t1):
		if self.offset < t1:
			for item in self.right.search(t0, t1):
				yield item
		if t0 < self.offset:
			for item in self.left.search(t0, t1):
				yield item

	def add(self, t0, t1, eid, debug=False):
		if debug:
			from time import strftime, localtime
			f = '%F, %T'
			print('%s.add: %s\t%s' % (
				self.__class__.__name__,
				strftime(f, localtime(t0)),
				strftime(f, localtime(t1)),
			))
		if self.offset <= t0:
			isRight = True
			node = self.right
		elif t0 < self.offset < t1:
			self.add(t0, self.offset, eid)
			self.add(self.offset, t1, eid)
			return
		elif t1 <= self.offset:
			isRight = False
			node = self.left
		else:
			raise RuntimeError
		########
		while True:
			if node.s0 <= t0 < node.s1 and node.s0 < t1 <= node.s1:
				break
			node = node.newParent()
		# now `node` is the new side (left/right) node
		if isRight:
			self.right = node
		else:
			self.left = node
		while True:
			child = node.getChild(t0)
			if child.s0 <= t1 <= child.s1:
				node = child
			else:
				break
		# now `node` is the node that event should be placed in
		ev_tuple = (
			t0 - node.offset,
			t1 - node.offset,
			eid,
		)
		node.events.append(ev_tuple)
		try:
			self.byEvent[eid].append((node, ev_tuple))
		except KeyError:
			self.byEvent[eid] = [(node, ev_tuple)]

	def delete(self, eid):
		try:
			refList = self.byEvent.pop(eid)
		except KeyError:
			return 0
		n = len(refList)
		for node, ev_tuple in refList:
			try:
				node.events.remove(ev_tuple)
			except ValueError:
				continue
			#if not node.events:
			#	node.parent.removeChild(node)
		return n

	def getLastOfEvent(self, eid):
		try:
			node, ev_tuple = self.byEvent[eid][-1]
			# self.byEvent is sorted by time? FIXME
		except KeyError as IndexError:
			return None
		return ev_tuple[0], ev_tuple[1]

	def getFirstOfEvent(self, eid):
		try:
			node, ev_tuple = self.byEvent[eid][0]
		except KeyError as IndexError:
			return None
		return ev_tuple[0], ev_tuple[1]

	def getDepth(self):
		return 1 + max(
			self.left.getDepth(),
			self.right.getDepth(),
		)

#if __name__=='__main__':
#	from scal3 import ui
#	from time import time as now
#	ui.eventGroups = event_lib.EventGroupsHolder.load()
#	for group in ui.eventGroups:
#		t0 = now()
#		group.updateOccurrenceNode()
#		print(now()-t0, group.title)
