"""Finding the collinear points of a random point set through duality.

The Python port of pgl's `examples/example_dual_arrangement.cpp`.

The dual of a point (a, b) is the line y = a x - b, and the dual of a line
y = m x - c is the point (m, c). Duality preserves incidence: a point lies on a
line exactly when the dual line contains the dual point. So k points of the
plane are collinear exactly when their k dual lines meet at a single point, and
that point is the dual of the line through them.

Building the arrangement of the dual lines therefore turns "which points are
collinear?" into "which arrangement vertices have more than two lines through
them?". A vertex where k lines meet has 2k halfedges leaving it, so the
interesting vertices are the ones of degree greater than four; each one hands
back both the line (its own dual) and the points on it (the input lines that
produced the edges around it).

The one collinear family duality cannot see is a vertical one: the duals of
(k, y1) and (k, y2) are two lines of the same slope k, and parallel lines have
no crossing to find.

The input points are integral, but the dual lines cross at rational points, so
the arrangement keeps its vertices as exact rationals. Nothing here rounds.

Output: example_dual_arrangement_primal.svg, example_dual_arrangement_dual.svg
"""

import random
from typing import NamedTuple

import pypgl as pgl

# The points are drawn from the grid [-GRID_RADIUS, GRID_RADIUS]^2, centered on
# the origin, which is also the window of the primal drawing.
GRID_RADIUS = 3


class Collinear(NamedTuple):
    """One maximal set of collinear points, as read off a single arrangement vertex."""

    dual_vertex: pgl.Point  # Where the dual lines meet: (m, c).
    line: pgl.Line         # Its dual, the primal line y = m x - c.
    on_line: list          # Indices of the points lying on it.


def random_points(count, radius, seed=41):
    """Distinct random points on a small integer grid, where collinearities abound.

    The seed is chosen for the picture it draws: a handful of collinear
    families, one of them of four points.
    """
    rng = random.Random(seed)
    distinct = set()  # Shapes are values: usable in a set as they are.
    while len(distinct) < count:
        distinct.add(pgl.Point(rng.randint(-radius, radius), rng.randint(-radius, radius)))
    return sorted(distinct)


def collinear_families(arrangement):
    """The vertices of the arrangement where more than two dual lines meet."""
    families = []
    for i in range(arrangement.vertexCount()):
        vertex = pgl.VertexId(i)
        if arrangement.degree(vertex) <= 4:
            continue  # Two lines crossing: an ordinary vertex, nothing to report.

        # A vertex remembers which input shapes pass through it, and the input
        # shape of index i is the dual line of the point of index i.
        position = arrangement.position(vertex)
        families.append(Collinear(position, position.dual(), arrangement.originsOf(vertex)))
    return families


PALETTE = ["#e11d48", "#2563eb", "#16a34a", "#d97706",
           "#9333ea", "#0891b2", "#db2777", "#65a30d"]


def family_color(family):
    """One color per collinear family, reused by both drawings."""
    return PALETTE[family % len(PALETTE)]


def draw_primal(points, families):
    """The points themselves, with every collinear family in its own color."""
    canvas = pgl.Canvas().margin(40)
    # The grid the points came from, and nothing else.
    canvas.view(pgl.Rectangle(-GRID_RADIUS, -GRID_RADIUS, GRID_RADIUS, GRID_RADIUS))

    canvas.strokeWidth("1.5px").fill("none")
    for i, family in enumerate(families):
        canvas.stroke(family_color(i)).draw(family.line)

    canvas.stroke("#334155").fill("#334155").pointRadius("4")
    canvas.draw(points)

    # On top, the points of each family in the color of their line. A point on
    # two of the lines takes the color of the family drawn last.
    canvas.pointRadius("6")
    for i, family in enumerate(families):
        canvas.stroke(family_color(i)).fill(family_color(i))
        canvas.draw(points[index] for index in family.on_line)

    canvas.writeSVG("example_dual_arrangement_primal.svg")


def draw_dual(arrangement, families):
    """The arrangement of the dual lines.

    The concurrent vertices are colored to match the primal lines they are dual
    to.
    """
    canvas = pgl.Canvas().margin(40)
    # Two dual lines of nearly equal slope cross very far away, so fitting the
    # whole arrangement would leave the interesting middle unreadably small.
    canvas.view(pgl.Rectangle(-4, -4, 4, 4))

    canvas.stroke("#94a3b8").strokeWidth("1px").fill("none")
    canvas.draw(arrangement.edges())

    # Every crossing of two dual lines, that is, every line through two points.
    canvas.stroke("#334155").fill("#334155").pointRadius("3")
    canvas.draw(arrangement.vertices())

    # The ones where three or more dual lines meet.
    canvas.pointRadius("7")
    for i, family in enumerate(families):
        canvas.stroke(family_color(i)).fill(family_color(i)).draw(family.dual_vertex)

    canvas.writeSVG("example_dual_arrangement_dual.svg")


def main():
    points = random_points(12, GRID_RADIUS)

    arrangement = pgl.Arrangement([p.dual() for p in points])
    families = collinear_families(arrangement)

    draw_primal(points, families)
    draw_dual(arrangement, families)

    print(f"{len(points)} points, dual arrangement with {arrangement.vertexCount()} "
          f"vertices, {arrangement.edgeCount()} edges and {arrangement.faceCount()} faces")
    print(f"{len(families)} lines through more than two points:")
    for family in families:
        # The vertex (m, c) is the line y = m x - c, written here with its sign.
        slope, intercept = family.dual_vertex.x(), -family.dual_vertex.y()
        through = " ".join(str(points[index]) for index in family.on_line)
        sign = "-" if intercept < 0 else "+"
        print(f"  y = {slope} x {sign} {abs(intercept)} through {through}", end="")

        # A direct scan over the points confirms the dual's answer, and that the
        # family is maximal: no further point lies on the line.
        on_line = sum(1 for p in points if family.line.contains(p))
        print("  [confirmed]" if on_line == len(family.on_line) else "  [MISMATCH]")

    print("wrote example_dual_arrangement_primal.svg and example_dual_arrangement_dual.svg")


if __name__ == "__main__":
    main()
