"""MonotoneChain and Polyline: the two open polygonal chains.

Both mirror Convex/Polygon's storage (vertices plus a lazy translation) and are
mutable, hence unhashable. They differ in what the vertex sequence means -- a
MonotoneChain sorts its input as a *point set*, a Polyline keeps it in traversal
order -- and that difference drives what each one can do (see src/bind_chains.cpp).
"""

from fractions import Fraction

import pytest

from pypgl import (
    Convex,
    Disk,
    Line,
    MonotoneChain,
    Point,
    Polygon,
    Polyline,
    Rectangle,
    Ray,
    Segment,
    Transformation,
    Triangle,
)


# --- MonotoneChain -----------------------------------------------------------


def test_chain_sorts_its_input_as_a_point_set():
    # The input is a set, not a pre-linked chain: any order gives the same chain.
    a = MonotoneChain([Point(2, 2), Point(0, 0), Point(1, 3)])
    b = MonotoneChain([Point(1, 3), Point(2, 2), Point(0, 0)])
    assert a == b
    assert a.vertices() == [Point(0, 0), Point(1, 3), Point(2, 2)]
    # Duplicates are dropped.
    assert MonotoneChain([Point(0, 0), Point(0, 0), Point(1, 1)]).size() == 2


def test_chain_has_n_minus_1_edges_and_no_closing_edge():
    c = MonotoneChain([Point(0, 0), Point(1, 3), Point(2, 2)])
    assert c.edges() == [
        Segment(Point(0, 0), Point(1, 3)),
        Segment(Point(1, 3), Point(2, 2)),
    ]
    assert len(c.orientedEdges()) == 2
    assert MonotoneChain([Point(0, 0)]).edges() == []


def test_chain_is_weakly_monotone_when_it_has_a_vertical_edge():
    assert MonotoneChain([Point(0, 0), Point(1, 1), Point(2, 0)]).isStrictlyMonotone()
    # Two vertices sharing an x: a vertical edge, so only weakly monotone.
    assert not MonotoneChain([Point(0, 0), Point(1, 1), Point(1, 5)]).isStrictlyMonotone()


def test_chain_vertical_queries():
    c = MonotoneChain([Point(0, 0), Point(2, 2)])
    assert c.indexAtX(1) == 0
    assert c.yAtX(1) == 1
    assert c.yAtX(Fraction(1, 2)) == Fraction(1, 2)
    # Outside the x-extent there is no chain to evaluate.
    assert c.yAtX(5) is None
    assert c.indexAtX(5) is None


def test_chain_below_above_are_weak_and_strict_variants():
    c = MonotoneChain([Point(0, 0), Point(2, 2)])
    above, below, on = Point(1, 5), Point(1, -5), Point(1, 1)

    # Chain strictly below `above`: a downward ray from `above` hits it.
    assert c.isStrictlyBelow(above) is not None
    assert c.isBelow(above) is not None
    assert c.isStrictlyAbove(above) is None

    assert c.isStrictlyAbove(below) is not None
    assert c.isAbove(below) is not None

    # A point *on* the chain is neither strictly below nor strictly above it,
    # but satisfies both weak forms.
    assert c.isStrictlyBelow(on) is None
    assert c.isStrictlyAbove(on) is None
    assert c.isBelow(on) is not None
    assert c.isAbove(on) is not None

    # Outside the x-extent every query is empty.
    assert c.isBelow(Point(9, 0)) is None
    assert c.isStrictlyAbove(Point(9, 0)) is None


def test_chain_insert_keeps_it_sorted():
    c = MonotoneChain([Point(0, 0), Point(2, 2)])
    c.insert(Point(1, 5))
    assert c.vertices() == [Point(0, 0), Point(1, 5), Point(2, 2)]
    c.insert([Point(3, 0), Point(-1, 1)])
    assert c.vertices()[0] == Point(-1, 1)
    assert c.vertices()[-1] == Point(3, 0)
    # A duplicate vertex is ignored.
    before = c.size()
    c.insert(Point(0, 0))
    assert c.size() == before


# --- Polyline ----------------------------------------------------------------


def test_polyline_keeps_traversal_order():
    p = Polyline([Point(0, 0), Point(2, 2), Point(1, 0)])
    assert p.vertices() == [Point(0, 0), Point(2, 2), Point(1, 0)]
    # Only the direction is canonicalized, so a polyline equals its reverse.
    assert p == Polyline([Point(1, 0), Point(2, 2), Point(0, 0)])
    # ...but not a different traversal of the same vertex set.
    assert p != Polyline([Point(0, 0), Point(1, 0), Point(2, 2)])


def test_polyline_may_self_intersect():
    simple = Polyline([Point(0, 0), Point(1, 1), Point(3, 0)])
    assert simple.isSimple()
    # An X-shaped chain crosses itself.
    crossing = Polyline([Point(0, 0), Point(2, 2), Point(2, 0), Point(0, 2)])
    assert not crossing.isSimple()
    # A closed polyline (last vertex == first) is not simple either.
    assert not Polyline([Point(0, 0), Point(2, 0), Point(1, 2), Point(0, 0)]).isSimple()


def test_polyline_edges_and_lengths():
    p = Polyline([Point(0, 0), Point(3, 4), Point(3, 5)])
    assert p.edges() == [
        Segment(Point(0, 0), Point(3, 4)),
        Segment(Point(3, 4), Point(3, 5)),
    ]
    assert p.length() == pytest.approx(6.0)  # 5 + 1
    assert p.lengthL1() == 8  # (3 + 4) + (0 + 1), exact
    assert p.lengthLInf() == 5  # max(3, 4) + max(0, 1), exact


# --- Shared behavior ---------------------------------------------------------


@pytest.mark.parametrize("make", [MonotoneChain, Polyline])
def test_chains_are_mutable_and_therefore_unhashable(make):
    c = make([Point(0, 0), Point(2, 2)])
    with pytest.raises(TypeError):
        hash(c)

    # In-place translation mutates and keeps the same object (pgl's O(1) translate).
    same = c
    c += Point(10, 0)
    assert same is c
    assert c.vertices()[0] == Point(10, 0)

    # The value-returning form leaves the original alone.
    moved = c - Point(10, 0)
    assert moved.vertices()[0] == Point(0, 0)
    assert c.vertices()[0] == Point(10, 0)


@pytest.mark.parametrize("make", [MonotoneChain, Polyline])
def test_chains_are_indexable_and_iterable_over_their_vertices(make):
    c = make([Point(0, 0), Point(1, 1), Point(2, 0)])
    assert len(c) == 3
    assert c[0] == Point(0, 0)
    assert c[-1] == Point(2, 0)  # cyclic indexing, like every other shape
    assert list(c) == c.vertices()
    assert Point(1, 1) in c  # point-in-shape sugar
    assert Point(9, 9) not in c
    assert c.index(Point(1, 1)) == 1
    assert c.index(Point(9, 9)) is None


@pytest.mark.parametrize("make", [MonotoneChain, Polyline])
def test_chains_have_the_full_predicate_matrix(make):
    c = make([Point(0, 0), Point(2, 2)])
    tri = Triangle(Point(0, 0), Point(4, 0), Point(0, 4))
    assert c.intersects(tri)
    assert tri.contains(c)  # the reverse row exists too
    assert not c.contains(tri)
    assert c.intersects(Rectangle(Point(0, 0), Point(1, 1)))
    assert not c.intersects(Disk(Point(20, 20), 1))
    # Mutual separation: the line cuts the chain in two at (1, 1), and that point
    # cuts the line in two. A line through the chain's *endpoint* (2, 2) would
    # not -- removing a boundary point leaves the chain connected.
    assert c.crosses(Line(Point(0, 1), Point(4, 1)))
    assert not c.crosses(Line(Point(0, 2), Point(4, 2)))


@pytest.mark.parametrize("make", [MonotoneChain, Polyline])
def test_chain_distances(make):
    c = make([Point(0, 0), Point(2, 0)])
    p = Point(1, 3)
    assert c.squaredDistance(p) == 9  # exact Fraction arithmetic
    assert c.distanceL1(p) == 3
    assert c.distanceLInf(p) == 3
    assert c.squaredDistance(Point(0, 0)) == 0
    # The Disk pair is the one that goes through floating point (irrational gap).
    assert isinstance(c.squaredDistance(Disk(Point(10, 0), 1)), float)
    # A chain is not convex, so it has no Hausdorff distance (pgl defines that
    # family only for the six convex shapes).
    assert not hasattr(c, "squaredHausdorffDistance")


@pytest.mark.parametrize("make", [MonotoneChain, Polyline])
def test_chain_intersection_returns_a_list_of_pieces(make):
    c = make([Point(0, 0), Point(2, 2)])
    # A chain can meet a line in several disjoint places, so the result is always
    # a list (never the single optional piece Convex returns).
    assert c.intersection(Line(Point(0, 1), Point(4, 1))) == [Point(1, 1)]
    assert c.intersection(Ray(Point(9, 9), Point(10, 10))) == []
    overlap = c.intersection(Segment(Point(1, 1), Point(3, 3)))
    assert overlap == [Segment(Point(1, 1), Point(2, 2))]
    assert c.intersection(Convex([Point(0, 0), Point(4, 0), Point(0, 4)]))


@pytest.mark.parametrize("make", [MonotoneChain, Polyline])
def test_chain_transformations(make):
    c = make([Point(0, 0), Point(2, 2)])
    assert (Transformation.rotation90() * c).vertices() == [Point(-2, 2), Point(0, 0)]
    assert c.rotated90().vertices() == [Point(-2, 2), Point(0, 0)]
    assert c.scaledUpX(3).vertices()[-1] == Point(6, 2)
    assert c.vertices()[-1] == Point(2, 2)  # the value-returning form copies

    c.scaleUpY(3)  # in place
    assert c.vertices()[-1] == Point(2, 6)


@pytest.mark.parametrize("make", [MonotoneChain, Polyline])
def test_chain_measures(make):
    c = make([Point(0, 0), Point(3, 4)])
    assert c.bbox() == Rectangle(Point(0, 0), Point(3, 4))
    assert c.diameter() == Segment(Point(0, 0), Point(3, 4))
    assert c.length() == pytest.approx(5.0)
    assert c.pointInside() == Point(Fraction(3, 2), 2)
    assert not c.isDegenerate()
    assert not c.empty()
    assert MonotoneChain([]).empty()
    assert Polyline([Point(1, 1), Point(1, 1)]).isDegenerate()


def test_polygon_and_chain_predicates_meet():
    # The chains are full columns of the shared matrix, so every other shape sees
    # them -- including Polygon, whose own row was regenerated for free.
    square = Polygon([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)])
    inside = Polyline([Point(1, 1), Point(2, 2), Point(3, 1)])
    assert square.contains(inside)
    assert inside.intersects(square)
    assert square.squaredDistance(MonotoneChain([Point(6, 0), Point(7, 1)])) == 4
