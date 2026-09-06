"""closestSegments / closestPoints: where a squaredDistance is realized.

squaredDistance says how far apart two shapes are and forgets where.
``closestSegments`` names the two elements attaining it -- the receiver's
first -- and ``closestPoints`` names the two points themselves. Both answer
``None`` exactly when the distance is zero, which is the same question the
distance already answers.

The two grids are not the same shape, and the reason is what each answer has
to name (see PGL_BIND_ALL_CLOSEST / PGL_BIND_CLOSEST_POINTS_UNBOUNDED in
src/common.h):

* ``closestSegments`` needs both operands bounded polygonal -- covered by
  finitely many segments whose endpoints are the shape's own vertices -- so it
  is the eleven such shapes squared, and it stays exact in the plain number
  type because the answer is made of vertices already stored.
* ``closestPoints`` needs only one of them to be: an unbounded convex operand
  realizes the distance at a point on no edge and at no vertex, so it has no
  element to name, but the point is still there and still exact. Unbounded on
  *both* sides is left out, and so is Disk in either position.
"""

from fractions import Fraction

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
    PolygonSet,
    PolygonWithHoles,
    Polyline,
    Ray,
    Rectangle,
    Segment,
    Triangle,
)


# The eleven bounded polygonal shapes, each placed well clear of the origin so
# every pair below is at a positive distance from a Point(0, 0) receiver.
def _bounded():
    ring = [Point(10, 10), Point(14, 10), Point(14, 14), Point(10, 14)]
    return [
        Point(10, 10),
        Segment(Point(10, 10), Point(14, 14)),
        OrientedSegment(Point(10, 10), Point(14, 14)),
        Triangle(Point(10, 10), Point(14, 10), Point(12, 13)),
        Rectangle(Point(10, 10), Point(14, 14)),
        Convex(ring),
        MonotoneChain([Point(10, 10), Point(12, 13), Point(14, 10)]),
        Polyline([Point(10, 10), Point(12, 13), Point(14, 10)]),
        Polygon(ring),
        Polygon(ring).asPolygonWithHoles(),
        Polygon(ring).asPolygonSet(),
    ]


# The five unbounded convex shapes, all of them well clear of the origin too.
def _unbounded():
    return [
        Line(Point(0, 20), Point(1, 20)),
        OrientedLine(Point(0, 20), Point(1, 20)),
        Ray(Point(0, 20), Point(1, 20)),
        Halfplane(Point(0, 20), Point(1, 20)),
        Rectangle(Point(20, 20), Point(30, 30)).asHalfplaneIntersection(),
    ]


# --- the two grids ----------------------------------------------------------

@pytest.mark.parametrize("a", _bounded(), ids=lambda s: type(s).__name__)
@pytest.mark.parametrize("b", _bounded(), ids=lambda s: type(s).__name__)
def test_every_bounded_pair_has_both_methods(a, b):
    origin = Point(0, 0)
    assert a.closestSegments(b) is None  # they overlap: same block of the plane
    segments = origin.closestSegments(b)
    points = origin.closestPoints(b)
    assert len(segments) == 2 and len(points) == 2
    assert all(isinstance(s, Segment) for s in segments)
    assert all(isinstance(p, Point) for p in points)


@pytest.mark.parametrize("bounded", _bounded(), ids=lambda s: type(s).__name__)
@pytest.mark.parametrize("unbounded", _unbounded(), ids=lambda s: type(s).__name__)
def test_an_unbounded_operand_has_points_but_no_elements(bounded, unbounded):
    assert len(bounded.closestPoints(unbounded)) == 2
    assert len(unbounded.closestPoints(bounded)) == 2
    # It has no element to name: the point lies on no edge and at no vertex.
    with pytest.raises(TypeError):
        bounded.closestSegments(unbounded)
    assert not hasattr(type(unbounded), "closestSegments")


@pytest.mark.parametrize("unbounded", _unbounded(), ids=lambda s: type(s).__name__)
def test_two_unbounded_shapes_have_nothing_to_anchor_a_choice_to(unbounded):
    # Two parallel lines realize their distance along their whole length.
    with pytest.raises(TypeError):
        unbounded.closestPoints(Line(Point(0, -5), Point(1, -5)))


def test_disk_is_out_of_both_grids():
    # A disk's nearest point is generally irrational.
    assert not hasattr(Disk, "closestPoints")
    assert not hasattr(Disk, "closestSegments")
    with pytest.raises(TypeError):
        Point(0, 0).closestPoints(Disk(Point(9, 9), 1))


# --- what the answer says ---------------------------------------------------

def test_the_receivers_element_comes_first():
    a = Segment(Point(0, 0), Point(0, 4))
    b = Segment(Point(3, 0), Point(3, 4))
    assert a.closestSegments(b) == [a, b]
    assert b.closestSegments(a) == [b, a]
    assert a.closestPoints(b) == [Point(0, 0), Point(3, 0)]
    assert b.closestPoints(a) == [Point(3, 0), Point(0, 0)]


def test_a_shape_with_no_edge_names_a_degenerate_one():
    t = Triangle(Point(10, 0), Point(14, 0), Point(12, 3))
    first, second = Point(0, 0).closestSegments(t)
    assert first == Segment(Point(0, 0), Point(0, 0))
    assert first.isDegenerate()
    assert second == Segment(Point(10, 0), Point(14, 0))


def test_empty_exactly_when_the_distance_is_zero():
    t = Triangle(Point(0, 0), Point(10, 0), Point(0, 10))
    for other in (Point(1, 1), Point(0, 0), Segment(Point(-5, 1), Point(5, 1))):
        assert t.squaredDistance(other) == 0
        assert t.closestSegments(other) is None
        assert t.closestPoints(other) is None


def test_a_shape_nested_in_another_is_at_distance_zero():
    outer = Rectangle(Point(0, 0), Point(10, 10))
    inner = Rectangle(Point(3, 3), Point(4, 4))
    assert outer.contains(inner)
    assert outer.squaredDistance(inner) == 0
    assert outer.closestPoints(inner) is None


def test_a_hole_is_boundary_like_any_other():
    # A shape inside a hole is at *positive* distance from the region around
    # it, and the witness lands on the hole's edge.
    outer = Polygon([0, 0, 10, 0, 10, 10, 0, 10])
    hole = Polygon([3, 3, 7, 3, 7, 7, 3, 7])
    region = PolygonWithHoles(outer, [hole])
    centre = Point(5, 5)
    assert region.squaredDistance(centre) == 4
    assert region.closestPoints(centre) == [Point(5, 3), centre]
    on_region, on_centre = region.closestSegments(centre)
    assert on_region == Segment(Point(3, 3), Point(7, 3))
    assert on_centre == Segment(centre, centre)


def test_the_points_refine_the_elements_the_segments_name():
    a = Rectangle(Point(0, 0), Point(2, 2))
    b = Triangle(Point(7, 1), Point(9, 0), Point(9, 4))
    elements = a.closestSegments(b)
    points = a.closestPoints(b)
    for point, element in zip(points, elements):
        assert element.contains(point)
    assert points[0].squaredDistance(points[1]) == a.squaredDistance(b)


def test_the_witness_can_fall_strictly_inside_an_element():
    # The segment meets the ray at the segment's own midpoint, an end of
    # neither -- which is why the search is over projections, not just ends.
    segment = Segment(Point(-3, -1), Point(-3, 1))
    ray = Ray(Point(0, 0), Point(1, 0))
    assert segment.closestPoints(ray) == [Point(-3, 0), Point(0, 0)]
    assert ray.closestPoints(segment) == [Point(0, 0), Point(-3, 0)]


def test_the_points_are_exact_even_where_they_divide():
    # The foot of the perpendicular from (4, 0) onto y = x is (2, 2); onto the
    # same line from (3, 0) it is (3/2, 3/2), a point the segment's own
    # coordinate type cannot name and a Fraction does.
    diagonal = Segment(Point(0, 0), Point(4, 4))
    assert Point(4, 0).closestPoints(diagonal) == [Point(4, 0), Point(2, 2)]
    foot = Point(3, 0).closestPoints(diagonal)[1]
    assert foot == Point(Fraction(3, 2), Fraction(3, 2))
    assert foot.x() == Fraction(3, 2)


def test_the_elements_stay_in_the_shapes_own_vertices():
    # closestSegments never divides: both answers are edges already stored.
    diagonal = Segment(Point(0, 0), Point(4, 4))
    _, on_diagonal = Point(3, 0).closestSegments(diagonal)
    assert on_diagonal == diagonal


def test_a_polygon_set_answers_from_the_component_that_is_nearest():
    left = Polygon([0, 0, 2, 0, 2, 2, 0, 2])
    right = Polygon([20, 0, 22, 0, 22, 2, 20, 2])
    pair = PolygonSet([left.asPolygonWithHoles(), right.asPolygonWithHoles()])
    assert pair.closestPoints(Point(21, 5)) == [Point(21, 2), Point(21, 5)]
    assert pair.closestSegments(Point(21, 5))[0] == Segment(Point(22, 2), Point(20, 2))


def test_a_halfplane_intersection_answers_from_its_boundary():
    box = Rectangle(Point(20, 20), Point(30, 30)).asHalfplaneIntersection()
    assert box.closestPoints(Point(0, 20)) == [Point(20, 20), Point(0, 20)]
    wedge = HalfplaneIntersection(
        [Halfplane(Point(0, 0), Point(1, 0)), Halfplane(Point(0, 0), Point(0, -1))]
    )
    on_wedge, on_point = wedge.closestPoints(Point(-4, -3))
    assert on_wedge == Point(0, 0)
    assert on_point == Point(-4, -3)


def test_it_agrees_with_squared_distance_across_the_bounded_grid():
    origin = Point(0, 0)
    for other in _bounded():
        first, second = origin.closestPoints(other)
        assert first.squaredDistance(second) == origin.squaredDistance(other)
        assert other.contains(second)
