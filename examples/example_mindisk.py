"""The smallest disk enclosing a set of points.

The Python port of pgl's `examples/example_mindisk.cpp`.

Welzl's randomized incremental algorithm, in expected linear time. The C++
example keeps every coordinate even, because an integral instantiation divides
by two when two points support the disk and would truncate; pypgl's coordinates
are exact rationals, so that caveat does not apply here and the center comes
back exact whatever the input.

Output: example_mindisk.svg
"""

import pypgl as pgl


def main():
    points = [
        pgl.Point(0, 2), pgl.Point(4, 12), pgl.Point(10, 4), pgl.Point(16, 14),
        pgl.Point(22, 6), pgl.Point(18, -2), pgl.Point(8, -4), pgl.Point(12, 8),
        pgl.Point(6, 2), pgl.Point(16, 4),
    ]

    disk = pgl.smallestEnclosingDisk(points)

    canvas = pgl.Canvas()

    # The disk first, so the points stay visible on top of its fill.
    canvas.stroke("#2563eb").fill("#93c5fd").fillOpacity("25%").draw(disk)

    canvas.stroke("#991b1b").fill("#dc2626").fillOpacity("100%")
    canvas.draw(points)

    canvas.writeSVG("example_mindisk.svg")

    print(f"center: {disk.center()}, squared radius: {disk.squaredRadius()}")
    print("wrote example_mindisk.svg")


if __name__ == "__main__":
    main()
