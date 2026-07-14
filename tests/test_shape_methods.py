"""The per-shape methods that mirror pgl's own: vertical/horizontal queries
(yAtX/xAtY), the orientation sign and the half-planes it induces, the geometric
above/below half-planes, endpoint membership, and the shape conversions
(asConvex/asPolygon/asRay/asOrientedLine) plus circumcircles.

Throughout, "above" means larger y (the math convention, not the image one).
"""

from fractions import Fraction

import pypgl


ORIENTED = ("OrientedSegment", "OrientedLine", "Ray")
XY_AT = ("Segment", "OrientedSegment", "Line", "OrientedLine", "Ray")
HALFPLANE_SHAPES = ("Line", "OrientedLine", "Ray")


# --- yAtX / xAtY --------------------------------------------------------

def test_yatx_xaty_exact_on_a_segment():
    s = pypgl.Segment(0, 0, 4, 2)          # y = x/2
    assert s.yAtX(2) == 1
    assert s.yAtX(1) == Fraction(1, 2)     # exact, not 0.5
    assert s.xAtY(Fraction(1, 2)) == 1


def test_yatx_is_none_beyond_a_bounded_shape():
    s = pypgl.Segment(0, 0, 4, 2)
    assert s.yAtX(9) is None               # past the far endpoint
    assert s.yAtX(-1) is None
    ray = pypgl.Ray(0, 0, 2, 1)            # unbounded forward only
    assert ray.yAtX(10) == 5
    assert ray.yAtX(-10) is None           # behind the source


def test_yatx_spans_the_whole_line():
    line = pypgl.Line(0, 0, 2, 1)
    assert line.yAtX(-10) == -5
    assert line.xAtY(-5) == -10


def test_xy_at_bound_on_every_line_like_shape():
    for name in XY_AT:
        cls = getattr(pypgl, name)
        assert hasattr(cls, "yAtX") and hasattr(cls, "xAtY"), name


# --- orientation sign ---------------------------------------------------

def test_orientation_sign_is_left_positive():
    o = pypgl.OrientedSegment(0, 0, 4, 0)          # pointing +x
    assert o.orientation(pypgl.Point(1, 1)) == 1   # left
    assert o.orientation(pypgl.Point(1, -1)) == -1  # right
    assert o.orientation(pypgl.Point(2, 0)) == 0   # collinear


def test_orientation_flips_with_the_direction():
    p = pypgl.Point(1, 1)
    o = pypgl.OrientedSegment(0, 0, 4, 0)
    assert o.orientation(p) == -o.opposite().orientation(p)


def test_orientation_bound_on_every_oriented_shape():
    p = pypgl.Point(1, 1)
    for name in ORIENTED:
        shape = getattr(pypgl, name)(0, 0, 4, 0)
        assert shape.orientation(p) == 1, name


# --- left / right half-planes (orientation-dependent) -------------------

def test_left_and_right_halfplanes_follow_the_direction():
    o = pypgl.OrientedSegment(0, 0, 4, 0)          # pointing +x
    left, right = o.leftHalfplane(), o.rightHalfplane()
    assert left.contains(pypgl.Point(1, 1)) and not left.contains(pypgl.Point(1, -1))
    assert right.contains(pypgl.Point(1, -1)) and not right.contains(pypgl.Point(1, 1))
    # Both are closed, so the boundary belongs to each.
    assert left.contains(pypgl.Point(2, 0)) and right.contains(pypgl.Point(2, 0))


def test_left_right_halfplanes_swap_with_the_opposite():
    o = pypgl.OrientedLine(0, 0, 2, 1)
    assert o.leftHalfplane() == o.opposite().rightHalfplane()


# --- above / below half-planes (geometric, orientation-independent) -----

def test_halfplane_above_contains_the_larger_y_side():
    # y = x/2: (0, 5) is above it, (0, -5) below.
    for name in HALFPLANE_SHAPES:
        shape = getattr(pypgl, name)(0, 0, 2, 1)
        above, below = shape.halfplaneAbove(), shape.halfplaneBelow()
        assert above.contains(pypgl.Point(0, 5)), name
        assert not above.contains(pypgl.Point(0, -5)), name
        assert below.contains(pypgl.Point(0, -5)), name
        assert not below.contains(pypgl.Point(0, 5)), name


def test_halfplane_above_of_a_vertical_line_is_the_smaller_x_side():
    v = pypgl.Line(0, 0, 0, 5)
    assert v.halfplaneAbove().contains(pypgl.Point(-5, 0))
    assert v.halfplaneBelow().contains(pypgl.Point(5, 0))


def test_halfplane_above_ignores_the_orientation():
    a = pypgl.OrientedLine(0, 0, 2, 1)
    assert a.halfplaneAbove() == a.opposite().halfplaneAbove()


# --- endpoint membership ------------------------------------------------

def test_contains_endpoint_is_not_a_geometric_test():
    s = pypgl.Segment(0, 0, 4, 2)
    assert s.containsEndpoint(pypgl.Point(4, 2))
    assert not s.containsEndpoint(pypgl.Point(2, 1))   # on the segment, not an endpoint
    assert s.contains(pypgl.Point(2, 1))               # ... but geometrically inside


# --- conversions --------------------------------------------------------

def test_oriented_segment_conversions_keep_the_direction():
    o = pypgl.OrientedSegment(0, 0, 4, 2)
    assert o.asOrientedLine() == pypgl.OrientedLine(0, 0, 4, 2)
    assert o.asRay() == pypgl.Ray(0, 0, 4, 2)
    assert o.asSegment() == pypgl.Segment(0, 0, 4, 2)


def test_halfplane_as_oriented_line_round_trips():
    h = pypgl.Halfplane(0, 0, 3, 0)
    assert h.asOrientedLine().leftHalfplane() == h


def test_halfplane_line_helpers():
    h = pypgl.Halfplane(0, 0, 3, 0)
    assert h.isHorizontal() and not h.isVertical()
    assert h.slope() == 0


def test_point_swapped():
    assert pypgl.Point(2, 5).swapped() == pypgl.Point(5, 2)
    p = pypgl.Point(2, 5)
    assert p.swapped().swapped() == p


def test_triangle_and_rectangle_as_convex_and_polygon():
    t = pypgl.Triangle(0, 0, 4, 0, 0, 3)
    assert isinstance(t.asConvex(), pypgl.Convex)
    assert isinstance(t.asPolygon(), pypgl.Polygon)
    assert list(t.asConvex().vertices()) == list(t.vertices())

    r = pypgl.Rectangle(0, 0, 2, 2)
    assert isinstance(r.asConvex(), pypgl.Convex)
    assert len(r.asPolygon().vertices()) == 4

    c = pypgl.Convex([pypgl.Point(0, 0), pypgl.Point(2, 0), pypgl.Point(0, 2)])
    assert isinstance(c.asPolygon(), pypgl.Polygon)
    assert c.asPolygon().area() == c.area()


# --- triangle shape queries and circumcircles ---------------------------

def test_triangle_shape_flags():
    right = pypgl.Triangle(0, 0, 4, 0, 0, 3)       # 3-4-5
    assert right.isRectangle() and not right.isObtuse()
    obtuse = pypgl.Triangle(0, 0, 4, 0, 5, 1)
    assert obtuse.isObtuse() and not obtuse.isRectangle()
    isosceles = pypgl.Triangle(0, 0, 4, 0, 2, 3)
    assert isosceles.isIsosceles()
    assert not right.isIsosceles()


def test_triangle_circumcircle_passes_through_the_vertices():
    t = pypgl.Triangle(0, 0, 4, 0, 0, 3)
    disk = t.circumcircle()
    assert isinstance(disk, pypgl.Disk)
    # Right triangle: the circumcenter is the hypotenuse midpoint, r = 5/2.
    assert disk.center() == pypgl.Point(2, Fraction(3, 2))
    assert disk.squaredRadius() == Fraction(25, 4)
    for v in t.vertices():
        assert disk.boundaryContains(v)


def test_rectangle_circumcircle_passes_through_the_corners():
    r = pypgl.Rectangle(0, 0, 2, 2)
    disk = r.circumcircle()
    assert disk.center() == pypgl.Point(1, 1)
    assert disk.squaredRadius() == 2
    for v in r.vertices():
        assert disk.boundaryContains(v)
