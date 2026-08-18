"""Iterated midpoint polygon.

The Python port of pgl's `examples/example_convex.cpp`.

Starting from the convex hull of random points sampled inside a disk, this
repeatedly replaces the polygon by its "midpoint polygon" -- the convex hull of
the midpoints of the current polygon's edges -- and draws every iteration to an
SVG with cycling colors.

Each iteration shrinks toward the centroid of the original vertices (drawn as a
red dot), which is invariant under the midpoint map. After renormalizing, the
shape converges to an affine-regular polygon.

Every midpoint is an exact rational, so the coordinates stay exact however many
times the map is applied -- after a hundred iterations they are ratios of
enormous integers, and none of it rounds. That is the whole point of pypgl's
`Fraction` coordinates: in floating point this figure would collapse into noise
long before it converged.

Output: midpoint_polygon.svg
"""

import random

import pypgl as pgl

COLORS = [
    "crimson", "darkorange", "gold", "yellowgreen", "seagreen",
    "teal", "steelblue", "royalblue", "slateblue", "purple", "magenta",
]


def random_points_in_disk(n, r, seed=12345):
    """n random integer-coordinate points inside the disk of radius r at the origin."""
    rng = random.Random(seed)
    disk = pgl.Disk(pgl.Point(0, 0), r)
    points = []
    while len(points) < n:
        p = pgl.Point(rng.randint(-r, r), rng.randint(-r, r))
        if p in disk:  # `point in shape` is shape.contains(point)
            points.append(p)
    return points


def midpoint_polygon(convex):
    """The convex hull through the midpoints of the polygon's edges."""
    return pgl.Convex([edge.midpoint() for edge in convex.edges()])


def main():
    convex = pgl.Convex(random_points_in_disk(30, 100))
    center = convex.verticesCentroid()

    canvas = pgl.Canvas()

    for i in range(101):
        color = COLORS[i % len(COLORS)]
        canvas.stroke(color).fill(color).fillOpacity("10%").draw(convex)
        convex = midpoint_polygon(convex)

    canvas.stroke("white").fill("red").fillOpacity("100%").draw(center)

    canvas.writeSVG("midpoint_polygon.svg")


if __name__ == "__main__":
    main()
