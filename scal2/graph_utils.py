from igraph import Graph

def makeIntervalGraph(intervals, overlaps):
    g = Graph()
    n = len(intervals)
    g.add_vertices(n-1)
    g.vs['name'] = range(n)
    for i in range(1, n):
        xi = intervals[i]
        for j in range(i):
            if overlaps(xi, intervals[j]):
                g.add_edges([
                    (i, j),
                ])
    return g


def assignComponents(g):
    g.vs['component'] = [None]*g.vcount()
    subgraphs = g.decompose()
    for compI, sg in enumerate(subgraphs):
        for v in sg.vs:
            origV = g.vs[v['name']]
            origV['component'] = compI
    return len(subgraphs)


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



