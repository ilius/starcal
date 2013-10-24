from igraph import Graph


def colorGraph(g):
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



