"""L1 (Manhattan) / L-infinity (Chebyshev) distance, and Hausdorff distance.

Mirrors squaredDistance's coverage (see PGL_BIND_ALL_L1LINF_DISTANCE /
PGL_BIND_ALL_HAUSDORFF_DISTANCE in src/common.h) with two narrower exceptions
upstream pgl does not close yet:

* Disk only has an L1/LInf distance pair against Point (a coarse angular scan
  refined by golden-section search, so always a float); no other shape has a
  closed form to or from Disk yet.
* squaredHausdorffDistance / hausdorffDistanceL1 / hausdorffDistanceLInf are
  only defined among the six *convex* shapes {Point, Segment, OrientedSegment,
  Rectangle, Triangle, Convex} -- Disk (no closed form) and Polygon (may be
  non-convex) are excluded entirely. These compute the standard *symmetric*
  Hausdorff distance max(h(A, B), h(B, A)), not a one-sided directed
  distance, so a.squaredHausdorffDistance(b) always equals
  b.squaredHausdorffDistance(a).
"""

from fractions import Fraction

import pytest

import pypgl
from pypgl import Convex, Disk, OrientedSegment, Point, Polygon, Rectangle, Segment, Triangle


# --- distanceL1 / distanceLInf ---------------------------------------------

def test_point_point_l1_linf_are_exact():
    a, b = Point(0, 0), Point(3, 4)
    assert a.distanceL1(b) == 7
    assert a.distanceLInf(b) == 4
    assert isinstance(a.distanceL1(b), Fraction)


def test_segment_point_l1_linf():
    s = Segment(Point(0, 0), Point(0, 10))
    assert s.distanceL1(Point(3, 5)) == 3
    assert s.distanceLInf(Point(3, 5)) == 3


def test_rectangle_triangle_convex_l1_linf_cross_product():
    r = Rectangle(Point(0, 0), Point(2, 2))
    t = Triangle(Point(10, 0), Point(12, 0), Point(10, 2))
    c = Convex([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)])
    # Disjoint rectangle/triangle: L1/LInf distances are nonnegative and exact.
    assert r.distanceL1(t) > 0
    assert r.distanceLInf(t) > 0
    assert isinstance(r.distanceL1(t), (int, Fraction))
    # Overlapping convex/rectangle: distance is zero.
    assert c.distanceL1(r) == 0
    assert c.distanceLInf(r) == 0


def test_polygon_gets_l1_linf_but_not_hausdorff():
    p = Polygon([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)])
    assert p.distanceL1(Point(10, 0)) == 6
    assert p.distanceLInf(Point(10, 0)) == 6
    assert not hasattr(p, "squaredHausdorffDistance")
    assert not hasattr(p, "hausdorffDistanceL1")
    assert not hasattr(p, "hausdorffDistanceLInf")


def test_disk_l1_linf_only_against_point_and_always_float():
    d = Disk(Point(0, 0), 5)
    assert d.distanceL1(Point(10, 0)) == pytest.approx(5.0)
    assert d.distanceLInf(Point(10, 0)) == pytest.approx(5.0)
    assert isinstance(d.distanceL1(Point(10, 0)), float)
    # Symmetric: Point<->Disk works from either side.
    assert Point(10, 0).distanceL1(d) == pytest.approx(5.0)
    assert Point(10, 0).distanceLInf(d) == pytest.approx(5.0)


def test_disk_l1_linf_not_defined_against_other_shapes():
    d = Disk(Point(0, 0), 5)
    with pytest.raises(TypeError):
        d.distanceL1(Segment(Point(10, 0), Point(11, 0)))
    with pytest.raises(TypeError):
        Segment(Point(10, 0), Point(11, 0)).distanceL1(d)


def test_l1_linf_present_on_every_non_disk_shape():
    for name in ("Point", "Segment", "OrientedSegment", "Line", "OrientedLine",
                 "Ray", "Halfplane", "Triangle", "Rectangle", "Convex", "Polygon"):
        cls = getattr(pypgl, name)
        assert hasattr(cls, "distanceL1"), f"{name}.distanceL1 missing"
        assert hasattr(cls, "distanceLInf"), f"{name}.distanceLInf missing"


# --- Hausdorff distance (squared, L1, LInf) --------------------------------

HAUSDORFF_SHAPES = ("Point", "Segment", "OrientedSegment", "Rectangle", "Triangle", "Convex")


def test_hausdorff_present_only_on_the_six_convex_shapes():
    for name in HAUSDORFF_SHAPES:
        cls = getattr(pypgl, name)
        assert hasattr(cls, "squaredHausdorffDistance"), f"{name} missing squaredHausdorffDistance"
        assert hasattr(cls, "hausdorffDistanceL1"), f"{name} missing hausdorffDistanceL1"
        assert hasattr(cls, "hausdorffDistanceLInf"), f"{name} missing hausdorffDistanceLInf"
    for name in ("Line", "OrientedLine", "Ray", "Halfplane", "Polygon", "Disk"):
        cls = getattr(pypgl, name)
        assert not hasattr(cls, "squaredHausdorffDistance"), f"{name} should not have squaredHausdorffDistance"


def test_squared_hausdorff_distance_of_segment_onto_itself_is_zero():
    s = Segment(Point(0, 0), Point(4, 0))
    assert s.squaredHausdorffDistance(s) == 0


def test_squared_hausdorff_distance_point_to_segment():
    # pgl's squaredHausdorffDistance is the standard *symmetric* Hausdorff
    # distance max(h(A, B), h(B, A)): here that is the segment's farthest
    # endpoint (0,0)-(3,4) squared-distance 25 from the point, which is at
    # least as large as the point's own one-sided distance to the segment (9).
    p = Point(0, 0)
    s = Segment(Point(3, 0), Point(3, 4))
    assert p.squaredHausdorffDistance(s) == 25
    assert p.squaredHausdorffDistance(s) == s.squaredHausdorffDistance(p)


def test_hausdorff_distance_l1_linf_of_rectangle_pair_is_symmetric():
    a = Rectangle(Point(0, 0), Point(2, 2))
    b = Rectangle(Point(0, 0), Point(4, 4))
    # a is a proper subset of b, so the one-sided distance from a to b is 0,
    # but the symmetric Hausdorff distance also accounts for b's corner (4,4)
    # being 4 away (L1) from the nearest point of a -- so both directions
    # return that same nonzero value, whichever operand order is used.
    assert a.hausdorffDistanceL1(b) == 4
    assert b.hausdorffDistanceL1(a) == 4
    assert a.hausdorffDistanceLInf(b) == 2
    assert b.hausdorffDistanceLInf(a) == 2


def test_hausdorff_matrix_is_symmetric_in_argument_types():
    # Every pair among the six shapes should be callable in both directions
    # (rank-based forwarding on the C++ side).
    shapes = [
        Point(0, 0),
        Segment(Point(1, 0), Point(1, 1)),
        OrientedSegment(Point(2, 0), Point(2, 1)),
        Rectangle(Point(0, 0), Point(1, 1)),
        Triangle(Point(5, 5), Point(6, 5), Point(5, 6)),
        Convex([Point(0, 0), Point(3, 0), Point(3, 3), Point(0, 3)]),
    ]
    for a in shapes:
        for b in shapes:
            assert a.squaredHausdorffDistance(b) >= 0
            assert a.hausdorffDistanceL1(b) >= 0
            assert a.hausdorffDistanceLInf(b) >= 0
