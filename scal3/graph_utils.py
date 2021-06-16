#!/usr/bin/env python3
from igraph import Graph


def colorGraph(g: Graph, vertexSortKey: "Callable[[Graph, int], [Any]]"):
	"""
		vertexSortKey is the key function for sorting vertices
		it must return a tuple, in which the last item is vertex index
	"""
	# Using "SL" (Smalest Last) algorithm
	n = g.vcount()
	adjlist = g.get_adjlist()
	colors = [None] * n
	for row in sorted(
		vertexSortKey(g, i) for i in range(n)
	):
		i = row[-1]
		adjColors = set()
		for j in adjlist[i]:
			c = colors[j]
			if c is not None:
				adjColors.add(c)
		c = 0
		while c in adjColors:
			c += 1
		colors[i] = c
	g.vs["color"] = colors

def addBoxHeightToColoredGraph(g):
	n = g.vcount()
	adjlist = g.get_adjlist()
	colors = g.vs["color"]
	colorCount = max(colors) + 1
	heightList = [1 for i in range(n)]
	for i, c in enumerate(colors):
		adjColors = set()
		for j in adjlist[i]:
			adjColors.add(colors[j])
		for c_end in range(c + 1, colorCount + 1):
			if c_end in adjColors:
				heightList[i] = c_end - c
				break
	g.vs["box_height"] = heightList
