"""A shortest obstacle-avoiding path across a polygonal room.

The Python port of pgl's `examples/example_visibility.cpp`.

A shortest path inside a region with holes is a polygonal chain whose interior
vertices are all corners of the region: it can only bend where an obstacle
forces it to. So the whole continuous problem collapses onto the visibility
graph, and a shortest path in that graph under Euclidean edge lengths is a
shortest path in the room.

The drawing shows the region in grey, the visibility graph behind it in pale
blue, and the shortest path from one corner to another in orange.

Output: example_visibility.svg
"""

import pypgl as pgl


def main():
    # A rectangular room with three blocks in it, staggered so that no two
    # consecutive gaps line up and the direct line is blocked several times.
    outer = pgl.Polygon([0, 0, 100, 0, 100, 60, 0, 60])
    holes = [
        pgl.Polygon([20, 12, 32, 54, 20, 54]),
        pgl.Polygon([50, 8, 62, 8, 62, 40, 50, 40]),
        pgl.Polygon([78, 20, 90, 20, 90, 45]),
    ]
    room = pgl.PolygonWithHoles(outer, holes)

    if not room.isValid():   # holes inside the outer ring, interiors disjoint
        raise SystemExit("the region is not a valid polygon with holes")

    visibility = room.visibilityGraph()
    source, target = outer[1], outer[3]
    path = visibility.shortestPath(source, target, lambda a, b: a.distance(b))

    if not path:
        raise SystemExit(f"no path from {source} to {target}")

    length = sum(a.distance(b) for a, b in zip(path, path[1:]))

    print(f"visibility graph: {visibility.vertexCount()} vertices, "
          f"{visibility.edgeCount()} edges")
    print(f"shortest path ({len(path)} vertices, length {length:.3f}): "
          + " ".join(str(p) for p in path))

    canvas = pgl.Canvas()
    canvas.stroke("#94a3b8").fill("#e2e8f0").strokeWidth("2px").draw(room)

    canvas.stroke("#bfdbfe").strokeWidth("1px").fill("none")
    canvas.draw(pgl.Segment(u, v) for u, v in visibility.edges())  # each edge once

    canvas.stroke("#ea580c").strokeWidth("3px").draw(pgl.Polyline(path))

    canvas.stroke("#1d4ed8").fill("#1d4ed8").pointRadius("5")
    canvas.draw([source, target])

    canvas.writeSVG("example_visibility.svg")
    print("wrote example_visibility.svg")


if __name__ == "__main__":
    main()
