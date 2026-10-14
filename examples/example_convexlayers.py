"""Convex layers (onion peeling) of a set of points.

The Python port of pgl's `examples/example_convexlayers.cpp`.

The points go into a DynamicConvexHull. The first layer is the convex hull;
erasing its vertices exposes the next one, and so on until the set is empty.
Each erase takes O(log^2 n) time, so peeling every layer of n points takes
O(n log^2 n) time in total.

The hull is strictly convex, so a point in the middle of a hull edge is not one
of its vertices and is peeled with a later layer.

Output: example_convexlayers.svg
"""

import random

import pypgl as pgl

COLORS = [
    "crimson", "darkorange", "gold", "yellowgreen", "seagreen",
    "teal", "steelblue", "royalblue", "slateblue", "purple", "magenta",
]


def random_points_in_disk(n, r, seed=2026):
    """n random integer-coordinate points inside the disk of radius r at the origin."""
    rng = random.Random(seed)
    disk = pgl.Disk(pgl.Point(0, 0), r)
    points = []
    while len(points) < n:
        p = pgl.Point(rng.randint(-r, r), rng.randint(-r, r))
        if p in disk:  # `point in shape` is shape.contains(point)
            points.append(p)
    return points


def main():
    points = random_points_in_disk(150, 100)
    hull = pgl.DynamicConvexHull(points)

    layers = []
    while not hull.empty():
        layers.append(hull.convexHull())
        for p in hull.vertices():
            hull.erase(p)

    canvas = pgl.Canvas()
    for i, layer in enumerate(layers):
        color = COLORS[i % len(COLORS)]
        canvas.stroke(color).fill(color).fillOpacity("8%").draw(layer)

    canvas.stroke("white").fill("black").fillOpacity("100%").draw(points)

    canvas.writeSVG("example_convexlayers.svg")

    print(f"{len(points)} points, {len(layers)} convex layers")
    print("wrote example_convexlayers.svg")


if __name__ == "__main__":
    main()
