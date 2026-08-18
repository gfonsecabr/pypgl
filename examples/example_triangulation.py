"""Triangulation: the Delaunay triangulation of a point set, and directed walks.

The Python port of pgl's `examples/example_triangulation.cpp`.

A segment is walked across the triangulation twice: `trianglesIntersecting`
takes every triangle it touches, `trianglesInteriorIntersecting` only those it
passes through the inside of. The difference is the triangles the segment merely
grazes along an edge or at a vertex.

Output: example_triangulation.svg
"""

import random

import pypgl as pgl


def random_points(count, max_coord, seed=1):
    rng = random.Random(seed)
    return [
        pgl.Point(rng.randint(0, max_coord), rng.randint(0, max_coord))
        for _ in range(count)
    ]


def draw(filename, triangulation, query, interior_hits, hits):
    canvas = pgl.Canvas()

    # Drawing the triangulation itself draws its mesh.
    canvas.stroke("#2f9aff").strokeWidth("1").fill("#000000").fillOpacity("0.2")
    canvas.draw(triangulation)

    canvas.stroke("#10b305").fill("#10b305").fillOpacity(".5")
    canvas.draw(triangulation.triangles())

    canvas.stroke("#ff0000").fill("#ff0000").fillOpacity(".5")
    canvas.draw(interior_hits)

    canvas.stroke("#ffff00").fill("#ffff00").fillOpacity(".3")
    canvas.draw(hits)

    canvas.stroke("#1100ff").fill("#1100ff").fillOpacity(".5")
    canvas.draw(query)

    canvas.writeSVG(filename)


def main():
    # 100 random points in a 100x100 box.
    triangulation = pgl.Triangulation(random_points(100, 100))  # Delaunay

    query = pgl.OrientedSegment(10, 20, 80, 90)
    draw(
        "example_triangulation.svg",
        triangulation,
        query,
        triangulation.trianglesInteriorIntersecting(query),
        triangulation.trianglesIntersecting(query),
    )


if __name__ == "__main__":
    main()
