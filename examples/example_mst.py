"""The Euclidean minimum spanning tree of a point set, via its Delaunay triangulation.

The Python port of pgl's `examples/example_mst.cpp`.

The triangulation is where the shortcut is: the Euclidean MST of a point set is
a subgraph of its Delaunay triangulation, so the tree of that O(n)-edge graph is
the tree of the complete one. Squaring the distances loses nothing either --
squaring is increasing on non-negative numbers, so it orders the edges exactly
as the distances do -- and it keeps every weight exact, with no square root and
no rounding anywhere in the run.

The drawing shows the triangulation in grey behind the tree in green.

Output: example_mst.svg
"""

import pypgl as pgl


def main():
    points = [
        pgl.Point(8, 12), pgl.Point(24, 38), pgl.Point(45, 10), pgl.Point(68, 22),
        pgl.Point(84, 48), pgl.Point(58, 68), pgl.Point(31, 70), pgl.Point(47, 43),
        pgl.Point(72, 54), pgl.Point(14, 58), pgl.Point(90, 12), pgl.Point(60, 90),
        pgl.Point(20, 88), pgl.Point(38, 20),
    ]

    triangulation = pgl.Triangulation(points)
    graph = triangulation.asGraph()

    # Prim's algorithm. The weight callable chooses its own number type: an
    # exact squared distance keeps every comparison exact.
    mst = graph.spanningTree(lambda a, b: a.squaredDistance(b))

    canvas = pgl.Canvas()
    canvas.stroke("#cbd5e1").strokeWidth("1.5px").fill("none")
    canvas.draw(triangulation.edges())

    canvas.stroke("#078e07").strokeWidth("3px")
    canvas.draw(pgl.Segment(u, v) for u, v in mst.edges())  # each edge once

    canvas.stroke("#1d4ed8").fill("#1d4ed8").pointRadius("5")
    canvas.draw(mst.vertices())

    canvas.writeSVG("example_mst.svg")
    print(f"{graph.edgeCount()} Delaunay edges, {mst.edgeCount()} in the tree")
    print("wrote example_mst.svg")


if __name__ == "__main__":
    main()
