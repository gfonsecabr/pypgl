"""ShapeTree: a static spatial index, and its region queries.

The Python port of pgl's `examples/example_shapetree.cpp`.

Two trees are built and queried against the same triangle: one over 100 random
points, one over 100 random small triangles. The tree's own node boxes are drawn
underneath, so the subdivision it prunes with is visible.

Output: example_shapetree_points.svg, example_shapetree_triangles.svg
"""

import random

import pypgl as pgl


def random_points(count, max_coord, seed=1):
    rng = random.Random(seed)
    return [
        pgl.Point(rng.randint(0, max_coord), rng.randint(0, max_coord))
        for _ in range(count)
    ]


def random_triangles(count, max_coord, size, seed=5):
    rng = random.Random(seed)
    triangles = []
    while len(triangles) < count:
        x = rng.randint(0, max_coord)
        y = rng.randint(0, max_coord)
        corners = [
            pgl.Point(x + rng.randint(-size, size), y + rng.randint(-size, size))
            for _ in range(3)
        ]
        triangle = pgl.Triangle(*corners)
        if not triangle.isDegenerate():
            triangles.append(triangle)
    return triangles


def draw(filename, tree, query, contained, intersecting=()):
    canvas = pgl.Canvas()

    # The tree's node boxes, lightly filled -- drawing the tree itself draws its
    # subdivision rather than its elements.
    canvas.stroke("#2f9aff").strokeWidth("1").fill("#000000").fillOpacity("0.2")
    canvas.draw(tree)

    canvas.stroke("#1100ff").fill("#1100ff").fillOpacity(".5")
    canvas.draw(query)

    # Drawing a collection draws its elements one by one, and iterating a
    # ShapeTree yields the shapes it stores.
    canvas.stroke("#10b305").fill("#10b305").fillOpacity(".5")
    canvas.draw(tree.shapes())

    canvas.stroke("#ff0000").fill("#ff0000").fillOpacity(".5")
    canvas.draw(contained)

    canvas.stroke("#ffff00").fill("#ffff00").fillOpacity(".3")
    canvas.draw(intersecting)

    canvas.writeSVG(filename)


def main():
    query = pgl.Triangle(200, 200, 600, 800, 900, 250)

    # 100 random points in a 1000x1000 box.
    tree = pgl.ShapeTree(random_points(100, 1000), 3)
    draw("example_shapetree_points.svg", tree, query, tree.reportContainedIn(query))

    # 100 random triangles of size up to 50 in the same box. Here the two
    # queries differ: a triangle can meet the query without being inside it.
    tree = pgl.ShapeTree(random_triangles(100, 1000, 50), 3)
    draw(
        "example_shapetree_triangles.svg",
        tree,
        query,
        tree.reportContainedIn(query),
        tree.reportIntersecting(query),
    )


if __name__ == "__main__":
    main()
