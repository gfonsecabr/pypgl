"""The Voronoi diagram of a point set, as the dual of its Delaunay triangulation.

The Python port of pgl's `examples/example_voronoi.cpp`.

The diagram is an `Arrangement` whose every face carries the site that generated
it as its label, so `diagram.label(diagram.locateFace(q))` is the site nearest
to `q` -- no separate nearest-neighbor structure needed. The arrows run from
each red query point to the blue site its face names.

Output: example_voronoi.svg
"""

import pypgl as pgl


def main():
    sites = [
        pgl.Point(8, 12), pgl.Point(24, 38), pgl.Point(45, 10), pgl.Point(68, 22),
        pgl.Point(84, 48), pgl.Point(58, 68), pgl.Point(31, 70), pgl.Point(47, 43),
        pgl.Point(72, 54), pgl.Point(14, 58),
    ]

    canvas = pgl.Canvas()
    canvas.stroke("#1d4ed8").fill("#1d4ed8").pointRadius("6")
    canvas.draw(sites)

    diagram = pgl.Triangulation(sites).voronoiDiagram()
    diagram.buildPointLocation()

    # The unbounded Voronoi edges are clipped to the fitted viewport by the
    # canvas; no artificial bounding rectangle is part of the arrangement.
    canvas.stroke("#64748b").strokeWidth("2px").fill("none")
    canvas.draw(diagram.edges())

    queries = [
        pgl.Point(16, 20), pgl.Point(35, 27), pgl.Point(52, 53),
        pgl.Point(79, 34), pgl.Point(21, 45),
    ]
    canvas.stroke("#f19e9e").fill("#f19e9e").pointRadius("3")
    canvas.draw(queries)

    # Each query point joined to the site its Voronoi cell is labelled with.
    arrows = [
        pgl.OrientedSegment(query, diagram.label(diagram.locateFace(query)))
        for query in queries
    ]
    for arrow in arrows:
        print(arrow)

    canvas.stroke("#f59e0b").strokeWidth("2px").fill("none")
    canvas.draw(arrows)

    canvas.writeSVG("example_voronoi.svg")
    print("wrote example_voronoi.svg")


if __name__ == "__main__":
    main()
