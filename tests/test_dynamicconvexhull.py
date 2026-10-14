"""DynamicConvexHull: a set of points keeping its convex hull under updates.

Every hull query is checked against a static reference computed from scratch
(pgl.convexHull over the stored points), after random sequences of inserts and
erases on a small grid -- small on purpose, since that is what produces the
collinear runs, the repeated points and the one- and two-point hulls the
structure has to get right. The seven predicates are checked against the same
predicate on convexHull(), which is the contract, for one operand of every
kind of bound shape, compound and degenerate ones included.
"""

import random
from fractions import Fraction

import pytest

import pypgl as pgl
from pypgl import Point as P

PREDICATES = (
    "contains",
    "boundaryContains",
    "interiorContains",
    "intersects",
    "interiorsIntersect",
    "separates",
    "crosses",
)


def _lex(points):
    return sorted(points, key=lambda p: (p.x(), p.y()))


def _reference_vertices(points):
    """The strictly convex hull, counterclockwise from the lexicographically
    smallest point -- how both Convex and DynamicConvexHull number vertices."""
    if not points:
        return []
    return list(pgl.Convex(list(points)).vertices())


def _check_hull(hull, stored):
    assert len(hull) == hull.size() == len(stored)
    assert hull.empty() == (not stored)
    assert list(hull) == _lex(stored)

    expected = _reference_vertices(stored)
    assert hull.vertices() == expected
    assert hull.hullSize() == len(expected)
    assert hull.convexHull() == pgl.Convex(list(stored))
    for i, v in enumerate(expected):
        assert hull.vertex(i) == v
        assert hull.vertex(i - len(expected)) == v
        assert hull.index(v) == i
        assert hull.verticesContain(v)
    for p in stored:
        assert p in hull and hull.has(p)
        if p not in expected:
            assert hull.index(p) is None
            assert not hull.verticesContain(p)

    if stored:
        lower, upper = hull.lowerHull(), hull.upperHull()
        convex = hull.convexHull()
        assert lower.vertices() == list(convex.lowerHull().vertices())
        assert upper.vertices() == list(convex.upperHull().vertices())

        xs = [p.x() for p in stored]
        ys = [p.y() for p in stored]
        assert hull.bbox() == pgl.Rectangle(P(min(xs), min(ys)), P(max(xs), max(ys)))

        for d in (P(1, 0), P(-1, 0), P(0, 1), P(0, -1), P(1, 1), P(-2, 1), P(3, -5), P(-1, -1)):
            best = max(d.x() * p.x() + d.y() * p.y() for p in stored)
            ties = _lex(p for p in expected if d.x() * p.x() + d.y() * p.y() == best)
            assert hull.extremeVertex(d) == ties[0]


@pytest.mark.parametrize("seed", range(40))
def test_random_updates_match_a_static_hull(seed):
    rng = random.Random(seed)
    span = rng.choice([2, 4, 8])
    hull = pgl.DynamicConvexHull()
    stored = set()
    for _ in range(80):
        p = P(rng.randint(0, span), rng.randint(0, span))
        if rng.random() < 0.6:
            assert hull.insert(p) == (p not in stored)
            stored.add(p)
        else:
            assert hull.erase(p) == (p in stored)
            stored.discard(p)
        _check_hull(hull, stored)


def test_collinear_points_keep_only_the_two_extremes():
    points = [P(i, 2 * i) for i in range(6)]
    hull = pgl.DynamicConvexHull(points)
    assert hull.vertices() == [P(0, 0), P(5, 10)]
    assert hull.hullSize() == 2
    hull.insert(P(1, 0))
    assert hull.vertices() == [P(0, 0), P(1, 0), P(5, 10)]


def test_repeated_points_are_stored_once():
    hull = pgl.DynamicConvexHull([P(1, 1), P(1, 1), P(0, 0)])
    assert len(hull) == 2
    assert not hull.insert(P(0, 0))
    assert hull.erase(P(1, 1))
    assert not hull.erase(P(1, 1))
    assert list(hull) == [P(0, 0)]


def test_exact_rational_coordinates():
    third = Fraction(1, 3)
    hull = pgl.DynamicConvexHull([P(0, 0), P(1, 0), P(third, third), P(third, 1)])
    assert hull.vertices() == [P(0, 0), P(1, 0), P(third, 1)]
    assert hull.contains(P(third, third))
    assert not hull.boundaryContains(P(third, third))


def test_membership_is_not_containment():
    # `in` asks whether the point is stored, as for every container; contains
    # asks whether it lies in the hull.
    hull = pgl.DynamicConvexHull([P(0, 0), P(4, 0), P(0, 4)])
    assert P(1, 1) not in hull and hull.contains(P(1, 1))
    assert P(4, 0) in hull


def test_copy_is_independent():
    hull = pgl.DynamicConvexHull([P(0, 0), P(4, 0), P(0, 4)])
    copy = pgl.DynamicConvexHull(hull)
    copy.insert(P(4, 4))
    assert len(hull) == 3 and len(copy) == 4
    assert hull.hullSize() == 3 and copy.hullSize() == 4


def test_clear():
    hull = pgl.DynamicConvexHull([P(0, 0), P(4, 0), P(0, 4)])
    hull.clear()
    assert hull.empty() and list(hull) == [] and hull.vertices() == []
    assert hull.insert(P(1, 1))
    assert hull.vertices() == [P(1, 1)]


def test_mutating_while_iterating_is_safe():
    # Iteration walks a snapshot, so the peeling idiom -- erase what you are
    # iterating -- neither skips points nor reads recycled storage.
    points = [P(x, y) for x in range(5) for y in range(5)]
    hull = pgl.DynamicConvexHull(points)
    seen = []
    for p in hull:
        seen.append(p)
        hull.erase(p)
    assert seen == _lex(points) and hull.empty()

    hull = pgl.DynamicConvexHull(points)
    for _ in hull:
        hull.clear()
        hull.insert(P(9, 9))
    assert list(hull) == [P(9, 9)]


def test_peeling_gives_the_hull_of_what_is_left():
    rng = random.Random(7)
    points = {P(rng.randint(-20, 20), rng.randint(-20, 20)) for _ in range(120)}
    hull = pgl.DynamicConvexHull(list(points))
    remaining = set(points)
    layers = 0
    while not hull.empty():
        layer = hull.vertices()
        assert layer == _reference_vertices(remaining)
        for v in layer:
            assert hull.erase(v)
            remaining.discard(v)
        assert list(hull) == _lex(remaining)
        layers += 1
    assert not remaining and layers > 3


def test_empty_set():
    hull = pgl.DynamicConvexHull()
    assert hull.empty() and hull.hullSize() == 0 and hull.vertices() == []
    assert hull.convexHull() == pgl.Convex()
    assert hull.index(P(0, 0)) is None and not hull.verticesContain(P(0, 0))
    assert not hull.has(P(0, 0)) and not hull.erase(P(0, 0))
    with pytest.raises(IndexError):
        hull.vertex(0)
    with pytest.raises(pgl.PreconditionError):
        hull.bbox()
    with pytest.raises(pgl.PreconditionError):
        hull.extremeVertex(P(1, 0))


def test_zero_direction_is_refused():
    hull = pgl.DynamicConvexHull([P(0, 0), P(1, 0)])
    with pytest.raises(pgl.PreconditionError):
        hull.extremeVertex(P(0, 0))


def test_repr():
    hull = pgl.DynamicConvexHull([P(0, 0), P(4, 0), P(0, 4), P(1, 1)])
    assert repr(hull) == "DynamicConvexHull(size=4, hullSize=3)"


def test_canvas_draws_the_hull_and_then_the_points():
    points = [P(0, 0), P(4, 0), P(0, 4), P(1, 1)]
    hull = pgl.DynamicConvexHull(points)
    expected = pgl.Canvas().draw(pgl.Convex(points)).draw(_lex(points)).toSVG()
    assert pgl.Canvas().draw(hull).toSVG() == expected
    assert pgl.Canvas().draw(pgl.DynamicConvexHull()).toSVG() == pgl.Canvas().toSVG()
    assert "<svg" in hull._repr_svg_()


# --- the seven predicates, against the same predicate on convexHull() -------

def _operands(rng, span):
    """One shape of every bound kind, on a grid of half units. Each operand
    draws its corners from a window chosen at random -- around the hull,
    within it, or a single small cell -- so that across the battery every
    predicate meets both answers wherever both are possible (a bounded hull
    never contains a line, and nothing separates a point)."""
    half = Fraction(1, 2)

    def window():
        lo = rng.randint(0, span - 1)
        return rng.choice([(-1, span + 1), (0, span), (1, span - 1), (lo, lo + 1)])

    def pt(w):
        a, b = w
        return P(rng.randint(2 * a, 2 * b) * half, rng.randint(2 * a, 2 * b) * half)

    def two(w):
        a = pt(w)
        b = pt(w)
        while b == a:
            b = pt(w)
        return a, b

    def tri(w):
        while True:
            t = pgl.Triangle(pt(w), pt(w), pt(w))
            if not t.isDegenerate():
                return t

    def box(w):
        a, b = two(w)
        return pgl.Rectangle(P(min(a.x(), b.x()), min(a.y(), b.y())),
                             P(max(a.x(), b.x()), max(a.y(), b.y())))

    def solid_box(w):
        while True:
            r = box(w)
            if r.area() > 0:
                return r

    def ell(w):
        corner, size = pt(w), rng.choice([half, 1, 2])
        ring = [(0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (0, 2)]
        return pgl.Polygon([P(corner.x() + x * size, corner.y() + y * size) for x, y in ring])

    def region(w):
        outer = solid_box(w)
        if outer.width() >= 2 and outer.height() >= 2:
            lo = outer.min()
            hole = pgl.Rectangle(P(lo.x() + half, lo.y() + half), P(lo.x() + 1, lo.y() + 1))
            return pgl.PolygonWithHoles(outer.asPolygon(), [hole.asPolygon()])
        return outer.asPolygonWithHoles()

    w = [window() for _ in range(17)]
    convex = pgl.Convex([pt(w[9]) for _ in range(rng.choice([2, 3, 6]))])
    return [
        pt(w[0]),
        pgl.Segment(*two(w[1])),
        pgl.OrientedSegment(*two(w[2])),
        pgl.Line(*two(w[3])),
        pgl.OrientedLine(*two(w[4])),
        pgl.Ray(*two(w[5])),
        pgl.Halfplane(*two(w[6])),
        tri(w[7]),
        box(w[8]),
        convex,
        pgl.MonotoneChain([pt(w[10]) for _ in range(rng.choice([2, 4]))]),
        pgl.Polyline([pt(w[11]) for _ in range(rng.choice([2, 4]))]),
        ell(w[12]),
        region(w[13]),
        solid_box(w[14]).regularizedUnion(solid_box(w[14])),
        pgl.HalfplaneIntersection([pgl.Halfplane(*two(w[15])) for _ in range(rng.choice([1, 3, 4]))]),
        pgl.Disk(pt(w[16]), rng.choice([0, half, 1, 2])),
    ]


def test_operand_battery_covers_every_shape():
    kinds = {type(s).__name__ for s in _operands(random.Random(0), 4)}
    assert len(kinds) == 17


# (predicate, operand kind) pairs with only one possible answer: a bounded
# hull contains nothing unbounded, its boundary holds nothing with area and
# nothing unbounded, and nothing separates or crosses a point or a half-plane.
# Every other pair must see both answers, or the comparison proves nothing.
_ONE_SIDED = {
    *(("contains", k) for k in ("Line", "OrientedLine", "Ray", "Halfplane")),
    *(("interiorContains", k) for k in ("Line", "OrientedLine", "Ray", "Halfplane")),
    *(("boundaryContains", k) for k in ("Line", "OrientedLine", "Ray", "Halfplane", "Triangle",
                                         "Polygon", "PolygonWithHoles", "PolygonSet")),
    ("separates", "Point"), ("crosses", "Point"),
    ("separates", "Halfplane"), ("crosses", "Halfplane"),
}


def test_predicates_answer_as_on_the_static_hull():
    outcomes = {}
    for seed in range(25):
        rng = random.Random(1000 + seed)
        span = 4
        hull = pgl.DynamicConvexHull()
        stored = set()
        # Grow from empty through one, two and collinear points to a full
        # hull, with erases mixed in, testing every state on the way.
        for step in range(30):
            p = P(rng.randint(0, span), rng.randint(0, span))
            if step < 3 or rng.random() < 0.7:
                hull.insert(p)
                stored.add(p)
            else:
                hull.erase(p)
                stored.discard(p)
            reference = hull.convexHull()
            for other in _operands(rng, span):
                for name in PREDICATES:
                    got = getattr(hull, name)(other)
                    assert got == getattr(reference, name)(other), (name, sorted(stored, key=str), other)
                    outcomes.setdefault((name, type(other).__name__), set()).add(got)
    assert len(outcomes) == 17 * len(PREDICATES)
    assert {k for k, v in outcomes.items() if len(v) < 2} <= _ONE_SIDED


@pytest.mark.parametrize("points", [
    [],
    [P(2, 2)],
    [P(0, 0), P(3, 3)],
    [P(0, 0), P(1, 1), P(2, 2), P(3, 3)],
    [P(0, 1), P(4, 1)],
], ids=["empty", "point", "segment", "collinear", "horizontal"])
def test_predicates_on_degenerate_hulls(points):
    hull = pgl.DynamicConvexHull(points)
    reference = hull.convexHull()
    rng = random.Random(len(points))
    for _ in range(15):
        for other in _operands(rng, 4):
            for name in PREDICATES:
                assert getattr(hull, name)(other) == getattr(reference, name)(other), (name, other)
