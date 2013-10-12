from igraph import Graph


def colorGraph(g):
    ## Using 'SL' (Smalest Last) algorithm
    n = g.vcount()
    adjlist = g.get_adjlist()
    g.vs['color'] = [None]*n
    for row in sorted(
        [
            (-g.degree(i), i) for i in range(n)
        ],
    ):
        i = row[1]
        colors = set()
        for j in adjlist[i]:
            c = g.vs[j]['color']
            if c is not None:
                colors.add(c)
        c = 0
        while c in colors:
            c += 1
        g.vs[i]['color'] = c



