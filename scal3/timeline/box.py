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

import logging

from scal3 import logger

log = logger.get()

from time import perf_counter

from scal3 import ui
from scal3.locale_man import tr as _
from scal3.timeline import conf
from scal3.ui import conf as uiconf

__all__ = ["calcEventBoxes"]


debugMode = log.level <= logging.DEBUG

movableEventTypes = (
	"task",
	"lifetime",
)

# -----------------------------------------


class Box:
	def __init__(
		self,
		t0,
		t1,
		odt,
		u0,
		du,
		text="",
		color=None,
		ids=None,
		lineW=2,
	) -> None:
		self.t0 = t0
		self.t1 = t1
		self.odt = odt  # original delta t
		# self.mt = (t0+t1)/2.0  # - timeMiddle # FIXME
		# self.dt = (t1-t0)/2.0
		# if t1-t0 != odt:
		# 	log.info(f"Box, {t1-t0 = }, {odt = }")
		self.u0 = u0
		self.du = du
		# ----
		self.x = None
		self.w = None
		self.y = None
		self.h = None
		# ----
		self.text = text
		if color is None:
			color = uiconf.textColor.v  # FIXME
		self.color = color
		self.ids = ids  # (groupId, eventId)
		self.lineW = lineW
		# ----
		self.hasBorder = False

	# ---------

	def setPixelValues(self, timeStart, pixelPerSec, beforeBoxH, maxBoxH) -> None:
		self.x = (self.t0 - timeStart) * pixelPerSec
		self.w = (self.t1 - self.t0) * pixelPerSec
		self.y = beforeBoxH + maxBoxH * self.u0
		self.h = maxBoxH * self.du

	def contains(self, px, py):
		return 0 <= px - self.x < self.w and 0 <= py - self.y < self.h


def makeIntervalGraph(boxes):
	try:
		from igraph import Graph
	except ImportError:
		log.exception("error importing Graph")
		return
	g = Graph()
	n = len(boxes)
	g.add_vertices(n)
	g.vs["name"] = list(range(n))
	# ----
	# list[(time: int, isStart: bool, boxIndex: int)]
	points: list[tuple[int, bool, int]] = []
	for boxI, box in enumerate(boxes):
		points += [
			(box.t0, True, boxI),
			(box.t1, False, boxI),
		]
	points.sort()
	openBoxes = set()
	for _t, isStart, boxI in points:
		if isStart:
			g.add_edges([(boxI, oboxI) for oboxI in openBoxes])
			openBoxes.add(boxI)
		else:
			openBoxes.remove(boxI)
	return g


def renderBoxesByGraph(boxes, graph, minColor, minU) -> None:
	colorCount = max(graph.vs["color"]) - minColor + 1
	if colorCount < 1:
		return
	du = (1.0 - minU) / colorCount
	min_vertices = graph.vs.select(color_eq=minColor)  # a VertexSeq
	for v in min_vertices:
		box = boxes[v["name"]]
		box_du = du * v["box_height"]
		box.u0 = minU if conf.boxReverseGravity.v else 1 - minU - box_du
		box.du = box_du
	graph.delete_vertices(min_vertices)
	for subGraph in graph.decompose():
		renderBoxesByGraph(
			boxes,
			subGraph,
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
		from scal3.graph_utils import (
			addBoxHeightToColoredGraph,
			colorGraph,
		)
	except ImportError:
		errorBoxH = 0.8  # FIXME
		return [
			Box(
				timeStart,
				timeEnd,
				timeEnd - timeStart,
				1 - errorBoxH,  # u0
				errorBoxH,  # du
				text='Install "python3-igraph" to see events',
				color=(128, 0, 0),  # FIXME
				lineW=2 * conf.boxLineWidth.v,
			),
		]
	boxesDict = {}
	# timeMiddle = (timeStart + timeEnd) / 2.0
	for groupIndex in range(len(ui.eventGroups)):
		group = ui.eventGroups.byIndex(groupIndex)
		if not group.enable:
			continue
		if not group.showInTimeLine:
			continue
		for item in group.occur.search(
			timeStart - borderTm,
			timeEnd + borderTm,
		):
			t0 = item.start
			t1 = item.end
			eid = item.eid
			odt = item.dt
			pixBoxW = (t1 - t0) * pixelPerSec
			if pixBoxW < conf.boxSkipPixelLimit.v:
				continue
			# if not isinstance(eid, int):
			# 	log.error(f"----- bad eid from search: {eid!r}")
			# 	continue
			event = group[eid]
			if t0 <= timeStart and timeEnd <= t1:
				# Fills Range, FIXME
				continue
			lineW = conf.boxLineWidth.v
			if lineW >= 0.5 * pixBoxW:
				lineW = 0
			box = Box(
				t0,
				t1,
				odt,
				0,
				1,
				text=event.getText(False),
				color=group.color,  # or event.color FIXME
				ids=(group.id, event.id) if pixBoxW > 0.5 else None,
				lineW=lineW,
			)
			box.hasBorder = borderTm > 0 and event.name in movableEventTypes
			boxValue = (groupIndex, t0, t1)
			toAppend = boxesDict.get(boxValue)
			if toAppend is None:
				boxesDict[boxValue] = [box]
			else:
				boxesDict[boxValue].append(box)

	# ---
	if debugMode:
		t0 = perf_counter()
	boxes = []
	for _boxValue, boxGroup in sorted(boxesDict.items()):
		if len(boxGroup) < 4:
			boxes += boxGroup
		else:
			box = boxGroup[0]
			box.text = _("{eventCount} events").format(
				eventCount=_(len(boxGroup)),
			)
			box.ids = None
			# log.debug(f"{len(boxGroup) = }")
			# log.debug(f"{box.t1 - box.t0} secs")
			boxes.append(box)
	del boxesDict
	# -----
	if not boxes:
		return []
	# -----
	if debugMode:
		t1 = perf_counter()
	# ---
	graph = makeIntervalGraph(boxes)
	if graph is None:
		return
	if debugMode:
		log.debug(f"makeIntervalGraph: {perf_counter() - t1:e}")
	# -----

	def boxSortKeyFunc(i: int) -> "tuple[int, int]":
		# the last item should be i
		# the first item should be -g.degree(i) to have less number of colors/levels,
		# and give higher colors to more isolated vertices/boxes
		# adding -boxes[i].odt before i does not seem very effective or useful
		# should I add groupIndex before i?
		return (
			-graph.degree(i),
			i,
		)

	# TODO: assign same color to subsequent events / boxes
	# (box2.t0 == box1.t1)

	colorGraph(graph, boxSortKeyFunc)
	addBoxHeightToColoredGraph(graph)
	renderBoxesByGraph(boxes, graph, 0, 0)
	if debugMode:
		log.debug(f"box placing time:  {perf_counter() - t0:e}")
		log.debug("")
	return boxes
