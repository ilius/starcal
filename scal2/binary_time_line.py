import sys
from math import log

sys.path.append('/starcal2')

from scal2.time_utils import *
from scal2.core import to_jd, jd_to, convert, DATE_GREG, floatJdEncode

J2000 = to_jd(2000, 1, 1, DATE_GREG)


class Node:
    def __init__(self, parent, base, level, offset, rightOri):
        self.parent = parent
        self.base = base ## 8 or 16 is better
        self.level = level ## base ** level is the mathematical scope of the node (with its children)
        ## level > 0
        self.offset = offset ## in days
        self.rightOri = rightOri ## FIXME
        self.clear()
        ###
        ## self.next ? FIXME
        ## next node with the same level (not a child of it)
    def clear(self):
        self.children = {} ## possible keys are 0 to base-1, or -(base-1) to 0
        self.events = [] ## list of tuples (rel_start, rel_end, event_id)
    def getIndexRange(self, t0, t1):
        if self.rightOri:
            dt = self.base ** (self.level - 1)
            i0 = max(0, int((t0-self.offset) // dt))
            i1 = min(self.base, int((t1-1-self.offset)//dt) + 1)
            return range(i0, i1)
        else:
            dt = self.base ** (self.level - 1)
            i0 = min(0, int((t0-self.offset) // dt))
            i1 = max(-self.base, int((t1+1-self.offset)//dt) + 1)
            return range(i0, i1, -1)
    def getScope(self):
        if self.rightOri:
            return self.offset, self.offset + self.base ** self.level
        else:
            return self.offset - self.base ** self.level, self.offset
    def inScope(self, tm):
        s = self.getScope()
        return s[0] <= tm <= s[1]
    def getEvents(self, t0, t1):## t0 < t1
        '''
            returns a list of (ev_t0, ev_t1, ev_id) s
        '''
        ## t0 and t1 are absolute. not relative to the self.offset
        ## all time values are in days
        events = []
        for ev_rt0, ev_rt1, ev_id in self.events:
            ev_t0 = ev_rt0 + self.offset
            ev_t1 = ev_rt1 + self.offset
            if overlaps(t0, t1, ev_t0, ev_t1):
                ## events.append((ev_t0, ev_t1, ev_id))
                events.append((max(t0, ev_t0), min(t1, ev_t1), ev_id))
        if self.children:
            for i in self.getIndexRange(t0, t1):
                try:
                    child = self.children[i]
                except KeyError:
                    pass
                else:
                    events += child.getEvents(t0, t1)
        return events
    newChild = lambda self, index: Node(
        self,
        self.base,
        self.level-1,
        self.offset + index * self.base ** (self.level - 1),
        self.rightOri,
    )
    #def getChildAtIndex(
    def getChildAtTime(self, tm):
        if not self.inScope(tm):
            #print 'Out of scope, level=%s, offset=%s, rightOri=%s'%(self.level, self.offset, self.rightOri)
            return None
        dt = self.base ** (self.level - 1)
        index = int((tm-self.offset) // dt)
        try:
            child = self.children[index]
        except KeyError:
            child = self.children[index] = self.newChild(index)
        return child
    def newParent(self):
        parent = Node(
             None,
             self.base,
             self.level+1,
             self.offset,
             self.rightOri,
        )
        self.parent = parent
        parent.children[0] = self
        return parent

class CenterNode:
    def __init__(self, base=8, offset=J2000):
        self.base = base
        self.offset = offset
        self.clear()
    def clear(self):
        self.right = Node(None, self.base, 1, self.offset, True)
        self.left = Node(None, self.base, 1, self.offset, False)
    def getEvents(self, t0, t1):
        if self.offset <= t0:
            return self.right.getEvents(t0, t1)
        elif t0 < self.offset < t1:
            return self.left.getEvents(t0, self.offset) + self.right.getEvents(self.offset, t1)
        elif t1 <= self.offset:
            return self.left.getEvents(t0, t1)
        else:
            raise RuntimeError
    #def calcCoverNode(self, t0, t1):
    #    base = self.base
    #    dt0 = abs(t0-self.offset)
    #    dt1 = abs(t1-self.offset)
    #    if min(dt0, dt1) < base:## FIXME
    #        return (0, 0)
    #    lgb = log(base)
    #    lgt0 = log(dt0)
    #    lgt1 = log(dt1)
    #    flevel_t0 = lgt0 / lgb
    #    flevel_t1 = lgt1 / lgb
    #    testLevel = max(
    #        ifloor(flevel_t0),
    #        ifloor(flevel_t1) + 1,
    #    )
    #    while True:
    #        w = base**testLevel
    #        factor_t0 = dt0 // w
    #        factor_t1 = dt1 // w
    #        if factor_t0 == factor_t1:
    #            return (testLevel, factor_t0)
    #        testLevel += 1
    def addEvent(self, t0, t1, ev_id):
        #if t1 < t0:
        #    print 'CenterNode.addEvent, dt=%s'%(t1-t0)
        if self.offset <= t0:
            isRight = True
            node = self.right
        elif t0 < self.offset < t1:
            self.addEvent(t0, self.offset, ev_id)
            self.addEvent(self.offset, t1, ev_id)
            return
        elif t1 <= self.offset:
            isRight = False
            node = self.left
        else:
            raise RuntimeError
        ########
        #level, factor = self.calcCoverNode(t0, t1)
        while True:
            #if node.inScope(t0) and node.level >= level:
            if node.inScope(t0) and node.inScope(t1):
                break
            node = node.newParent()
        if isRight:
            self.right = node
        else:
            self.left = node
        while True:
            childNode = node.getChildAtTime(t0)
            if childNode.inScope(t1):
                node = childNode
            else:
                break
        #while node.level > level:
            #childNode = node.getChildAtTime(t0)
            #if not childNode:
            #    print 'Out of scope'
            #    return
            #node = childNode
        node.events.append((t0-node.offset, t1-node.offset, ev_id))


def inputDate(msg):
    while True:
        try:
            date = raw_input(msg)
        except KeyboardInterrupt:
            return
        if date == 'q':
            return
        try:
            return dateDecode(date)
        except Exception, e:
            print str(e)

def inputDateJd(msg):
    date = inputDate(msg)
    if date:
        (y, m, d) = date
        return to_jd(y, m, d, DATE_GREG)


def test():
    from scal2 import ui
    ui.eventGroups.load()
    startJd = to_jd(2010, 1, 1, DATE_GREG)
    endJd = to_jd(2013, 1, 1, DATE_GREG)
    for group in ui.eventGroups:
        group.node = CenterNode()
        if not group.enable:
            continue
        for event in group:
            for t0, t1 in event.calcOccurrenceForJdRange(startJd, endJd).getFloatJdRangeList():
                group.node.addEvent(t0, t1, event.id)
    while True:
        startJd = inputDateJd('Start Date: ')
        if not startJd:
            break
        endJd =   inputDateJd('  End Date: ')
        if not endJd:
            break
        print 'Events:'
        for group in ui.eventGroups:
            if not group.enable:
                continue
            for t0, t1, eid in group.node.getEvents(startJd, endJd):
                print floatJdEncode(t0, DATE_GREG) + '\tto\t' + floatJdEncode(t1, DATE_GREG) + '\t' + group[eid].summary
    print

if __name__=='__main__':
    test()
                    
    




