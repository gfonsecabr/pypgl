"""The arrangement of a few crossing segments and lines.

The Python port of pgl's `examples/example_arrangement.cpp`.

Every edge, then every vertex, then the boundary of one face -- the largest
bounded one -- in a color of its own.

The input is integral, but the segments cross at non-lattice points. pypgl's
coordinates are exact rationals, so those vertices are exact rather than
rounded; nothing here approximates until the canvas converts to double to emit
the SVG.

Output: example_arrangement.svg
"""

import pypgl as pgl


def largest_face(arrangement):
    """The bounded face of largest area."""
    best, best_area = None, 0
    for i in range(arrangement.faceCount()):
        face = pgl.FaceId(i)
        if arrangement.isUnbounded(face):
            continue
        area = arrangement.polygonWithHoles(face).twiceArea()
        if best is None or area > best_area:
            best, best_area = face, area
    return best


def main():
    shapes = [
        pgl.Segment(3, 3, 12, 7),
        pgl.Segment(1, 0, 15, 12),
        pgl.Line(pgl.Point(12, 2), pgl.Point(0, 12)),
        pgl.Segment(4, 15, 8, 3),
        pgl.Segment(0, 2, 13, 12),
        pgl.Line(pgl.Point(0, 2), pgl.Point(12, 0)),
        pgl.Segment(13, 9, 5, 9),
        pgl.Segment(4, 0, 9, 12),
    ]

    arrangement = pgl.Arrangement(shapes)

    canvas = pgl.Canvas()

    # Every edge of the subdivision, one entry per twin pair.
    canvas.stroke("#334155").strokeWidth("1.5px").fill("none")
    canvas.draw(arrangement.edges())

    # Every vertex: the endpoints together with every crossing.
    canvas.stroke("#1d4ed8").fill("#1d4ed8").pointRadius("4")
    canvas.draw(arrangement.vertices())

    face = largest_face(arrangement)

    # The pieces bounding the chosen face, on top and in another color.
    canvas.stroke("#e11d48").strokeWidth("3px").fill("none")
    canvas.draw(arrangement.halfedge(h) for h in arrangement.boundaryOf(face))

    canvas.writeSVG("example_arrangement.svg")

    print(f"{arrangement.vertexCount()} vertices, {arrangement.edgeCount()} edges, "
          f"{arrangement.faceCount()} faces (the unbounded one included)")
    print(f"highlighted face {face.index()}, of area "
          f"{float(arrangement.polygonWithHoles(face).area()):.3f}, bounded by "
          f"{len(arrangement.boundaryOf(face))} edges")
    print("wrote example_arrangement.svg")


if __name__ == "__main__":
    main()
