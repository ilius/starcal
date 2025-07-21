from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from collections.abc import Callable

	from igraph import Graph

__all__ = ["addBoxHeightToColoredGraph", "colorGraph"]


def colorGraph(g: Graph, vertexSortKey: Callable[[int], Any]) -> None:
	"""VertexSortKey is the key function for sorting vertices."""
	# Using "SL" (Smalest Last) algorithm
	n = g.vcount()
	adjlist = g.get_adjlist()
	colors: list[int | None] = [None] * n
	for i in sorted(
		range(n),
		key=vertexSortKey,
	):
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


def addBoxHeightToColoredGraph(g: Graph) -> None:
	n = g.vcount()
	adjlist = g.get_adjlist()
	colors = g.vs["color"]
	colorCount = max(colors) + 1
	heightList = [1 for i in range(n)]
	for i, c in enumerate(colors):
		adjColors = {colors[j] for j in adjlist[i]}
		for c_end in range(c + 1, colorCount + 1):
			if c_end in adjColors:
				heightList[i] = c_end - c
				break
	g.vs["box_height"] = heightList
