"""The degeneracy classification shared by every shape.

pgl splits degenerate shapes in two. Some are *well defined*: a triangle with
three collinear vertices really is a segment, a radius-zero disk really is a
point, and every operation on them answers the limit case. Those are named by
isPoint / isSegment, with getIfPoint / getIfSegment handing back the shape the
point set actually is. Others are **undefined** -- a line through two equal
points has no direction, a disk through three distinct collinear points could be
either of two half-planes -- and for those every geometric operation is
undefined behavior in the C++ sense. isUndefined() is what tells the two apart.

A shape that has dropped below its natural dimension is entirely boundary with
empty interior, which is the other half of the contract tested here.
"""

import pytest

from pypgl import (
    Convex,
    Disk,
    Halfplane,
    HalfplaneIntersection,
    Line,
    MonotoneChain,
    OrientedLine,
    OrientedSegment,
    Point,
    Polygon,
    PolygonWithHoles,
    Polyline,
    Ray,
    Rectangle,
    Segment,
    Triangle,
)


# Every shape that can collapse to a point, with a collapsed instance.
COLLAPSED_TO_A_POINT = [
    Segment(Point(2, 2), Point(2, 2)),
    OrientedSegment(Point(2, 2), Point(2, 2)),
    Triangle(Point(2, 2), Point(2, 2), Point(2, 2)),
    Rectangle(Point(2, 2), Point(2, 2)),
    Convex([Point(2, 2)]),
    Polygon([Point(2, 2), Point(2, 2), Point(2, 2)]),
    MonotoneChain([Point(2, 2)]),
    Polyline([Point(2, 2), Point(2, 2)]),
    Disk(Point(2, 2), 0),
    HalfplaneIntersection(Rectangle(Point(2, 2), Point(2, 2))),
]

# The two-dimensional shapes that can collapse to a segment, with a collapsed
# instance. Each of these really has dropped a dimension. Disk is absent: a disk
# is never a segment, so isPoint and isUndefined cover it between them.
COLLAPSED_TO_A_SEGMENT = [
    Triangle(Point(0, 0), Point(2, 2), Point(4, 4)),
    Rectangle(Point(0, 0), Point(4, 0)),
    Convex([Point(0, 0), Point(2, 2), Point(4, 4)]),
    Polygon([Point(0, 0), Point(4, 4), Point(2, 2)]),
    HalfplaneIntersection(Rectangle(Point(0, 0), Point(4, 0))),
]

# The chains are the interesting exception: a straight chain covers exactly a
# segment, so isSegment holds, but a chain is one-dimensional to begin with and
# has therefore dropped nothing. It keeps its own boundary convention (the two
# extreme vertices) and its relative interior, and is not degenerate.
STRAIGHT_CHAINS = [
    MonotoneChain([Point(0, 0), Point(2, 2), Point(4, 4)]),
    Polyline([Point(0, 0), Point(2, 2), Point(4, 4)]),
]

# The four shapes with nothing to collapse *to*: a degenerate one is undefined
# outright, so they carry isUndefined and nothing else.
UNDEFINED_ONLY = [Line, OrientedLine, Ray, Halfplane]


# --- isPoint / getIfPoint ---------------------------------------------------

@pytest.mark.parametrize("shape", COLLAPSED_TO_A_POINT, ids=lambda s: type(s).__name__)
def test_a_collapsed_shape_reports_the_point_it_covers(shape):
    assert shape.isPoint()
    assert shape.getIfPoint() == Point(2, 2)
    assert shape.isDegenerate()
    # Well defined: it really is that point, and behaves like it.
    assert not shape.isUndefined()


@pytest.mark.parametrize("shape", COLLAPSED_TO_A_POINT, ids=lambda s: type(s).__name__)
def test_a_shape_collapsed_to_a_point_is_not_also_a_segment(shape):
    if hasattr(shape, "isSegment"):
        assert not shape.isSegment()
        assert shape.getIfSegment() is None


def test_an_ordinary_shape_is_no_kind_of_degenerate():
    t = Triangle(Point(0, 0), Point(4, 0), Point(0, 4))
    assert not t.isPoint()
    assert not t.isSegment()
    assert not t.isUndefined()
    assert not t.isDegenerate()
    assert t.getIfPoint() is None
    assert t.getIfSegment() is None


# --- isSegment / getIfSegment -----------------------------------------------

@pytest.mark.parametrize(
    "shape", COLLAPSED_TO_A_SEGMENT + STRAIGHT_CHAINS, ids=lambda s: type(s).__name__
)
def test_a_flattened_shape_reports_the_segment_it_covers(shape):
    assert shape.isSegment()
    assert not shape.isPoint()
    assert shape.getIfSegment() is not None
    assert shape.getIfSegment().length() > 0
    assert not shape.isUndefined()


@pytest.mark.parametrize("shape", COLLAPSED_TO_A_SEGMENT, ids=lambda s: type(s).__name__)
def test_a_flattened_area_shape_is_degenerate(shape):
    assert shape.isDegenerate()


@pytest.mark.parametrize("shape", STRAIGHT_CHAINS, ids=lambda s: type(s).__name__)
def test_a_straight_chain_is_a_segment_without_being_degenerate(shape):
    # A chain is already one-dimensional, so covering a segment costs it no
    # dimension: it keeps its relative interior and is not degenerate. Only a
    # chain collapsed all the way to a point is.
    assert shape.isSegment()
    assert not shape.isDegenerate()
    midpoint = shape.getIfSegment().midpoint()
    assert shape.interiorContains(midpoint)
    assert not shape.boundaryContains(midpoint)
    # Its boundary is still its two extreme vertices, as for any chain.
    assert shape.boundaryContains(Point(0, 0))
    assert shape.boundaryContains(Point(4, 4))


def test_a_segment_never_collapses_to_a_segment():
    # A Segment's only degenerate form is a point, so it has no isSegment.
    s = Segment(Point(0, 0), Point(4, 4))
    assert not hasattr(s, "isSegment")
    assert not s.isPoint()


def test_a_disk_is_never_a_segment():
    d = Disk(Point(0, 0), 3)
    assert not hasattr(d, "isSegment")


# --- isUndefined ------------------------------------------------------------

@pytest.mark.parametrize("cls", UNDEFINED_ONLY, ids=lambda c: c.__name__)
def test_a_shape_through_two_equal_points_is_undefined(cls):
    # No direction, so no reasonable interpretation.
    degenerate = cls(Point(1, 1), Point(1, 1))
    assert degenerate.isDegenerate()
    assert degenerate.isUndefined()
    # ... and these four have nothing to collapse to, so no getIf* pair.
    assert not hasattr(degenerate, "isPoint")
    assert not hasattr(degenerate, "getIfPoint")


@pytest.mark.parametrize("cls", UNDEFINED_ONLY, ids=lambda c: c.__name__)
def test_an_ordinary_line_like_shape_is_defined(cls):
    assert not cls(Point(0, 0), Point(1, 1)).isUndefined()


def test_a_disk_through_distinct_collinear_points_is_undefined():
    # Three distinct collinear points have no circle through them; two distinct
    # ones have infinitely many. Either way there is no disk to speak of.
    d = Disk(Point(0, 0), Point(1, 1), Point(2, 2))
    assert d.isDegenerate()
    assert d.isUndefined()
    assert not d.isPoint()


def test_a_segment_is_never_undefined():
    # A degenerate segment is always a point.
    assert not Segment(Point(2, 2), Point(2, 2)).isUndefined()


def test_an_empty_chain_is_undefined():
    # True only for an empty chain, which has no vertex at all.
    assert MonotoneChain([]).isUndefined()
    assert Polyline([]).isUndefined()


def test_an_empty_convex_is_the_empty_set_not_an_undefined_one():
    # Upstream gave Rectangle, Convex and Polygon a real empty state: a hull
    # with no vertex is now the empty set, which is well defined (contained in
    # every shape, meeting none) rather than undefined.
    empty = Convex([])
    assert empty.empty()
    assert not empty.isUndefined()


def test_a_halfplane_intersection_is_never_undefined():
    # insert() ignores undefined half-planes, so every region is well defined.
    assert not HalfplaneIntersection([Halfplane(Point(1, 1), Point(1, 1))]).isUndefined()


def test_a_self_overlapping_polygon_is_undefined():
    # A polygon whose zero area comes from a self-overlapping boundary rather
    # than from collinear vertices covers more than a segment, yet is degenerate.
    p = Polygon([Point(0, 0), Point(4, 0), Point(0, 0), Point(4, 4)])
    if p.isDegenerate() and not p.isSegment() and not p.isPoint():
        assert p.isUndefined()


# --- a collapsed shape is all boundary and no interior ----------------------

@pytest.mark.parametrize(
    "shape",
    COLLAPSED_TO_A_POINT + COLLAPSED_TO_A_SEGMENT,
    ids=lambda s: f"{type(s).__name__}-{'pt' if s.isPoint() else 'seg'}",
)
def test_a_collapsed_shape_has_empty_interior(shape):
    # Having dropped below its natural dimension, it is entirely boundary: so
    # boundaryContains coincides with contains, and nothing is interior to it.
    # (The straight chains are excluded on purpose -- see the test above: they
    # have dropped nothing, so they keep their relative interior.)
    carrier = shape.getIfPoint() or shape.getIfSegment()
    probe = carrier if isinstance(carrier, Point) else carrier.midpoint()
    assert shape.contains(probe)
    assert shape.boundaryContains(probe)
    assert not shape.interiorContains(probe)
    assert not shape.interiorsIntersect(shape)


# --- PolygonWithHoles, which has the tests but no getIf* pair ---------------

def test_a_region_reports_its_collapse_without_a_getif_pair():
    r = PolygonWithHoles(Polygon([Point(0, 0), Point(4, 0), Point(2, 0)]))
    assert r.isSegment()
    assert not r.isPoint()
    # Upstream gives the region no getIfPoint/getIfSegment.
    assert not hasattr(r, "getIfSegment")


def test_the_empty_region_is_undefined():
    # Degenerate without covering a point or a segment.
    r = PolygonWithHoles()
    assert r.isDegenerate()
    assert r.isUndefined()
    assert not r.isPoint()
    assert not r.isSegment()


# --- Point itself has no degeneracy at all ----------------------------------

def test_a_point_cannot_degenerate():
    p = Point(1, 2)
    for name in ("isPoint", "getIfPoint", "isSegment", "getIfSegment", "isUndefined"):
        assert not hasattr(p, name), name
