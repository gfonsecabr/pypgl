"""The Minkowski sum of a non-convex polygon and a convex one.

The Python port of pgl's `examples/example_minkowskisum.cpp`.

The sum A (+) B is the set of all sums of a point of A and a point of B. When
the origin lies inside B, every translate A + b covers a copy of A, so the sum
grows A outward and the picture is the union of one translated copy of B per
point of A. It is enough to place a copy at each *vertex*: the sum's boundary is
swept by those copies, and every other translate lands inside their union
together with A itself.

Output: example_minkowskisum.svg
"""

import pypgl as pgl


def main():
    polygon = pgl.Polygon([
        0, 0, 100, 0, 100, 45, 75, 45, 75, 25, 25, 25, 25, 75, 75, 75, 100, 100, 0, 100,
    ])
    convex = pgl.Convex([8, 0, 4, 7, -4, 7, -8, 0, -4, -7, 4, -7])

    # One operand is a body, so the answer is guaranteed connected and comes
    # back as a single PolygonWithHoles rather than as a set of regions.
    summed = polygon.minkowskiSum(convex)

    print(f"polygon area {float(polygon.area()):.1f}, "
          f"sum area {float(summed.area()):.1f}, "
          f"holes in the sum: {summed.holeCount()}")

    canvas = pgl.Canvas()

    # The sum underneath, as a pale filled region.
    canvas.stroke("#1d4ed8").strokeWidth("1.5").fill("#93c5fd").fillOpacity("0.35")
    canvas.draw(summed)

    # One copy of the convex per polygon vertex; together they sweep out the
    # difference between the polygon and the sum.
    canvas.stroke("#375cc4").strokeWidth("0.5").fill("#77a1d1").fillOpacity("0.35")
    canvas.draw(convex + vertex for vertex in polygon.vertices())

    # The polygon itself on top.
    canvas.stroke("#111827").strokeWidth("1.5").fill("#6b7280").fillOpacity("0.5")
    canvas.draw(polygon)

    canvas.writeSVG("example_minkowskisum.svg")
    print("wrote example_minkowskisum.svg")


if __name__ == "__main__":
    main()
