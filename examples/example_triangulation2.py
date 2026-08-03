"""Constrained Delaunay triangulation of a spiral polygon.

The Python port of pgl's `examples/example_triangulation2.cpp`.

The domain is a corridor of constant width winding around the origin. Because
the triangulation is *constrained*, no triangle crosses a wall of the corridor,
so the mesh follows the spiral around instead of cutting across it -- which an
unconstrained Delaunay triangulation of the same vertices would do.

The spiral is laid out with floating-point trigonometry and then rounded to
integer vertices, since pypgl coordinates are exact and reject `float`. Once
built, everything downstream is exact.

Output: example_triangulation2.svg
"""

import math
import random

import pypgl as pgl


def make_spiral(r0, k, width, turns, steps_per_turn):
    """A simple spiral polygon: a corridor of constant width, `turns` times round.

    The boundary runs outward along the inner wall (radius r0 + k*theta) and back
    along the outer wall (the same plus `width`), so it never self-intersects as
    long as width < pitch (= 2*pi*k).
    """
    theta_max = turns * 2.0 * math.pi
    steps = turns * steps_per_turn
    vertices = []

    def add(t, extra):
        r = r0 + k * t + extra
        # round() before Point(): pypgl rejects float coordinates outright rather
        # than silently approximating them.
        p = pgl.Point(round(r * math.cos(t)), round(r * math.sin(t)))
        # Skip repeated integer vertices so no edge collapses to zero length.
        if not vertices or vertices[-1] != p:
            vertices.append(p)

    for i in range(steps + 1):          # outward along the inner wall
        add(theta_max * i / steps, 0.0)
    for i in range(steps, -1, -1):      # back along the outer wall
        add(theta_max * i / steps, width)

    return pgl.Polygon(vertices)


def random_points_inside(polygon, count, max_coord, seed=1):
    rng = random.Random(seed)
    points = []
    while len(points) < count:
        p = pgl.Point(
            rng.randint(-max_coord, max_coord), rng.randint(-max_coord, max_coord)
        )
        if polygon.interiorContains(p):
            points.append(p)
    return points


def draw(filename, triangulation, query, interior_hits, hits):
    canvas = pgl.Canvas()

    canvas.stroke("#2f9aff").strokeWidth("1").fill("#000000").fillOpacity("0.2")
    canvas.draw(triangulation)

    canvas.stroke("#10b305").fill("#10b305").fillOpacity(".5")
    for triangle in triangulation.triangles():
        canvas.draw(triangle)

    canvas.stroke("#ff0000").fill("#ff0000").fillOpacity(".5")
    for triangle in interior_hits:
        canvas.draw(triangle)

    canvas.stroke("#ffff00").fill("#ffff00").fillOpacity(".3")
    for triangle in hits:
        canvas.draw(triangle)

    canvas.stroke("#1100ff").fill("#1100ff").fillOpacity(".5")
    canvas.draw(query)

    canvas.writeSVG(filename)


def main():
    spiral = make_spiral(12.0, 3.5, 15.0, turns=3, steps_per_turn=40)
    if not spiral.isSimple():
        raise RuntimeError("Polygon is not simple")

    points = random_points_inside(spiral, 100, 100)
    # Constrained Delaunay: the polygon's edges are constrained, and nothing
    # outside it is triangulated.
    triangulation = pgl.Triangulation(spiral, points)

    query = pgl.Convex(
        [pgl.Point(-47, -36), pgl.Point(53, 64), pgl.Point(53, -36), pgl.Point(27, -74)]
    )
    draw(
        "example_triangulation2.svg",
        triangulation,
        query,
        triangulation.trianglesInteriorIntersecting(query),
        triangulation.trianglesIntersecting(query),
    )


if __name__ == "__main__":
    main()
