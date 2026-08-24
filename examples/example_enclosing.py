"""The smallest disk and the smallest-area rectangle enclosing a point set.

The Python port of pgl's `examples/example_enclosing.cpp`.

The disk comes from Welzl's randomized incremental algorithm, in expected
linear time. The rectangle is tilted and its corners are fractional, but its
four supporting lines are not, which is why `smallestEnclosingRectangle`
returns a `HalfplaneIntersection` rather than a `Rectangle`: a `Rectangle` is
axis-aligned by definition, and the smallest-area one is generally not. It
reads a convex boundary, so it lives on `Convex`; every other shape reaches it
through its own `convexHull()`.

Both stay exact here. Coordinates are exact rationals, so halving one to place
a disk center between two points never truncates, and a fractional corner is
carried rather than rounded.

Output: example_enclosing.svg
"""

import pypgl as pgl


def main():
    points = [
        pgl.Point(0, 2), pgl.Point(4, 12), pgl.Point(10, 4), pgl.Point(16, 14),
        pgl.Point(18, 10), pgl.Point(18, 8), pgl.Point(18, -2), pgl.Point(8, -4),
        pgl.Point(12, 8), pgl.Point(6, 2), pgl.Point(16, 4), pgl.Point(14, 12),
    ]

    disk = pgl.smallestEnclosingDisk(points)
    hull = pgl.Convex(points)
    rect = hull.smallestEnclosingRectangle()

    canvas = pgl.Canvas()

    # Both enclosing shapes first, so the points stay visible on top of them.
    canvas.stroke("#2563eb").fill("#93c5fd").fillOpacity("25%").draw(disk)

    # A region is drawn together with the points defining its boundary lines,
    # which for this one lie outside it.
    canvas.stroke("#2dc535").fill("#95fd93").fillOpacity("25%").draw(rect)

    canvas.stroke("#991b1b").fill("#dc2626").fillOpacity("100%")
    canvas.draw(points)

    canvas.writeSVG("example_enclosing.svg")

    print(f"center: {disk.center()}, squared radius: {disk.squaredRadius()}")
    print(f"rectangle: {rect}")
    print(f"its corners: {rect.asConvex()}")
    print("wrote example_enclosing.svg")


if __name__ == "__main__":
    main()
