from scal2.interval_utils import overlaps
from scal2.event_search_tree import EventSearchTree
from scal2.event_man import epsTm
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
boxMaxHeightFactor = 0.8 ## < 1.0

boxSkipPixelLimit = 0.1 ## pixels

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
    tOverlaps = lambda self, other: overlaps(self.t0, self.t1, other.t0, other.t1)
    yOverlaps = lambda self, other: overlaps(self.u0, self.u1, other.u0, other.u1)
    dt = lambda self: self.t1 - self.t0
    du = lambda self: self.u1 - self.u0
    def __cmp__(self, other):## FIXME
        c = -cmp(self.odt, other.odt)
        if c != 0: return c
        return cmp(self.order, other.order)
    def setPixelValues(self, timeStart, pixelPerSec, beforeBoxH, maxBoxH):
        self.x = (self.t0 - timeStart) * pixelPerSec
        self.w = (self.t1 - self.t0) * pixelPerSec
        self.y = beforeBoxH + maxBoxH * self.u0
        self.h = maxBoxH * (self.u1 - self.u0)
    contains = lambda self, px, py: 0 <= px-self.x < self.w and 0 <= py-self.y < self.h


def calcEventBoxes(
    timeStart,
    timeWidth,
    pixelPerSec,
):
    timeEnd = timeStart + timeWidth
    borderTm = (boxMoveBorder + boxMoveLineW) / pixelPerSec
    ####
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
            box.hasBorder = (event.name in movableEventTypes)
            boxValue = (group.id, t0, t1)
            try:
                boxesDict[boxValue].append(box)
            except KeyError:
                boxesDict[boxValue] = [box]
    ###
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
    boxes.sort() ## FIXME
    ##
    boundaries = set()
    for box in boxes:
        boundaries.add(box.t0)
        boundaries.add(box.t1)
    boundaries = sorted(boundaries)
    ##
    segNum = len(boundaries) - 1
    segCountList = [0] * segNum
    boxesIndex = []
    for boxI, box in enumerate(boxes):
        segI0 = boundaries.index(box.t0)
        segI1 = boundaries.index(box.t1)
        boxesIndex.append((box, boxI, segI0, segI1))
        for i in range(segI0, segI1):
            segCountList[i] += 1
    placedBoxes = EventSearchTree()
    for box, boxI, segI0, segI1 in boxesIndex:
        conflictRanges = []
        for c_t0, c_t1, c_boxI, c_dt in placedBoxes.search(
            box.t0 + epsTm,
            box.t1 - epsTm,
        ):## FIXME
            c_box = boxes[c_boxI]
            '''
            if not box.tOverlaps(c_box):
                min4 = min(box.t0, c_box.t0)
                max4 = max(box.t1, c_box.t1)
                dmm = max4 - min4
                tran = lambda t: (t-min4)/dmm
                print 'no overlap (%s, %s) and (%s, %s)'%(
                    tran(box.t0),
                    tran(box.t1),
                    tran(c_box.t0),
                    tran(c_box.t1),
                )
                ## box.t1 == c_box.t0   OR   c_box.t1 == box.t0
                ## this should not be returned in EventSearchTree.search()
                ## FIXME
                continue
            '''
            conflictRanges.append((c_box.u0, c_box.u1))
        freeSpaces = realRangeListsDiff([(0, 1)], conflictRanges)
        if not freeSpaces:
            print 'unable to find a free space for box, box.ids=%s'%(box.ids,)
            box.u0 = box.u1 = 0
            continue
        if boxReverseGravity:
            freeSpaces.reverse()
        height = min(
            max([sp[1] - sp[0] for sp in freeSpaces]),
            boxMaxHeightFactor / max(segCountList[segI0:segI1]),
        )
        freeSp = None
        for sp in freeSpaces:
            if sp[1] - sp[0] >= height:
                freeSp = sp
                break
        freeSpH = freeSp[1] - freeSp[0]
        if 0.5*freeSpH < height < 0.75*freeSpH:## for better height balancing FIXME
            height = 0.5*freeSpH
        if boxReverseGravity:
            box.u0 = freeSp[0]
            box.u1 = box.u0 + height
        else:
            box.u1 = freeSp[1]
            box.u0 = box.u1 - height
        placedBoxes.add(box.t0, box.t1, boxI)
    return boxes





