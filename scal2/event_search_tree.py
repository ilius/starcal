# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Saeed Rasooli <saeed.gnu@gmail.com>
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

sys.path.append('/starcal2')

from scal2.utils import myRaise
from scal2.time_utils import *
from scal2.bin_heap import MaxHeap

class Node:
    def __init__(self, mt, red=True):
        self.mt = mt
        self.red = red
        self.min_t = mt
        self.max_t = mt
        self.events = MaxHeap()
        self.left = None
        self.right = None
        #self.count = 0
    def add(self, t0, t1, dt, eid):
        self.events.add(dt, eid)
        if t0 < self.min_t:
            self.min_t = t0
        if t1 > self.max_t:
            self.max_t = t1
    def updateMinMax(self):
        self.updateMinMaxChild(self.left)
        self.updateMinMaxChild(self.right)
    def updateMinMaxChild(self, child):
        if child:
            if child.max_t > self.max_t:
                self.max_t = child.max_t 
            if child.min_t < self.min_t:
                self.min_t = child.min_t
    #def updateCount(self):
    #    self.count = 1
    #    if self.left:
    #        self.count += self.left.count
    #    if self.right:
    #        self.count += self.right.count


def isRed(x):
    if x is None:
        return False
    return x.red

def rotateLeft(h):
    #assert isRed(h.right)
    x = h.right
    h.right = x.left
    x.left = h
    x.red = h.red
    h.red = True
    return x

def rotateRight(h):
    #assert isRed(h.left)
    x = h.left
    h.left = x.right
    x.right = h
    x.red = h.red
    h.red = True
    return x

def flipColors(h):
    #assert not isRed(h)
    #assert isRed(h.left)
    #assert isRed(h.right)
    h.red = True
    h.left.red = False
    h.right.red = False

class EventSearchTree:
    def __init__(self):
        self.clear()
    def clear(self):
        self.root = None
        self.byId = {}
    def addStep(self, node, t0, t1, mt, dt, eid):
        if t0 >= t1:
            return node
        if node is None:
            node = Node(mt)
            node.add(t0, t1, dt, eid)
            return node
        cm = cmp(mt, node.mt)
        if cm < 0:
            node.left  = self.addStep(node.left , t0, t1, mt, dt, eid)
        elif cm > 0:
            node.right = self.addStep(node.right, t0, t1, mt, dt, eid)
        else:## cm == 0
            node.add(t0, t1, dt, eid)

        if isRed(node.right) and not isRed(node.left):
            node = rotateLeft(node)
        if isRed(node.left) and isRed(node.left.left):
            node = rotateRight(node)
        if isRed(node.left) and isRed(node.right):
            flipColors(node)

        node.updateMinMax()
        #node.updateCount()
        return node
    def add(self, t0, t1, eid, debug=False):
        if debug:
            from time import strftime, localtime
            f = '%F, %T'
            print 'EventSearchTree.add: %s\t%s'%(
                strftime(f, localtime(t0)),
                strftime(f, localtime(t1)),
            )
        try:
            mt = (t0 + t1)/2.0
            dt = (t1 - t0)/2.0
            self.root = self.addStep(self.root, t0, t1, mt, dt, eid)
            try:
                hp = self.byId[eid]
            except KeyError:
                hp = self.byId[eid] = MaxHeap()
            hp.add(mt, dt)## FIXME
        except:
            myRaise()
    #def size(self, node='root'):
    #    if node == 'root':
    #        node = self.root
    #    if node is None:
    #        return 0
    #    return node.count
    def searchStep(self, node, t0, t1):
        if node is None:
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
    def getDepthNode(self, node):
        if node is None:
            return 0
        return 1 + max(
            self.getDepthNode(node.left),
            self.getDepthNode(node.right),
        )
    def getDepth(self):
        return self.getDepthNode(self.root)
    def getMinNode(self, node):
        if node is None:
            return
        while node.left is not None:
            node = node.left
        return node
    def deleteMinNode(self, node):
        if node.left is None:
            return node.right
        node.left = self.deleteMinNode(node.left)
        return node
    def deleteStep(self, node, mt, dt, eid):
        if node is None:
            return None
        cm = cmp(mt, node.mt)
        if cm < 0:
            node.left = self.deleteStep(node.left, mt, dt, eid)
        elif cm > 0:
            node.right = self.deleteStep(node.right, mt, dt, eid)
        else:## cm == 0
            node.events.delete(dt, eid)
            if not node.events:## Cleaning tree, not essential
                if node.right is None:
                    return node.left
                if node.left is None:
                    return node.right
                node2 = node
                node = self.getMinNode(node2.right)
                node.right = self.deleteMinNode(node2.right)
                node.left = node2.left
        #node.count = self.size(node.left) + self.size(node.right) + 1
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
            mt, dt = hp.getMin()
        except ValueError:
            return
        return mt-dt, mt+dt
    '''
    def deleteMoreThanStep(self, node, t0):
        if node is None:
            return None
        if node.max_t <= t0:
            return node
        max_dt = node.mt - t0
        if max_dt > 0:
            node.events.deleteLessThan(max_dt) ## FIXME
        self.deleteMoreThanStep(self, node.left, t0)
        self.deleteMoreThanStep(self, node.right, t0)
    def deleteMoreThan(self, t0):
        self.root = self.deleteMoreThanStep(self.root, t0)
    '''




