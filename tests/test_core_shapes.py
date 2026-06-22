"""Milestone 2: the remaining core shapes — constructors, accessors, measures,
the predicate matrix across pairs, and variant-typed intersection results."""

from fractions import Fraction

import pytest

import pypgl


# --- construction and basic accessors ------------------------------------

def test_all_shapes_importable():
    for name in (
        "OrientedSegment", "Line", "OrientedLine", "Ray",
        "Halfplane", "Triangle", "Rectangle", "Convex",
    ):
        assert hasattr(pypgl, name)


def test_oriented_segment_keeps_order_unlike_segment():
    # Segment normalizes endpoints; OrientedSegment preserves them.
    seg = pypgl.Segment(2, 2, 0, 0)
    assert seg.min() == pypgl.Point(0, 0)
    oseg = pypgl.OrientedSegment(2, 2, 0, 0)
    assert oseg.source() == pypgl.Point(2, 2)
    assert oseg.target() == pypgl.Point(0, 0)
    assert oseg.opposite().source() == pypgl.Point(0, 0)
    assert oseg.asSegment() == pypgl.Segment(0, 0, 2, 2)


def test_line_orientation_helpers():
    assert pypgl.Line(0, 0, 0, 5).isVertical()
    assert pypgl.Line(0, 3, 7, 3).isHorizontal()
    assert pypgl.Line(0, 0, 0, 0).isDegenerate()


def test_ray_supporting_lines():
    r = pypgl.Ray(0, 0, 2, 0)
    assert r.asLine() == pypgl.Line(0, 0, 2, 0)
    assert isinstance(r.asOrientedLine(), pypgl.OrientedLine)


def test_halfplane_opposite_and_boundary():
    h = pypgl.Halfplane(0, 0, 4, 0)
    assert h.asLine() == pypgl.Line(0, 0, 4, 0)
    assert h.opposite() != h


# --- exact measures ------------------------------------------------------

def test_triangle_measures_are_exact():
    t = pypgl.Triangle(0, 0, 4, 0, 0, 4)
    assert t.area() == 8
    assert t.twiceArea() == 16
    assert t.centroid() == pypgl.Point(Fraction(4, 3), Fraction(4, 3))
    assert len(t.vertices()) == 3
    assert len(t.edges()) == 3


def test_rectangle_measures():
    r = pypgl.Rectangle(0, 0, 4, 3)
    assert r.area() == 12
    assert r.min() == pypgl.Point(0, 0)
    assert r.max() == pypgl.Point(4, 3)
    assert len(r.vertices()) == 4


def test_rectangle_bounding_box_of_points():
    r = pypgl.Rectangle([pypgl.Point(1, 3), pypgl.Point(2, 4), pypgl.Point(3, 1),
                         pypgl.Point(5, 4), pypgl.Point(2, 3)])
    assert r == pypgl.Rectangle(1, 1, 5, 4)        # componentwise min/max
    assert pypgl.Rectangle([pypgl.Point(2, 2)]) == pypgl.Rectangle(2, 2, 2, 2)
    with pytest.raises(ValueError):
        pypgl.Rectangle([])                        # empty range is rejected


def test_rectangle_bounding_box_of_shapes():
    seg = pypgl.Segment(1, 1, 2, 2)
    tri = pypgl.Triangle(0, 0, 4, 0, 0, 3)
    cvx = pypgl.Convex([pypgl.Point(5, 5), pypgl.Point(7, 5), pypgl.Point(6, 8)])
    # An iterable mixing different bounded shape types (not allowed in C++).
    assert pypgl.Rectangle([seg, tri, cvx]) == pypgl.Rectangle(0, 0, 7, 8)
    # Points and shapes may be mixed.
    assert pypgl.Rectangle([pypgl.Point(-1, -1), tri]) == pypgl.Rectangle(-1, -1, 4, 3)
    # Any iterable works, e.g. a generator.
    assert pypgl.Rectangle(s for s in (seg, tri)) == pypgl.Rectangle(0, 0, 4, 3)


def test_rectangle_rejects_unbounded_shapes():
    # Unbounded shapes have no bbox(), so they cannot seed a bounding box.
    with pytest.raises(AttributeError):
        pypgl.Rectangle([pypgl.Line(0, 0, 1, 1)])
    with pytest.raises(ValueError):
        pypgl.Rectangle(iter([]))                  # empty iterable


def test_convex_hull_drops_interior_point():
    pts = [pypgl.Point(0, 0), pypgl.Point(4, 0), pypgl.Point(4, 4),
           pypgl.Point(0, 4), pypgl.Point(2, 2)]
    c = pypgl.Convex(pts)
    assert c.area() == 16
    assert len(c.vertices()) == 4  # interior (2,2) is not a hull vertex


# --- vertex iteration sugar ---------------------------------------------

def test_vertex_iteration():
    t = pypgl.Triangle(0, 0, 4, 0, 0, 4)
    assert list(t) == [t[0], t[1], t[2]]
    assert len(t) == 3
    r = pypgl.Rectangle(0, 0, 4, 3)
    assert len(list(r)) == 4


# --- predicate matrix across shapes -------------------------------------

def test_point_in_triangle_and_rectangle():
    t = pypgl.Triangle(0, 0, 4, 0, 0, 4)
    assert pypgl.Point(1, 1) in t
    assert pypgl.Point(5, 5) not in t
    r = pypgl.Rectangle(0, 0, 4, 4)
    assert pypgl.Point(2, 2) in r
    assert pypgl.Point(9, 9) not in r


def test_cross_shape_predicates():
    t = pypgl.Triangle(0, 0, 4, 0, 0, 4)
    line = pypgl.Line(0, 2, 4, 2)
    assert t.intersects(line)
    assert not t.contains(line)
    # A line through the interior separates the triangle.
    assert line.separates(t)


def test_line_contains_collinear_segment():
    line = pypgl.Line(0, 0, 6, 6)
    assert line.contains(pypgl.Segment(1, 1, 3, 3))
    assert not line.contains(pypgl.Segment(1, 1, 3, 4))


# --- typed intersection results -----------------------------------------

def test_line_line_intersection_point():
    a = pypgl.Line(0, 0, 4, 4)
    b = pypgl.Line(0, 4, 4, 0)
    assert a.intersection(b) == pypgl.Point(2, 2)


def test_line_line_intersection_is_line_when_equal():
    a = pypgl.Line(0, 0, 4, 4)
    b = pypgl.Line(1, 1, 9, 9)
    assert isinstance(a.intersection(b), pypgl.Line)


def test_parallel_lines_intersection_none():
    a = pypgl.Line(0, 0, 4, 0)
    b = pypgl.Line(0, 1, 4, 1)
    assert a.intersection(b) is None


def test_ray_ray_intersection_variants():
    r = pypgl.Ray(0, 0, 1, 0)
    # Opposite-overlapping rays meet in a segment.
    assert isinstance(r.intersection(pypgl.Ray(2, 0, 1, 0)), pypgl.Segment)
    # Same-direction overlapping rays meet in a ray.
    assert isinstance(r.intersection(pypgl.Ray(1, 0, 2, 0)), pypgl.Ray)


def test_triangle_line_clips_to_segment():
    t = pypgl.Triangle(0, 0, 4, 0, 0, 4)
    clipped = t.intersection(pypgl.Line(0, 2, 4, 2))
    assert isinstance(clipped, pypgl.Segment)
    assert clipped == pypgl.Segment(0, 2, 2, 2)


def test_convex_point_intersection():
    c = pypgl.Convex([pypgl.Point(0, 0), pypgl.Point(4, 0),
                      pypgl.Point(4, 4), pypgl.Point(0, 4)])
    assert c.intersection(pypgl.Point(2, 2)) == pypgl.Point(2, 2)
    assert c.intersection(pypgl.Point(9, 9)) is None


# --- exact squared distance ---------------------------------------------

def test_squared_distance_is_exact_fraction():
    p = pypgl.Point(0, 0)
    # Perpendicular distance to the line x + y = 1 is 1/sqrt(2); squared = 1/2.
    d = p.squaredDistance(pypgl.Line(0, 1, 1, 0))
    assert d == Fraction(1, 2)
    assert isinstance(d, Fraction)


def test_squared_distance_across_shapes():
    p = pypgl.Point(0, 0)
    assert p.squaredDistance(pypgl.Point(3, 4)) == 25
    assert p.squaredDistance(pypgl.Segment(3, 0, 3, 9)) == 9
    assert p.squaredDistance(pypgl.Line(0, 2, 2, 2)) == 4
    t = pypgl.Triangle(0, 0, 4, 0, 0, 4)
    assert t.squaredDistance(pypgl.Point(0, -3)) == 9
    assert pypgl.Rectangle(0, 0, 1, 1).squaredDistance(pypgl.Rectangle(4, 0, 5, 1)) == 9
    c = pypgl.Convex([pypgl.Point(0, 0), pypgl.Point(2, 0), pypgl.Point(0, 2)])
    assert c.squaredDistance(pypgl.Point(5, 0)) == 9


def test_squared_distance_is_symmetric():
    line = pypgl.Line(0, 1, 1, 0)
    p = pypgl.Point(0, 0)
    assert line.squaredDistance(p) == p.squaredDistance(line)


def test_convex_halfplane_squared_distance():
    # Convex x Halfplane is bound in both directions (pgl gap since fixed).
    c = pypgl.Convex([pypgl.Point(0, 0), pypgl.Point(2, 0), pypgl.Point(0, 2)])
    h = pypgl.Halfplane(0, 5, 4, 5)  # closed half-plane bounded by y = 5
    assert c.squaredDistance(h) == 9
    assert h.squaredDistance(c) == c.squaredDistance(h)


def test_squared_distance_zero_on_contact():
    s = pypgl.Segment(0, 0, 4, 0)
    assert s.squaredDistance(pypgl.Point(2, 0)) == 0
    t = pypgl.Triangle(0, 0, 4, 0, 0, 4)
    assert t.squaredDistance(pypgl.Point(1, 1)) == 0


# --- exact bounding box --------------------------------------------------

def test_bbox_exact_for_each_bounded_shape():
    R = pypgl.Rectangle
    assert isinstance(pypgl.Point(2, 3).bbox(), R)
    assert pypgl.Point(2, 3).bbox() == R(2, 3, 2, 3)          # degenerate
    assert pypgl.Segment(0, 0, 3, 5).bbox() == R(0, 0, 3, 5)
    assert pypgl.OrientedSegment(3, 5, 0, 0).bbox() == R(0, 0, 3, 5)
    assert pypgl.Triangle(0, 0, 4, 0, 1, 3).bbox() == R(0, 0, 4, 3)
    assert pypgl.Rectangle(0, 0, 4, 3).bbox() == R(0, 0, 4, 3)  # itself
    c = pypgl.Convex([pypgl.Point(0, 0), pypgl.Point(4, 0),
                      pypgl.Point(2, 5), pypgl.Point(1, 1)])
    assert c.bbox() == R(0, 0, 4, 5)


def test_bbox_exact_with_big_coordinates():
    big = 10 ** 40
    t = pypgl.Triangle(pypgl.Point(0, 0), pypgl.Point(big, 0),
                       pypgl.Point(0, big))
    assert t.bbox() == pypgl.Rectangle(0, 0, big, big)


def test_unbounded_shapes_have_no_bbox():
    for name in ("Line", "OrientedLine", "Ray", "Halfplane"):
        assert not hasattr(getattr(pypgl, name), "bbox"), name


# --- value semantics for the new shapes ---------------------------------

def test_new_shapes_hashable_and_comparable():
    assert len({pypgl.Triangle(0, 0, 4, 0, 0, 4),
                pypgl.Triangle(0, 0, 4, 0, 0, 4)}) == 1
    assert len({pypgl.Line(0, 0, 1, 1), pypgl.Line(0, 0, 2, 2)}) == 1  # equal lines
    assert pypgl.Rectangle(0, 0, 4, 3) == pypgl.Rectangle(4, 3, 0, 0)


def test_exact_big_coordinates_roundtrip():
    big = 10 ** 40
    t = pypgl.Triangle(pypgl.Point(0, 0), pypgl.Point(big, 0),
                       pypgl.Point(0, big))
    assert t.twiceArea() == big * big


def test_float_still_rejected_for_new_shapes():
    with pytest.raises(TypeError):
        pypgl.Triangle(0.0, 0, 1, 0, 0, 1)
