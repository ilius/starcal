#!/usr/bin/env python3
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

import logging
from scal3 import logger
log = logger.get()
debugMode = log.level <= logging.DEBUG

from time import time as now

from scal3.locale_man import tr as _
from scal3 import ui
from scal3.timeline import tl


movableEventTypes = (
	"task",
	"lifeTime",
)

#########################################


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
	):
		self.t0 = t0
		self.t1 = t1
		self.odt = odt ## original delta t
		#self.mt = (t0+t1)/2.0 ## - timeMiddle ## FIXME
		#self.dt = (t1-t0)/2.0
		#if t1-t0 != odt:
		#	log.info(f"Box, dt={}t1-t0, odt={odt}")
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

	def mt_key(self):
		return self.mt

	def dt_key(self):
		return -self.dt

	#########

	def setPixelValues(self, timeStart, pixelPerSec, beforeBoxH, maxBoxH):
		self.x = (self.t0 - timeStart) * pixelPerSec
		self.w = (self.t1 - self.t0) * pixelPerSec
		self.y = beforeBoxH + maxBoxH * self.u0
		self.h = maxBoxH * self.du

	def contains(self, px, py):
		return 0 <= px - self.x < self.w and 0 <= py - self.y < self.h


def makeIntervalGraph(boxes):
	try:
		from scal3.graph_utils import Graph
	except ImportError:
		return
	g = Graph()
	n = len(boxes)
	g.add_vertices(n - g.vcount())
	g.vs["name"] = list(range(n))
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
	colorCount = max(graph.vs["color"]) - minColor + 1
	if colorCount < 1:
		return
	du = (1.0 - minU) / colorCount
	min_vertices = graph.vs.select(color_eq=minColor) ## a VertexSeq
	for v in min_vertices:
		box = boxes[v["name"]]
		box_du = du * v["color_h"]
		box.u0 = minU if tl.boxReverseGravity else 1 - minU - box_du
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
				1 - errorBoxH,  # u0
				errorBoxH,  # du
				text="Install \"python3-igraph\" to see events",
				color=(128, 0, 0),## FIXME
				lineW=2 * boxLineWidth,
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
		for t0, t1, eid, odt in group.occur.search(
			timeStart - borderTm,
			timeEnd + borderTm,
		):
			pixBoxW = (t1 - t0) * pixelPerSec
			if pixBoxW < tl.boxSkipPixelLimit:
				continue
			#if not isinstance(eid, int):
			#	log.error(f"----- bad eid from search: {eid!r}")
			#	continue
			event = group[eid]
			eventIndex = group.index(eid)
			if t0 <= timeStart and timeEnd <= t1:## Fills Range ## FIXME
				continue
			lineW = tl.boxLineWidth
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
			box.hasBorder = (borderTm > 0 and event.name in movableEventTypes)
			boxValue = (groupIndex, t0, t1)
			toAppend = boxesDict.get(boxValue)
			if toAppend is None:
				boxesDict[boxValue] = [box]
			else:
				boxesDict[boxValue].append(box)

	###
	if debugMode:
		t0 = now()
	boxes = []
	for boxValue, boxGroup in sorted(boxesDict.items()):
		if len(boxGroup) < 4:
			boxes += boxGroup
		else:
			box = boxGroup[0]
			box.text = _("{eventCount} events").format(
				eventCount=_(len(boxGroup)),
			)
			box.ids = None
			# log.debug(f"len(boxGroup) = {len(boxGroup)}")
			# log.debug(f"{box.t1 - box.t0} secs")
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
		log.debug(f"makeIntervalGraph: {now() - t1:e}")
	###
	#####
	colorGraph(graph)
	renderBoxesByGraph(boxes, graph, 0, 0)
	if debugMode:
		log.debug(f"box placing time:  {now() - t0:e}")
		log.debug("")
	return boxes
