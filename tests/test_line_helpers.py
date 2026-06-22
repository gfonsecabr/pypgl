"""Line-like helpers shared across Segment/OrientedSegment/Line/OrientedLine/Ray
(slope, isVertical/isHorizontal/isDegenerate, collinear, parallel), point<->line
duality, and the exact L1/L-infinity distances and lengths."""

from fractions import Fraction

import pypgl


LINE_LIKE = ("Segment", "OrientedSegment", "Line", "OrientedLine", "Ray")


# --- slope and orientation flags ----------------------------------------

def test_slope_exact_fraction():
    s = pypgl.Segment(0, 0, 2, 4)
    assert s.slope() == 2
    assert pypgl.Segment(0, 0, 3, 1).slope() == Fraction(1, 3)
    assert pypgl.Line(0, 0, 1, 1).slope() == 1


def test_vertical_horizontal_degenerate_flags():
    assert pypgl.Segment(1, 0, 1, 5).isVertical()
    assert pypgl.Segment(0, 2, 7, 2).isHorizontal()
    diag = pypgl.Segment(0, 0, 2, 4)
    assert not diag.isVertical() and not diag.isHorizontal()
    assert not diag.isDegenerate()


def test_line_helpers_present_on_all_line_like_shapes():
    for name in LINE_LIKE:
        cls = getattr(pypgl, name)
        for method in ("slope", "isVertical", "isHorizontal", "isDegenerate"):
            assert hasattr(cls, method), f"{name}.{method} missing"


# --- collinear and parallel ---------------------------------------------

def test_collinear_against_point_and_lines():
    line = pypgl.Line(0, 0, 1, 1)
    assert line.collinear(pypgl.Point(5, 5))
    assert not line.collinear(pypgl.Point(0, 1))
    assert line.collinear(pypgl.Segment(2, 2, 3, 3))
    assert line.collinear(pypgl.Line(4, 4, 9, 9))


def test_parallel_distinct_from_collinear():
    a = pypgl.Line(0, 0, 1, 1)
    shifted = pypgl.Line(0, 1, 1, 2)   # parallel but not collinear
    assert a.parallel(shifted)
    assert not a.collinear(shifted)
    crossing = pypgl.Line(0, 1, 1, 0)
    assert not a.parallel(crossing)


def test_oriented_line_parallel_ray_both_directions():
    # pgl gap (now fixed): OrientedLine.parallel(Ray) used to be absent.
    ol = pypgl.OrientedLine(0, 0, 1, 1)
    ray = pypgl.Ray(3, 3, 5, 5)
    assert ol.parallel(ray)
    assert ray.parallel(ol)


# --- point <-> line duality ---------------------------------------------

def test_point_dual_and_polar_return_lines():
    pt = pypgl.Point(2, 3)
    assert isinstance(pt.dual(), pypgl.Line)
    assert isinstance(pt.polar(), pypgl.Line)


def test_dual_is_an_involution_via_line():
    # A point's dual is a line; that line's dual recovers the point.
    pt = pypgl.Point(2, 3)
    assert pt.dual().dual() == pt


# --- exact L1 / L-infinity distances and lengths ------------------------

def test_point_l1_linf_distances_exact():
    o = pypgl.Point(0, 0)
    q = pypgl.Point(3, 4)
    assert o.distanceL1(q) == 7        # 3 + 4
    assert o.distanceLInf(q) == 4      # max(3, 4)
    assert o.distanceL1(q) == Fraction(7)


def test_segment_l1_linf_lengths_exact():
    s = pypgl.Segment(0, 0, 3, 4)
    assert s.lengthL1() == 7
    assert s.lengthLInf() == 4
    assert s.squaredLength() == 25     # exact; length() would be ~5.0


def test_segment_as_line():
    s = pypgl.Segment(0, 0, 2, 4)
    assert s.asLine() == pypgl.Line(0, 0, 2, 4)
