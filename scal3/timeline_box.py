from time import time as now

from scal3.locale_man import tr as _
from scal3.core import debugMode
from scal3 import ui


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

boxSkipPixelLimit = 0.1 ## pixels

rotateBoxLabel = -1

#########################################

class Box:
	def __init__(
		self,
		t0,
		t1,
		odt,
		u0,
		du,
		text='',
		color=None,
		ids=None,
		lineW=2,
	):
		self.t0 = t0
		self.t1 = t1
		self.odt = odt ## original delta t
		#self.mt = (t0+t1)/2.0 ## - timeMiddle ## FIXME
		#self.dt = (t1-t0)/2.0
		#if t1-t0 != odt:
		#	print('Box, dt=%s, odt=%s'%(t1-t0, odt))
		self.u0 = u0
		self.du = du
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
		self.lineW = lineW
		####
		self.hasBorder = False
		self.tConflictBefore = []
	mt_key = lambda self: self.mt
	dt_key = lambda self: -self.dt
	#########
	def setPixelValues(self, timeStart, pixelPerSec, beforeBoxH, maxBoxH):
		self.x = (self.t0 - timeStart) * pixelPerSec
		self.w = (self.t1 - self.t0) * pixelPerSec
		self.y = beforeBoxH + maxBoxH * self.u0
		self.h = maxBoxH * self.du
	contains = lambda self, px, py: 0 <= px-self.x < self.w and 0 <= py-self.y < self.h

def makeIntervalGraph(boxes):
	try:
		from scal3.graph_utils import Graph
	except ImportError:
		return
	g = Graph()
	n = len(boxes)
	g.add_vertices(n - g.vcount())
	g.vs['name'] = list(range(n))
	####
	points = [] ## (time, isStart, boxIndex)
	for boxI, box in enumerate(boxes):
		points += [
			(box.t0, True, boxI),
			(box.t1, False, boxI),
		]
	points.sort()
	openBoxes = set()
	for t, isStart, boxI in points:
		if isStart:
			g.add_edges([
				(boxI, oboxI) for oboxI in openBoxes
			])
			openBoxes.add(boxI)
		else:
			openBoxes.remove(boxI)
	return g




def renderBoxesByGraph(boxes, graph, minColor, minU):
	colorCount = max(graph.vs['color']) - minColor + 1
	if colorCount < 1:
		return
	du = (1.0-minU) / colorCount
	min_vertices = graph.vs.select(color_eq=minColor) ## a VertexSeq
	for v in min_vertices:
		box = boxes[v['name']]
		box_du = du * v['color_h']
		box.u0 = minU if boxReverseGravity else 1 - minU - box_du
		box.du = box_du
	graph.delete_vertices(min_vertices)
	for sgraph in graph.decompose():
		renderBoxesByGraph(
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
	try:
		from scal3.graph_utils import Graph, colorGraph
	except ImportError:
		errorBoxH = 0.8 ## FIXME
		return [
			Box(
				timeStart,
				timeEnd,
				timeEnd - timeStart,
				1-errorBoxH, ## u0
				errorBoxH, ## du
				text = 'Install "python3-igraph" to see events',
				color = (128, 0, 0),## FIXME
				lineW = 2*boxLineWidth,
			)
		]
	boxesDict = {}
	#timeMiddle = (timeStart + timeEnd) / 2.0
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
			#	print('----- bad eid from search: %r'%eid)
			#	continue
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
				text = event.getText(False),
				color = group.color,## or event.color FIXME
				ids = (group.id, event.id) if pixBoxW > 0.5 else None,
				lineW = lineW,
			)
			box.hasBorder = (borderTm > 0 and event.name in movableEventTypes)
			boxValue = (groupIndex, t0, t1)
			try:
				boxesDict[boxValue].append(box)
			except KeyError:
				boxesDict[boxValue] = [box]
	###
	if debugMode:
		t0 = now()
	boxes = []
	for bvalue, blist in sorted(boxesDict.items()):
		if len(blist) < 4:
			boxes += blist
		else:
			box = blist[0]
			box.text = _('%s events')%_(len(blist))
			box.ids = None
			#print('len(blist) = %s'%len(blist))
			#print('%s secs'%(box.t1 - box.t0))
			boxes.append(box)
	del boxesDict
	#####
	if not boxes:
		return []
	#####
	if debugMode:
		t1 = now()
	###
	graph = makeIntervalGraph(boxes)
	if debugMode:
		print('makeIntervalGraph: %e'%(now()-t1))
	###
	#####
	colorGraph(graph)
	renderBoxesByGraph(boxes, graph, 0, 0)
	if debugMode:
		print('box placing time:  %e'%(now()-t0))
		print('')
	return boxes





