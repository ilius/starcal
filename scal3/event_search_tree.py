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

from scal3.utils import myRaise
from scal3.time_utils import *
from scal3.bin_heap import MaxHeap


epsTm = 0.01 ## seconds ## configure somewhere? FIXME

getCount = lambda x: x.count if x else 0
isRed = lambda x: x.red if x else False


class Node:
	def __init__(self, mt, red=True):
		self.mt = mt
		self.red = red
		self.min_t = mt
		self.max_t = mt
		self.events = MaxHeap()
		self.left = None
		self.right = None
		self.count = 0
	def add(self, t0, t1, dt, eid):
		self.events.push(dt, eid)
		if t0 < self.min_t:
			self.min_t = t0
		if t1 > self.max_t:
			self.max_t = t1
	def updateMinMax(self):
		self.updateMinMaxChild(self.left)
		self.updateMinMaxChild(self.right)
	def updateMinMaxChild(self, child):
		if child:
			if child.min_t < self.min_t:
				self.min_t = child.min_t
			if child.max_t > self.max_t:
				self.max_t = child.max_t
	#def updateCount(self):
	#	self.count = len(self.events) + getCount(self.left) + getCount(self.right)


def rotateLeft(h):
	#if not isRed(h.right):
	#	raise RuntimeError('rotateLeft: h.right is not red')
	x = h.right
	h.right = x.left
	x.left = h
	x.red = h.red
	h.red = True
	return x

def rotateRight(h):
	#if not isRed(h.left):
	#	raise RuntimeError('rotateRight: h.left is not red')
	x = h.left
	h.left = x.right
	x.right = h
	x.red = h.red
	h.red = True
	return x

def flipColors(h):
	#if isRed(h):
	#	raise RuntimeError('flipColors: h is red')
	#if not isRed(h.left):
	#	raise RuntimeError('flipColors: h.left is not red')
	#if not isRed(h.right):
	#	raise RuntimeError('flipColors: h.right is not red')
	h.red = True
	h.left.red = False
	h.right.red = False

class EventSearchTree:
	def __init__(self):
		self.clear()
	def clear(self):
		self.root = None
		self.byId = {}
	def doCountBalancing(self, node):
		if node.left and not node.left.right and \
			node.left.count - getCount(node.right) > len(node.events):
			#print('moving up from left')
			## `mup` is the node that is moving up and taking place of `node`
			mup, node.left = node.left, None
			#node.red, mup.red = mup.red, node.red
			mup.right, node = node, mup
		if node.right and not node.right.left and \
			node.right.count - getCount(node.left) > len(node.events):
			#print('moving up from right')
			## `mup` is the node that is moving up and taking place of `node`
			mup, node.right = node.right, None
			#node.red, mup.red = mup.red, node.red
			mup.left, node = node, mup
		return node
	def addStep(self, node, t0, t1, mt, dt, eid):
		if t0 > t1:
			return node
		if not node:
			node = Node(mt)
			node.add(t0, t1, dt, eid)
			return node
		if mt < node.mt:
			node.left  = self.addStep(node.left , t0, t1, mt, dt, eid)
		elif mt > node.mt:
			node.right = self.addStep(node.right, t0, t1, mt, dt, eid)
		else:## mt == node.mt
			node.add(t0, t1, dt, eid)
		## node = self.doCountBalancing(node)
		if isRed(node.right) and not isRed(node.left):
			node = rotateLeft(node)
		if isRed(node.left) and isRed(node.left.left):
			node = rotateRight(node)
		if isRed(node.left) and isRed(node.right):
			flipColors(node)
		## node.updateCount()
		node.updateMinMax()
		return node
	def add(self, t0, t1, eid, debug=False):
		if debug:
			from time import strftime, localtime
			f = '%F, %T'
			print('EventSearchTree.add: %s\t%s\t%s'%(
				eid,
				strftime(f, localtime(t0)),
				strftime(f, localtime(t1)),
			))
		###
		if t0 == t1:
			t1 += epsTm ## needed? FIXME
		mt = (t0 + t1)/2.0
		dt = (t1 - t0)/2.0
		###
		try:
			self.root = self.addStep(self.root, t0, t1, mt, dt, eid)
		except:
			myRaise()
		try:
			hp = self.byId[eid]
		except KeyError:
			hp = self.byId[eid] = MaxHeap()
		hp.push(mt, dt)## FIXME
	def searchStep(self, node, t0, t1):
		if not node:
			raise StopIteration
		t0 = max(t0, node.min_t)
		t1 = min(t1, node.max_t)
		if t0 >= t1:
			raise StopIteration
		###
		for item in self.searchStep(node.left, t0, t1):
			yield item
		###
		min_dt = abs((t0 + t1)/2.0 - node.mt) - (t1 - t0)/2.0
		if min_dt <= 0:
			for dt, eid in node.events.getAll():
				yield node.mt, dt, eid
		else:
			for dt, eid in node.events.moreThan(min_dt):
				yield node.mt, dt, eid
		###
		for item in self.searchStep(node.right, t0, t1):
			yield item
	def search(self, t0, t1):
		for mt, dt, eid in self.searchStep(self.root, t0, t1):
			yield (
				max(t0, mt-dt),
				min(t1, mt+dt),
				eid,
				2*dt,
			)
	def getLastBefore(self, t1):
		res = self.getLastBeforeStep(self.root, t1)
		if res:
			mt, dt, eid = res
			return mt-dt, mt+dt, eid
	def getLastBeforeStep(self, node, t1):
		if not node:
			return
		t1 = min(t1, node.max_t)
		if t1 <= node.min_t:
			return
		###
		right_res = self.getLastBeforeStep(node.right, t1)
		if right_res:
			return right_res
		###
		if node.mt < t1:
			dt, eid = node.events.getMax()
			return node.mt, dt, eid
		###
		return self.getLastBeforeStep(node.left, t1)
	def getMinNode(self, node):
		if not node:
			return
		while node.left:
			node = node.left
		return node
	def deleteMinNode(self, node):
		if not node.left:
			return node.right
		node.left = self.deleteMinNode(node.left)
		return node
	def deleteStep(self, node, mt, dt, eid):
		if not node:
			return
		if mt < node.mt:
			node.left = self.deleteStep(node.left, mt, dt, eid)
		elif mt > node.mt:
			node.right = self.deleteStep(node.right, mt, dt, eid)
		else:## mt == node.mt
			node.events.delete(dt, eid)
			if not node.events:## Cleaning tree, not essential
				if not node.right:
					return node.left
				if not node.left:
					return node.right
				node2 = node
				node = self.getMinNode(node2.right)
				node.right = self.deleteMinNode(node2.right)
				node.left = node2.left
		## node.updateCount()
		return node
	def delete(self, eid):
		try:
			hp = self.byId[eid]
		except KeyError:
			return 0
		else:
			n = 0
			for mt, dt in hp.getAll():
				try:
					self.root = self.deleteStep(self.root, mt, dt, eid)
				except:
					myRaise()
				else:
					n += 1
			del self.byId[eid]
			return n
	def getLastOfEvent(self, eid):
		try:
			hp = self.byId[eid]
		except KeyError:
			return
		try:
			mt, dt = hp.getMax()
		except ValueError:
			return
		return mt-dt, mt+dt
	def getFirstOfEvent(self, eid):
		try:
			hp = self.byId[eid]
		except KeyError:
			return
		try:
			mt, dt = hp.getMin()## slower than getMax, but twice faster than max() and
		except ValueError:
			return
		return mt-dt, mt+dt
	#def deleteMoreThanStep(self, node, t0):
	#	if not node:
	#		return
	#	if node.max_t <= t0:
	#		return node
	#	max_dt = node.mt - t0
	#	if max_dt > 0:
	#		node.events.deleteLessThan(max_dt) ## FIXME
	#	self.deleteMoreThanStep(self, node.left, t0)
	#	self.deleteMoreThanStep(self, node.right, t0)
	#def deleteMoreThan(self, t0):
	#	self.root = self.deleteMoreThanStep(self.root, t0)
	getDepthNode = lambda self, node:\
		1 + max(
			self.getDepthNode(node.left),
			self.getDepthNode(node.right),
		) if node else 0
	getDepth = lambda self: self.getDepthNode(self.root)
	def calcAvgDepthStep(self, node, depth):
		if not node:
			return 0, 0
		left_s, left_n = self.calcAvgDepthStep(node.left, depth+1)
		right_s, right_n = self.calcAvgDepthStep(node.right, depth+1)
		return (
			len(node.events) * depth + left_s + right_s,
			len(node.events) + left_n + right_n,
		)
	def calcAvgDepth(self):
		s, n = self.calcAvgDepthStep(self.root, 0)
		if n > 0:
			return float(s) / n



if __name__=='__main__':
	from random import shuffle
	n = 100
	ls = list(range(n))
	shuffle(ls)
	tree = EventSearchTree()
	for x in ls:
		tree.add(x, x+4, x)
	print(tree.getLastBefore(15.5))



