from igraph import Graph


def colorGraph(g, add_height=True):
	## Using 'SL' (Smalest Last) algorithm
	n = g.vcount()
	adjlist = g.get_adjlist()
	colors = [None]*n
	for d, i in sorted(
		[
			(-g.degree(i), i) for i in range(n)
		],
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
	g.vs['color'] = colors
	if add_height:
		colorCount = max(colors) + 1
		height = [1 for i in range(n)]
		for i, c in enumerate(colors):
			adjColors = set()
			for j in adjlist[i]:
				adjColors.add(colors[j])
			for c_end in range(c+1, colorCount+1):
				if c_end in adjColors:
					height[i] = c_end - c
					break
		g.vs['color_h'] = height








