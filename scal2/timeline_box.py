from time import time as now

from scal2.interval_utils import ab_overlaps, md_overlaps
from scal2.graph_utils import *
from scal2.event_search_tree import EventSearchTree
from scal2.locale_man import tr as _
from scal2.core import debugMode
from scal2.event_lib import epsTm
from scal2 import ui


movableEventTypes = (
    'task',
    'lifeTime',
)

#########################################

boxLineWidth = 2
boxInnerAlpha = 0.1

boxMoveBorder = 10
boxMoveLineW = 0.5

editingBoxHelperLineWidth = 0.3 ## px


#boxColorSaturation = 1.0
#boxColorLightness = 0.3 ## for random colors


boxReverseGravity = False
boxSortByWidth = True ## wider boxes are lower (with normal gravity)
boxMaxHeightFactor = 0.8 ## < 1.0

boxSkipPixelLimit = 0.1 ## pixels

rotateBoxLabel = -1

#########################################

def realRangeListsDiff(r1, r2):
    boundary = set()
    for (a, b) in r1+r2:
        boundary.add(a)
        boundary.add(b)
    boundaryList = sorted(boundary)
    ###
    ri1 = [] ## range1 indexes
    for (a, b) in r1:
        ri1 += range(boundaryList.index(a), boundaryList.index(b))
    ###
    ri2 = [] ## range2 indexes
    for (a, b) in r2:
        ri2 += range(boundaryList.index(a), boundaryList.index(b))
    ###
    ri3 = sorted(set(ri1).difference(set(ri2)))
    r3 = []
    pending = []
    for i in ri3:
        if pending:
            i2 = pending[-1] + 1
            if i2 < i:
                i1 = pending[0]
                r3.append((boundaryList[i1], boundaryList[i2]))
                pending = []
        pending.append(i)
    if pending:
        i1 = pending[0]
        i2 = pending[-1] + 1
        r3.append((boundaryList[i1], boundaryList[i2]))
    return r3

class Box:
    def __init__(
        self, t0, t1, odt, u0, u1,
        text='',
        color=None,
        ids=None,
        order=None,
        lineW=2,
    ):
        self.t0 = t0
        self.t1 = t1
        self.odt = odt ## original delta t
        self.tm = (t0+t1)/2.0
        self.td = (t1-t0)/2.0
        #if t1-t0 != odt:
        #    print 'Box, dt=%s, odt=%s'%(t1-t0, odt)
        self.u0 = u0
        self.u1 = u1
        ####
        self.x = None
        self.w = None
        self.y = None
        self.h = None
        ####
        self.text = text
        if color is None:
            color = ui.textColor ## FIXME
        self.color = color
        self.ids = ids ## (groupId, eventId)
        self.order = order ## (groupIndex, eventIndex)
        self.lineW = lineW
        ####
        self.hasBorder = False
        self.tConflictBefore = []
    #tOverlaps = lambda self, other: ab_overlaps(self.t0, self.t1, other.t0, other.t1)
    tOverlaps = lambda self, other: md_overlaps(self.tm, self.td, other.tm, other.td)
    yOverlaps = lambda self, other: ab_overlaps(self.u0, self.u1, other.u0, other.u1)
    dt = lambda self: self.t1 - self.t0
    du = lambda self: self.u1 - self.u0
    def __cmp__(self, other):## FIXME
        if boxSortByWidth:
            c = -cmp(self.odt, other.odt)
            if c != 0:
                return c
        return cmp(self.order, other.order)
    def setPixelValues(self, timeStart, pixelPerSec, beforeBoxH, maxBoxH):
        self.x = (self.t0 - timeStart) * pixelPerSec
        self.w = (self.t1 - self.t0) * pixelPerSec
        self.y = beforeBoxH + maxBoxH * self.u0
        self.h = maxBoxH * (self.u1 - self.u0)
    contains = lambda self, px, py: 0 <= px-self.x < self.w and 0 <= py-self.y < self.h


def updateBoxesForGraph(boxes, graph, minColor, minU):
    colorCount = max(graph.vs['color']) - minColor + 1
    if colorCount < 1:
        return
    du = (1.0-minU) / colorCount
    min_vertices = graph.vs.select(color_eq=minColor) ## a VertexSeq
    for v in min_vertices:
        box = boxes[v['name']]
        if boxReverseGravity:
            box.u0, box.u1 = minU, minU + du
        else:
            box.u0, box.u1 = 1 - minU - du, 1 - minU
    graph.delete_vertices(min_vertices)
    for sgraph in graph.decompose():
        updateBoxesForGraph(
            boxes,
            sgraph,
            minColor + 1,
            minU + du,
        )


def calcEventBoxes(
    timeStart,
    timeEnd,
    pixelPerSec,
    borderTm,
):
    boxesDict = {}
    for groupIndex in range(len(ui.eventGroups)):
        group = ui.eventGroups.byIndex(groupIndex)
        if not group.enable:
            continue
        if not group.showInTimeLine:
            continue
        for t0, t1, eid, odt in group.occur.search(timeStart-borderTm, timeEnd+borderTm):
            pixBoxW = (t1-t0) * pixelPerSec
            if pixBoxW < boxSkipPixelLimit:
                continue
            #if not isinstance(eid, int):
            #    print '----- bad eid from search: %r'%eid
            #    continue
            event = group[eid]
            eventIndex = group.index(eid)
            if t0 <= timeStart and timeEnd <= t1:## Fills Range ## FIXME
                continue
            lineW = boxLineWidth
            if lineW >= 0.5*pixBoxW:
                lineW = 0
            box = Box(
                t0,
                t1,
                odt,
                0,
                1,
                text = event.getSummary(),
                color = group.color,## or event.color FIXME
                ids = (group.id, event.id) if pixBoxW > 0.5 else None,
                order = (groupIndex, eventIndex),
                lineW = lineW,
            )
            box.hasBorder = (borderTm > 0 and event.name in movableEventTypes)
            boxValue = (group.id, t0, t1)
            try:
                boxesDict[boxValue].append(box)
            except KeyError:
                boxesDict[boxValue] = [box]
    ###
    if debugMode:
        t0 = now()
    boxes = []
    for bvalue, blist in boxesDict.iteritems():
        if len(blist) < 4:
            boxes += blist
        else:
            box = blist[0]
            box.text = _('%s events')%_(len(blist))
            box.ids = None
            #print 'len(blist)', len(blist)
            #print (box.t1 - box.t0), 'secs'
            boxes.append(box)
    del boxesDict
    #####
    if not boxes:
        return []
    ###
    boxes.sort(reverse=boxReverseGravity) ## FIXME
    ###
    graph = makeIntervalGraph(boxes, Box.tOverlaps)
    colorGraph(graph)
    updateBoxesForGraph(boxes, graph, 0, 0)
    if debugMode:
        print 'box placing time: %e'%(now()-t0)
    return boxes





