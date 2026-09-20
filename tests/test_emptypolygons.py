"""Empty triangles and quadrilaterals of a point set.

A polygon is *empty* with respect to a point set when its vertices belong to the
set and no other point of the set lies in the closed polygon -- a point on an
edge blocks it exactly as much as one inside. Only non-degenerate polygons
count, and a quadrilateral must be simple.

The differential tests below check every family against an independent
quadratic (resp. quartic) reference built on `Triangle.contains` /
`Polygon.contains`, which shares no code with the fan scan the library runs.
"""

import random
from itertools import combinations

import pytest

import pypgl
from pypgl import (
    Convex,
    OrientedSegment,
    Point,
    Polygon,
    Segment,
    Triangle,
    findEmptyConvexQuadrilaterals,
    findEmptyQuadrilaterals,
    findEmptyTriangles,
)


def keys(shapes):
    """A comparable key set. The shapes are mutable and so unhashable, but each
    canonicalizes its ring, so its repr identifies it up to rotation and
    reflection -- which is exactly the identity these functions report."""
    return {repr(s) for s in shapes}


# --- Independent references -------------------------------------------------


def brute_triangles(points):
    out = []
    for a, b, c in combinations(points, 3):
        t = Triangle(a, b, c)
        if t.twiceArea() == 0:  # three collinear points are no triangle
            continue
        if any(t.contains(p) for p in points if p not in (a, b, c)):
            continue
        out.append(t)
    return out


def brute_quadrilaterals(points, convex_only):
    out = {}
    for four in combinations(points, 4):
        a, b, c, d = four
        # The three distinct cyclic orders of four points; each is simple or
        # self-crossing, and several can be simple at once when one point lies
        # inside the triangle of the other three.
        for order in ((a, b, c, d), (a, b, d, c), (a, c, b, d)):
            p = Polygon(list(order))
            if p.size() != 4 or not p.isSimple():
                continue
            v = list(p.vertices())
            # Every vertex must be a proper corner, never a straight angle.
            if any(Triangle(v[i - 1], v[i], v[(i + 1) % 4]).twiceArea() == 0 for i in range(4)):
                continue
            if convex_only and not p.isConvex():
                continue
            if any(p.contains(q) for q in points if q not in four):
                continue
            result = Convex(list(order)) if convex_only else p
            out[repr(result)] = result
    return list(out.values())


def random_point_set(rng, n, span=6):
    # A small integer grid on purpose: it produces collinear triples, points on
    # edges and coincident points, which is where the degenerate rules bite.
    return list({Point(rng.randint(0, span), rng.randint(0, span)) for _ in range(n)})


# --- The three families against brute force ---------------------------------


@pytest.mark.parametrize("seed", range(12))
def test_every_family_matches_brute_force(seed):
    rng = random.Random(seed)
    points = random_point_set(rng, rng.randint(4, 7))
    assert keys(findEmptyTriangles(points)) == keys(brute_triangles(points))
    assert keys(findEmptyQuadrilaterals(points)) == keys(
        brute_quadrilaterals(points, convex_only=False)
    )
    assert keys(findEmptyConvexQuadrilaterals(points)) == keys(
        brute_quadrilaterals(points, convex_only=True)
    )


def test_the_result_types_are_the_tightest_ones():
    points = [Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4), Point(1, 1)]
    assert all(isinstance(t, Triangle) for t in findEmptyTriangles(points))
    # A quadrilateral may be non-convex, so it comes back as a Polygon; the
    # convex family is convex by construction and comes back as a Convex.
    assert all(isinstance(q, Polygon) for q in findEmptyQuadrilaterals(points))
    assert all(isinstance(q, Convex) for q in findEmptyConvexQuadrilaterals(points))


def test_the_convex_family_is_the_convex_part_of_the_other():
    points = [Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4), Point(1, 1)]
    quads = findEmptyQuadrilaterals(points)
    assert keys(findEmptyConvexQuadrilaterals(points)) == keys(
        Convex(list(q.vertices())) for q in quads if q.isConvex()
    )
    # One point inside the square blocks the square itself, leaving three
    # reflex quadrilaterals and one convex one.
    assert len(quads) == 4
    assert sum(1 for q in quads if q.isConvex()) == 1


# --- The vertex and edge forms ----------------------------------------------


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize(
    "find", [findEmptyTriangles, findEmptyQuadrilaterals, findEmptyConvexQuadrilaterals]
)
def test_the_vertex_form_is_the_full_one_filtered(seed, find):
    rng = random.Random(100 + seed)
    points = random_point_set(rng, 6)
    p = rng.choice(points)
    assert keys(find(points, p)) == keys(
        x for x in find(points) if any(v == p for v in x.vertices())
    )


def test_a_vertex_outside_the_set_is_treated_as_one_of_its_points():
    points = [Point(0, 0), Point(4, 0), Point(0, 4)]
    p = Point(4, 4)
    assert keys(findEmptyTriangles(points, p)) == keys(
        t for t in findEmptyTriangles(points + [p]) if any(v == p for v in t.vertices())
    )
    assert findEmptyTriangles(points, p)  # and it really does find some


def test_the_edge_form_of_the_triangles_is_the_full_one_filtered():
    points = [Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4), Point(1, 1)]
    a, b = Point(0, 0), Point(4, 0)
    assert keys(findEmptyTriangles(points, Segment(a, b))) == keys(
        t for t in findEmptyTriangles(points) if a in t.vertices() and b in t.vertices()
    )


def test_the_edge_form_of_the_quadrilaterals_wants_the_edge_as_an_inside_diagonal():
    points = [Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4), Point(1, 1)]
    a, b = Point(0, 0), Point(4, 4)
    got = findEmptyQuadrilaterals(points, Segment(a, b))
    want = [
        q
        for q in findEmptyQuadrilaterals(points)
        if a in q.vertices()
        and b in q.vertices()
        # A diagonal of the quadrilateral, not a side, and inside it: the
        # endpoints rest on the boundary and everything between them is strictly
        # within.
        and q.interiorContainsInterior(Segment(a, b))
    ]
    assert keys(got) == keys(want)


@pytest.mark.parametrize(
    "find", [findEmptyTriangles, findEmptyQuadrilaterals, findEmptyConvexQuadrilaterals]
)
def test_an_oriented_segment_is_the_same_edge(find):
    points = [Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4), Point(1, 3)]
    a, b = Point(0, 0), Point(4, 4)
    assert keys(find(points, Segment(a, b))) == keys(find(points, OrientedSegment(a, b)))
    # And the direction of the oriented one does not matter either.
    assert keys(find(points, OrientedSegment(a, b))) == keys(find(points, OrientedSegment(b, a)))


# --- Degenerate input -------------------------------------------------------


@pytest.mark.parametrize(
    "find", [findEmptyTriangles, findEmptyQuadrilaterals, findEmptyConvexQuadrilaterals]
)
def test_too_few_points_yield_nothing(find):
    assert find([]) == []
    assert find([Point(0, 0), Point(1, 1)]) == []


def test_collinear_points_make_no_empty_polygon():
    collinear = [Point(0, 0), Point(1, 1), Point(2, 2), Point(3, 3)]
    assert findEmptyTriangles(collinear) == []
    assert findEmptyQuadrilaterals(collinear) == []
    assert findEmptyConvexQuadrilaterals(collinear) == []


def test_the_points_are_read_as_a_set():
    triangle = [Point(0, 0), Point(2, 0), Point(0, 2)]
    # A coincident point counts once, so it neither adds a triangle nor blocks
    # the one that is there.
    assert keys(findEmptyTriangles(triangle + [Point(0, 0)])) == keys(
        findEmptyTriangles(triangle)
    )
    assert len(findEmptyTriangles(triangle)) == 1


def test_a_point_on_an_edge_blocks_the_polygon():
    # (1, 0) lies on the side from (0, 0) to (2, 0), which is as blocking as a
    # point strictly inside.
    assert findEmptyTriangles([Point(0, 0), Point(2, 0), Point(0, 2), Point(1, 0)]) != []
    assert Triangle(Point(0, 0), Point(2, 0), Point(0, 2)) not in findEmptyTriangles(
        [Point(0, 0), Point(2, 0), Point(0, 2), Point(1, 0)]
    )


def test_a_zero_length_edge_has_no_polygon():
    points = [Point(0, 0), Point(2, 0), Point(0, 2)]
    degenerate = Segment(Point(0, 0), Point(0, 0))
    assert findEmptyTriangles(points, degenerate) == []
    assert findEmptyQuadrilaterals(points, degenerate) == []
    assert findEmptyConvexQuadrilaterals(points, degenerate) == []


def test_a_point_inside_the_edge_blocks_every_polygon_through_it():
    points = [Point(0, 0), Point(1, 0), Point(2, 0), Point(0, 2), Point(2, 2)]
    blocked = Segment(Point(0, 0), Point(2, 0))  # (1, 0) sits inside it
    assert findEmptyTriangles(points, blocked) == []
    assert findEmptyQuadrilaterals(points, blocked) == []


def test_the_functions_are_public():
    for name in (
        "findEmptyTriangles",
        "findEmptyQuadrilaterals",
        "findEmptyConvexQuadrilaterals",
    ):
        assert name in pypgl.__all__
        assert hasattr(pypgl, name)
